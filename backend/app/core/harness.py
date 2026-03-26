"""
Harness 核心引擎 - 公文写作 Agent
基于 LangGraph + Deep Agents
"""
from typing import TypedDict, List, Optional, Annotated
import operator

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END

from app.core.config import settings


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
        # TODO: 实现需求解析逻辑
        return {"stage": "outline"}
    
    async def _search_knowledge(self, state: WritingState):
        """检索知识库"""
        # TODO: 实现知识库检索
        return {"references": []}
    
    async def _generate_outline(self, state: WritingState):
        """生成大纲"""
        # TODO: 实现大纲生成
        return {"outline": []}
    
    async def _generate_draft(self, state: WritingState):
        """生成初稿"""
        # TODO: 实现初稿生成
        return {"draft": ""}
    
    async def _self_check(self, state: WritingState):
        """自检"""
        # TODO: 实现自检逻辑
        return {}
    
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