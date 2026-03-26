"""
模板中心 API 路由
"""
from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import List, Optional

from app.services.template import template_service

router = APIRouter()


class TemplateCreate(BaseModel):
    title: str
    content: str
    doc_type: str
    category: str = ""
    tags: List[str] = []
    description: str = ""


class TemplateMatchRequest(BaseModel):
    doc_type: str
    topic: str
    requirements: str = ""


@router.get("/")
async def list_templates(
    doc_type: Optional[str] = Query(None, description="文档类型筛选"),
    category: Optional[str] = Query(None, description="分类筛选"),
    tag: Optional[str] = Query(None, description="标签筛选")
):
    """获取模板列表"""
    templates = template_service.list_templates(
        doc_type=doc_type,
        category=category,
        tag=tag
    )
    return {"templates": templates, "count": len(templates)}


@router.get("/{template_id}")
async def get_template(
    template_id: str,
    doc_type: Optional[str] = Query(None, description="文档类型")
):
    """获取模板详情"""
    template = template_service.get_template(template_id, doc_type)
    if not template:
        return {"error": "模板不存在"}
    return {"template": template}


@router.post("/")
async def create_template(template: TemplateCreate):
    """创建模板"""
    result = template_service.add_template(
        title=template.title,
        content=template.content,
        doc_type=template.doc_type,
        category=template.category,
        tags=template.tags,
        description=template.description
    )
    return {"status": "success", "data": result}


@router.post("/match")
async def match_template(request: TemplateMatchRequest):
    """
    智能匹配模板
    
    根据文档类型和主题，返回最相关的模板
    """
    results = await template_service.match_template(
        doc_type=request.doc_type,
        topic=request.topic,
        requirements=request.requirements
    )
    return {"matches": results, "count": len(results)}


@router.post("/init-defaults")
async def init_default_templates():
    """初始化默认模板"""
    template_service.initialize_default_templates()
    return {"status": "success", "message": "默认模板已初始化"}


@router.delete("/{template_id}")
async def delete_template(
    template_id: str,
    doc_type: Optional[str] = Query(None)
):
    """删除模板"""
    success = template_service.delete_template(template_id, doc_type)
    if success:
        return {"status": "success", "message": "模板已删除"}
    return {"status": "error", "message": "删除失败"}