"""
模板服务 - 智能模板匹配
"""
import os
from typing import List, Optional, Dict
from pathlib import Path
from difflib import SequenceMatcher

import yaml

from app.core.config import settings
from app.services.vector_search import vector_search


class TemplateService:
    """模板服务"""
    
    def __init__(self):
        self.base_path = Path(settings.KNOWLEDGE_BASE_PATH) / "templates"
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def _similarity(self, a: str, b: str) -> float:
        """计算字符串相似度"""
        return SequenceMatcher(None, a, b).ratio()
    
    def add_template(
        self,
        title: str,
        content: str,
        doc_type: str,
        category: str = "",
        tags: List[str] = None,
        description: str = ""
    ) -> Dict:
        """
        添加模板
        
        Args:
            title: 模板标题
            content: 模板内容
            doc_type: 文档类型（讲话稿/工作总结等）
            category: 分类
            tags: 标签
            description: 描述
            
        Returns:
            模板信息
        """
        template_id = f"template_{doc_type}_{title.replace(' ', '_')}"
        
        # 创建模板目录
        doc_type_dir = self.base_path / doc_type
        doc_type_dir.mkdir(exist_ok=True)
        
        file_path = doc_type_dir / f"{template_id}.md"
        
        # 构建 frontmatter
        frontmatter = {
            "id": template_id,
            "title": title,
            "doc_type": doc_type,
            "category": category,
            "tags": tags or [],
            "description": description,
            "created_at": str(Path().stat().st_mtime if Path().exists() else "")
        }
        
        # 保存模板
        md_content = f"""---
{yaml.dump(frontmatter, allow_unicode=True)}
---

# {title}

{description}

## 模板内容

{content}

## 使用说明

1. 替换方括号 `[]` 中的内容为实际信息
2. 根据实际情况调整段落结构
3. 注意检查人名、职务、日期等信息
"""
        
        file_path.write_text(md_content, encoding="utf-8")
        
        return {
            "id": template_id,
            "title": title,
            "doc_type": doc_type,
            "path": str(file_path)
        }
    
    def get_template(self, template_id: str, doc_type: str = None) -> Optional[Dict]:
        """获取模板"""
        if doc_type:
            file_path = self.base_path / doc_type / f"{template_id}.md"
        else:
            # 搜索所有类型
            file_path = None
            for doc_type_dir in self.base_path.iterdir():
                if doc_type_dir.is_dir():
                    candidate = doc_type_dir / f"{template_id}.md"
                    if candidate.exists():
                        file_path = candidate
                        break
        
        if not file_path or not file_path.exists():
            return None
        
        content = file_path.read_text(encoding="utf-8")
        
        # 解析 frontmatter
        metadata = {}
        body = content
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                try:
                    metadata = yaml.safe_load(parts[1])
                    body = parts[2].strip()
                except:
                    pass
        
        return {
            "id": template_id,
            "metadata": metadata,
            "content": body,
            "path": str(file_path)
        }
    
    def list_templates(
        self,
        doc_type: str = None,
        category: str = None,
        tag: str = None
    ) -> List[Dict]:
        """
        列出模板
        
        Args:
            doc_type: 文档类型筛选
            category: 分类筛选
            tag: 标签筛选
            
        Returns:
            模板列表
        """
        results = []
        
        if doc_type:
            type_dirs = [self.base_path / doc_type]
        else:
            type_dirs = [d for d in self.base_path.iterdir() if d.is_dir()]
        
        for type_dir in type_dirs:
            for md_file in type_dir.glob("*.md"):
                try:
                    content = md_file.read_text(encoding="utf-8")
                    metadata = {}
                    
                    # 解析 frontmatter
                    if content.startswith("---"):
                        parts = content.split("---", 2)
                        if len(parts) >= 3:
                            try:
                                metadata = yaml.safe_load(parts[1])
                            except:
                                pass
                    
                    # 应用筛选
                    if category and metadata.get("category") != category:
                        continue
                    if tag and tag not in metadata.get("tags", []):
                        continue
                    
                    results.append({
                        "id": metadata.get("id", md_file.stem),
                        "title": metadata.get("title", md_file.stem),
                        "doc_type": metadata.get("doc_type", type_dir.name),
                        "category": metadata.get("category", ""),
                        "tags": metadata.get("tags", []),
                        "description": metadata.get("description", ""),
                        "path": str(md_file)
                    })
                except Exception as e:
                    print(f"Error reading {md_file}: {e}")
        
        return results
    
    async def match_template(
        self,
        doc_type: str,
        topic: str,
        requirements: str = ""
    ) -> List[Dict]:
        """
        智能匹配模板
        
        结合向量搜索和关键词匹配，返回最相关的模板
        
        Args:
            doc_type: 文档类型
            topic: 主题
            requirements: 具体要求
            
        Returns:
            匹配结果列表（按相关度排序）
        """
        query = f"{topic} {requirements}"
        results = []
        
        # 1. 向量搜索
        if vector_search.qdrant:
            vector_results = await vector_search.search_templates(
                query,
                doc_type=doc_type,
                limit=5
            )
            for r in vector_results:
                template_id = r.get("id", "")
                template = self.get_template(template_id)
                if template:
                    results.append({
                        "template": template,
                        "score": r.get("score", 0),
                        "match_type": "semantic"
                    })
        
        # 2. 关键词匹配（补充）
        all_templates = self.list_templates(doc_type=doc_type)
        for t in all_templates:
            # 计算标题相似度
            title_sim = self._similarity(topic.lower(), t.get("title", "").lower())
            
            # 如果相似度较高且未在向量结果中
            if title_sim > 0.3:
                existing_ids = [r["template"]["id"] for r in results]
                if t["id"] not in existing_ids:
                    results.append({
                        "template": t,
                        "score": title_sim,
                        "match_type": "keyword"
                    })
        
        # 按分数排序
        results.sort(key=lambda x: x["score"], reverse=True)
        
        return results[:5]  # 返回前5个
    
    def delete_template(self, template_id: str, doc_type: str = None) -> bool:
        """删除模板"""
        template = self.get_template(template_id, doc_type)
        if not template:
            return False
        
        Path(template["path"]).unlink(missing_ok=True)
        
        # 删除向量
        vector_search.delete_document(
            vector_search.COLLECTION_TEMPLATES,
            template_id
        )
        
        return True
    
    def initialize_default_templates(self):
        """初始化默认模板"""
        
        # 讲话稿模板
        speech_template = """尊敬的[领导称谓]、各位[参会人员]：

大家好！

[开场白，简要说明会议背景和目的]

一、[第一部分标题]

[第一部分内容，阐述背景、现状等]

二、[第二部分标题]

[第二部分内容，分析问题、机遇等]

三、[第三部分标题]

[第三部分内容，提出工作要求、部署任务等]

[结语，号召性语言]

谢谢大家！"""
        
        self.add_template(
            title="通用领导讲话稿",
            content=speech_template,
            doc_type="讲话稿",
            category="通用",
            tags=["通用", "会议", "正式"],
            description="适用于各类会议的领导讲话"
        )
        
        # 工作总结模板
        summary_template = """[单位/部门][年度]工作总结

一、主要工作完成情况

（一）[工作一]
[具体描述]

（二）[工作二]
[具体描述]

（三）[工作三]
[具体描述]

二、主要做法和成效

[总结工作方法和取得的成效]

三、存在的问题和不足

[客观分析存在的问题]

四、下一步工作计划

[提出下一步工作安排]

[单位名称]
[日期]"""
        
        self.add_template(
            title="年度工作总结",
            content=summary_template,
            doc_type="工作总结",
            category="年度",
            tags=["年度", "总结", "汇报"],
            description="标准的年度工作总结格式"
        )
        
        # 活动策划模板
        event_template = """[活动名称]策划方案

一、活动背景

[活动举办的背景和意义]

二、活动目的

[预期达到的目标]

三、活动时间

[具体时间安排]

四、活动地点

[地点信息]

五、参加人员

[参会人员范围]

六、活动流程

[详细的活动流程安排]

七、工作分工

[各部门/人员职责]

八、经费预算

[预算明细]

九、注意事项

[其他需要说明的事项]

[单位名称]
[日期]"""
        
        self.add_template(
            title="活动策划方案",
            content=event_template,
            doc_type="活动策划",
            category="通用",
            tags=["活动", "策划", "方案"],
            description="标准的活动策划方案格式"
        )
        
        # 会议纪要模板
        meeting_template = """[会议名称]会议纪要

时间：[日期时间]
地点：[地点]
主持：[主持人]
出席：[出席人员]
列席：[列席人员]
记录：[记录人]

一、会议议题

[会议主要议题]

二、会议内容

[会议讨论的主要内容]

三、议定事项

（一）[事项一]
[具体内容]

（二）[事项二]
[具体内容]

四、工作要求

[后续工作要求]

[单位名称]
[日期]"""
        
        self.add_template(
            title="会议纪要",
            content=meeting_template,
            doc_type="会议纪要",
            category="通用",
            tags=["会议", "纪要", "记录"],
            description="标准的会议纪要格式"
        )


# 全局模板服务实例
template_service = TemplateService()