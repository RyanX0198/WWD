"""
文档 API 路由
提供文档的 CRUD 和版本管理接口
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.models import get_db
from app.services.document_db import DocumentService
from app.db.models import DocumentStatus, DocumentType

router = APIRouter(prefix="/documents", tags=["文档管理"])


# ========== 请求/响应模型 ==========

class DocumentCreate(BaseModel):
    """创建文档请求"""
    title: str
    content: str
    doc_type: str = DocumentType.OTHER
    tags: List[str] = []
    metadata: dict = {}


class DocumentUpdate(BaseModel):
    """更新文档请求"""
    title: Optional[str] = None
    content: Optional[str] = None
    status: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[dict] = None
    edit_reason: Optional[str] = None


class DocumentResponse(BaseModel):
    """文档响应"""
    id: str
    title: str
    content: str
    doc_type: str
    status: str
    author_id: str
    author_name: str
    version: int
    tags: List[str]
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


class VersionResponse(BaseModel):
    """版本响应"""
    id: str
    version_number: int
    title: str
    content: str
    change_type: str
    change_summary: str
    edited_by: str
    edited_by_name: str
    created_at: str


# ========== API 端点 ==========

@router.post("", response_model=DocumentResponse, summary="创建文档")
async def create_document(
    request: DocumentCreate,
    db: Session = Depends(get_db),
    # TODO: 从认证信息获取当前用户
    current_user_id: str = "test_user",
    current_user_name: str = "测试用户"
):
    """
    创建新文档
    
    自动创建初始版本记录
    """
    service = DocumentService(db)
    
    try:
        document = service.create_document(
            title=request.title,
            content=request.content,
            doc_type=request.doc_type,
            author_id=current_user_id,
            author_name=current_user_name,
            tags=request.tags,
            metadata=request.metadata
        )
        
        return document.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建文档失败: {str(e)}")


@router.get("", response_model=List[DocumentResponse], summary="获取文档列表")
async def get_documents(
    doc_type: Optional[str] = Query(None, description="文档类型筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量限制"),
    db: Session = Depends(get_db),
    current_user_id: str = "test_user"
):
    """
    获取当前用户的文档列表
    
    支持分页和筛选
    """
    service = DocumentService(db)
    
    documents = service.get_documents(
        author_id=current_user_id,
        doc_type=doc_type,
        status=status,
        skip=skip,
        limit=limit
    )
    
    return [doc.to_dict() for doc in documents]


@router.get("/{doc_id}", response_model=DocumentResponse, summary="获取文档详情")
async def get_document(
    doc_id: str,
    db: Session = Depends(get_db)
):
    """
    获取单个文档详情
    """
    service = DocumentService(db)
    document = service.get_document(doc_id)
    
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    return document.to_dict()


@router.put("/{doc_id}", response_model=DocumentResponse, summary="更新文档")
async def update_document(
    doc_id: str,
    request: DocumentUpdate,
    db: Session = Depends(get_db),
    current_user_id: str = "test_user",
    current_user_name: str = "测试用户"
):
    """
    更新文档
    
    自动创建版本记录
    """
    service = DocumentService(db)
    
    document = service.update_document(
        doc_id=doc_id,
        title=request.title,
        content=request.content,
        status=request.status,
        tags=request.tags,
        metadata=request.metadata,
        edited_by=current_user_id,
        edited_by_name=current_user_name,
        edit_reason=request.edit_reason
    )
    
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    return document.to_dict()


@router.delete("/{doc_id}", summary="删除文档")
async def delete_document(
    doc_id: str,
    hard_delete: bool = Query(False, description="是否硬删除"),
    db: Session = Depends(get_db),
    current_user_id: str = "test_user"
):
    """
    删除文档
    
    默认软删除，可通过 hard_delete=true 硬删除
    """
    service = DocumentService(db)
    
    success = service.delete_document(
        doc_id=doc_id,
        deleted_by=current_user_id,
        soft_delete=not hard_delete
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    return {"status": "success", "message": "文档已删除"}


@router.post("/{doc_id}/restore", response_model=DocumentResponse, summary="恢复文档")
async def restore_document(
    doc_id: str,
    db: Session = Depends(get_db)
):
    """
    恢复已删除的文档
    """
    service = DocumentService(db)
    
    document = service.restore_document(doc_id)
    
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在或未被删除")
    
    return document.to_dict()


# ========== 版本管理接口 ==========

@router.get("/{doc_id}/versions", response_model=List[VersionResponse], summary="获取版本历史")
async def get_versions(
    doc_id: str,
    db: Session = Depends(get_db)
):
    """
    获取文档的所有版本历史
    """
    service = DocumentService(db)
    
    # 先检查文档是否存在
    document = service.get_document(doc_id, include_deleted=True)
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    versions = service.get_versions(doc_id)
    return [v.to_dict() for v in versions]


@router.post("/{doc_id}/versions/{version_id}/restore", response_model=DocumentResponse, summary="恢复到指定版本")
async def restore_version(
    doc_id: str,
    version_id: str,
    db: Session = Depends(get_db),
    current_user_id: str = "test_user",
    current_user_name: str = "测试用户"
):
    """
    将文档恢复到指定版本
    
    会创建新的版本记录
    """
    service = DocumentService(db)
    
    document = service.restore_version(
        doc_id=doc_id,
        version_id=version_id,
        edited_by=current_user_id,
        edited_by_name=current_user_name
    )
    
    if not document:
        raise HTTPException(status_code=404, detail="文档或版本不存在")
    
    return document.to_dict()


@router.get("/{doc_id}/versions/{version_id}", summary="获取指定版本内容")
async def get_version(
    doc_id: str,
    version_id: str,
    db: Session = Depends(get_db)
):
    """
    获取特定版本的详细内容
    """
    service = DocumentService(db)
    
    version = service.get_version(version_id)
    
    if not version or version.document_id != doc_id:
        raise HTTPException(status_code=404, detail="版本不存在")
    
    return version.to_dict()