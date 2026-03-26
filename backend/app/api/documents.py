"""
文档管理 API 路由
"""
from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Optional

from app.services.export import export_service

router = APIRouter()


class DocumentCreate(BaseModel):
    title: str
    content: str
    doc_type: str


@router.post("/")
async def create_document(doc: DocumentCreate):
    """创建文档"""
    # TODO: 实现文档创建（保存到数据库或文件系统）
    return {"status": "success", "id": "xxx", "message": "文档创建功能开发中"}


@router.get("/{doc_id}")
async def get_document(doc_id: str):
    """获取文档"""
    # TODO: 实现文档查询
    return {"document": None, "message": "文档查询功能开发中"}


@router.put("/{doc_id}")
async def update_document(doc_id: str, doc: DocumentCreate):
    """更新文档"""
    # TODO: 实现文档更新
    return {"status": "success", "message": "文档更新功能开发中"}


@router.delete("/{doc_id}")
async def delete_document(doc_id: str):
    """删除文档"""
    # TODO: 实现文档删除
    return {"status": "success", "message": "文档删除功能开发中"}


@router.get("/{doc_id}/export")
async def export_document(
    doc_id: str,
    format: str = Query("markdown", description="导出格式: markdown, word, pdf"),
    title: Optional[str] = Query(None, description="文档标题"),
    content: Optional[str] = Query(None, description="文档内容（直接导出模式）")
):
    """
    导出文档
    
    支持格式：
    - markdown: Markdown 文件
    - word: Word 文档 (.docx)
    - pdf: PDF 文件（实际为 HTML，可打印保存）
    
    两种使用方式：
    1. 传入 doc_id，从数据库获取文档
    2. 直接传入 title 和 content，即时导出
    """
    # 如果传入了内容，直接导出
    if title and content:
        return export_service.get_export_response(title, content, format)
    
    # 否则从数据库获取（TODO: 实现数据库查询）
    # 目前临时返回示例
    return export_service.get_export_response(
        title or "未命名文档",
        content or "文档内容",
        format
    )


@router.post("/export")
async def export_document_post(doc: DocumentCreate, format: str = "markdown"):
    """
    导出文档（POST 方式，适合内容较长的场景）
    """
    return export_service.get_export_response(doc.title, doc.content, format)