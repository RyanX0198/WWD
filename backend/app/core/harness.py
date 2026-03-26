"""
Harness 核心引擎 - 公文写作 Agent
基于 LangGraph + Deep Agents
"""
from typing import TypedDict, List, Optional, Annotated
import operator
from pathlib import Path

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langgraph.graph import StateGraph, END

from app.core.config import settings
from app.core.llm_router import llm_router
from app.services.knowledge import knowledge_service


class WritingState(TypedDict):
    """写作任务状态"""
    messages: Annotated[List[BaseMessage], operator.add]
    document_type: str  # 公文类型：讲话稿、工作总结等
    topic: str  # 主题
    outline: Optional[List[dict]]  # 大纲
    draft: Optional[str]  # 初稿
    references: List[str]  # 引用资料
    stage: str  # 当前阶段：requirement/outline/draft/review


class WritingHarness:
    """公文写作 Harness"""
    
    def __init__(self):
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """构建写作流程图"""
        workflow = StateGraph(WritingState)
        
        # 定义节点
        workflow.add_node("parse_requirement", self._parse_requirement)
        workflow.add_node("search_knowledge", self._search_knowledge)
        workflow.add_node("generate_outline", self._generate_outline)
        workflow.add_node("generate_draft", self._generate_draft)
        workflow.add_node("self_check", self._self_check)
        
        # 定义边
        workflow.set_entry_point("parse_requirement")
        workflow.add_edge("parse_requirement", "search_knowledge")
        workflow.add_edge("search_knowledge", "generate_outline")
        workflow.add_edge("generate_outline", "generate_draft")
        workflow.add_edge("generate_draft", "self_check")
        workflow.add_edge("self_check", END)
        
        return workflow.compile()
    
    async def _parse_requirement(self, state: WritingState):
        """解析用户需求"""
        messages = state["messages"]
        last_message = messages[-1].content if messages else ""
        
        # 使用 LLM 解析需求
        model = llm_router.get_model(task_type="search")
        
        prompt = f"""分析用户的写作需求，提取以下信息：
1. 公文类型（讲话稿/工作总结/活动策划/会议纪要）
2. 主题/标题
3. 场合/受众
4. 关键要点

用户输入：{last_message}

请以 JSON 格式返回：
{{
    "document_type": "公文类型",
    "topic": "主题",
    "occasion": "场合",
    "key_points": ["要点1", "要点2"]
}}"""
        
        try:
            response = await model.ainvoke([HumanMessage(content=prompt)])
            parsed = json.loads(response.content)
            
            return {
                "stage": "knowledge",
                "document_type": parsed.get("document_type", state.get("document_type", "讲话稿")),
                "topic": parsed.get("topic", state.get("topic", ""))
            }
        except Exception as e:
            print(f"Parse requirement error: {e}")
            return {"stage": "knowledge"}
    
    async def _search_knowledge(self, state: WritingState):
        """检索知识库"""
        topic = state.get("topic", "")
        doc_type = state.get("document_type", "")
        
        references = []
        
        # 1. 从主题中提取可能的人名并查询
        people = knowledge_service.list_all_people()
        involved_people = []
        for person in people:
            if person in topic:
                person_data = knowledge_service.get_person(person)
                if person_data:
                    involved_people.append(person_data)
                    references.append(f"人物档案: {person}")
        
        # 2. 查询相关政策（简化版，后续可用向量检索）
        # TODO: 实现政策文件检索
        
        # 3. 查询模板
        # TODO: 实现模板匹配
        
        return {
            "references": references,
            "involved_people": involved_people,
            "stage": "outline"
        }
    
    async def _generate_outline(self, state: WritingState):
        """生成大纲"""
        doc_type = state.get("document_type", "讲话稿")
        topic = state.get("topic", "")
        involved_people = state.get("involved_people", [])
        
        # 构建提示词
        people_info = ""
        if involved_people:
            people_info = "\n\n涉及人物：\n"
            for p in involved_people:
                people_info += f"- {p.get('name')} ({p.get('current_position')})\n"
        
        model = llm_router.get_model(task_type="outline")
        
        prompt = f"""请为以下公文生成大纲：

公文类型: {doc_type}
主题: {topic}{people_info}

要求：
1. 符合政府公文规范
2. 结构清晰，层次分明
3. 包含开场白、主体内容、结尾

请以 JSON 格式返回大纲：
{{
    "sections": [
        {{"title": "章节标题", "content": "主要内容描述"}}
    ]
}}"""
        
        try:
            response = await model.ainvoke([HumanMessage(content=prompt)])
            content = response.content
            
            # 提取 JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            outline_data = json.loads(content.strip())
            outline = outline_data.get("sections", [])
            
            return {
                "outline": outline,
                "stage": "draft"
            }
        except Exception as e:
            print(f"Generate outline error: {e}")
            # 返回默认大纲
            default_outline = [
                {"title": "一、开场", "content": "引入主题"},
                {"title": "二、主体", "content": "详细阐述"},
                {"title": "三、总结", "content": "概括要点"}
            ]
            return {"outline": default_outline, "stage": "draft"}
    
    async def _generate_draft(self, state: WritingState):
        """生成初稿"""
        doc_type = state.get("document_type", "讲话稿")
        topic = state.get("topic", "")
        outline = state.get("outline", [])
        involved_people = state.get("involved_people", [])
        
        # 构建大纲文本
        outline_text = "\n".join([
            f"{i+1}. {section.get('title', '')}\n   {section.get('content', '')}"
            for i, section in enumerate(outline)
        ])
        
        # 构建称谓提示
        addressing_hint = ""
        if involved_people:
            addressing_hint = "\n\n称谓规范（严格遵循）：\n"
            for p in involved_people:
                rules = p.get('addressing_rules', {})
                formal = rules.get('正式场合', p.get('name'))
                addressing_hint += f"- {p.get('name')} 在正式场合称：{formal}\n"
        
        model = llm_router.get_model(task_type="writing")
        
        # 读取系统提示词
        try:
            agent_md = Path(settings.KNOWLEDGE_BASE_PATH) / "AGENTS.md"
            system_prompt = agent_md.read_text(encoding="utf-8")
        except:
            system_prompt = "你是一位专业的政府公文写作助手。"
        
        prompt = f"""请根据以下大纲生成完整的{doc_type}：

主题: {topic}

大纲:
{outline_text}{addressing_hint}

要求：
1. 严格遵循政府公文格式规范
2. 语言庄重、准确、简洁
3. 正确使用人物称谓
4. 控制字数在1500-2500字
5. 不要添加任何解释性文字，直接输出公文正文

请直接输出公文内容："""
        
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=prompt)
            ]
            response = await model.ainvoke(messages)
            
            return {
                "draft": response.content,
                "stage": "review"
            }
        except Exception as e:
            print(f"Generate draft error: {e}")
            return {"draft": "生成失败，请重试", "stage": "review"}
    
    async def _self_check(self, state: WritingState):
        """自检"""
        draft = state.get("draft", "")
        involved_people = state.get("involved_people", [])
        
        # 简单的自检规则
        issues = []
        
        # 1. 检查称谓
        for p in involved_people:
            name = p.get('name', '')
            rules = p.get('addressing_rules', {})
            avoid = rules.get('避免使用', '')
            
            if avoid and avoid in draft:
                issues.append(f"称谓错误：应使用'{rules.get('正式场合', name)}'而非'{avoid}'")
        
        # 2. 检查口语化词汇
        informal_words = ["高大上", "接地气", "搞", "很", "非常"]
        for word in informal_words:
            if word in draft:
                issues.append(f"口语化表达：避免使用'{word}'")
        
        # 3. 检查字数
        char_count = len(draft.replace(" ", "").replace("\n", ""))
        if char_count < 800:
            issues.append(f"字数偏少：当前约{char_count}字，建议1500字以上")
        elif char_count > 3500:
            issues.append(f"字数偏多：当前约{char_count}字，建议精简")
        
        # 添加检查报告
        if issues:
            draft += f"\n\n---\n【自检报告】\n" + "\n".join([f"• {i}" for i in issues])
        
        return {
            "draft": draft,
            "check_issues": issues,
            "stage": "complete"
        }
    
    async def write(self, document_type: str, topic: str) -> dict:
        """
        执行写作任务
        
        Args:
            document_type: 公文类型
            topic: 写作主题
            
        Returns:
            写作结果
        """
        initial_state = WritingState(
            messages=[HumanMessage(content=f"请写一篇{document_type}，主题是：{topic}")],
            document_type=document_type,
            topic=topic,
            outline=None,
            draft=None,
            references=[],
            stage="requirement"
        )
        
        result = await self.workflow.ainvoke(initial_state)
        return result


# 全局 Harness 实例
writing_harness = WritingHarness()