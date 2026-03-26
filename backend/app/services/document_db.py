"""
文档数据库操作服务
提供文档的 CRUD 和版本管理
"""
import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.db.models import Document, DocumentVersion, DocumentStatus, db


class DocumentService:
    """文档服务"""
    
    def __init__(self, db_session: Session = None):
        self.db = db_session
    
    # ========== 文档 CRUD ==========
    
    def create_document(
        self,
        title: str,
        content: str,
        doc_type: str,
        author_id: str,
        author_name: str,
        org_id: str = None,
        org_name: str = None,
        tags: list = None,
        metadata: dict = None
    ) -> Document:
        """
        创建新文档
        
        Args:
            title: 标题
            content: 内容
            doc_type: 文档类型
            author_id: 作者ID
            author_name: 作者名称
            org_id: 组织ID（可选）
            org_name: 组织名称（可选）
            tags: 标签列表（可选）
            metadata: 元数据（可选）
            
        Returns:
            创建的文档对象
        """
        doc_id = str(uuid.uuid4())
        
        # 创建文档
        document = Document(
            id=doc_id,
            title=title,
            content=content,
            doc_type=doc_type,
            status=DocumentStatus.DRAFT,
            author_id=author_id,
            author_name=author_name,
            org_id=org_id,
            org_name=org_name,
            word_count=str(len(content)),
            char_count=len(content),
            version=1,
            tags=tags or [],
            metadata=metadata or {},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        
        # 创建初始版本记录
        self._create_version(
            document_id=doc_id,
            version_number=1,
            title=title,
            content=content,
            change_type="create",
            change_summary="创建文档",
            edited_by=author_id,
            edited_by_name=author_name
        )
        
        return document
    
    def get_document(self, doc_id: str, include_deleted: bool = False) -> Optional[Document]:
        """
        获取文档
        
        Args:
            doc_id: 文档ID
            include_deleted: 是否包含已删除的文档
            
        Returns:
            文档对象或 None
        """
        query = self.db.query(Document).filter(Document.id == doc_id)
        
        if not include_deleted:
            query = query.filter(Document.is_deleted == False)
        
        return query.first()
    
    def get_documents(
        self,
        author_id: str = None,
        org_id: str = None,
        doc_type: str = None,
        status: str = None,
        skip: int = 0,
        limit: int = 100,
        include_deleted: bool = False
    ) -> List[Document]:
        """
        获取文档列表
        
        Args:
            author_id: 作者ID筛选（可选）
            org_id: 组织ID筛选（可选）
            doc_type: 文档类型筛选（可选）
            status: 状态筛选（可选）
            skip: 跳过数量（分页）
            limit: 返回数量限制
            include_deleted: 是否包含已删除的文档
            
        Returns:
            文档列表
        """
        query = self.db.query(Document)
        
        if author_id:
            query = query.filter(Document.author_id == author_id)
        
        if org_id:
            query = query.filter(Document.org_id == org_id)
        
        if doc_type:
            query = query.filter(Document.doc_type == doc_type)
        
        if status:
            query = query.filter(Document.status == status)
        
        if not include_deleted:
            query = query.filter(Document.is_deleted == False)
        
        return query.order_by(desc(Document.updated_at)).offset(skip).limit(limit).all()
    
    def update_document(
        self,
        doc_id: str,
        title: str = None,
        content: str = None,
        status: str = None,
        tags: list = None,
        metadata: dict = None,
        edited_by: str = None,
        edited_by_name: str = None,
        edit_reason: str = None
    ) -> Optional[Document]:
        """
        更新文档（自动创建版本记录）
        
        Args:
            doc_id: 文档ID
            title: 新标题（可选）
            content: 新内容（可选）
            status: 新状态（可选）
            tags: 新标签（可选）
            metadata: 新元数据（可选）
            edited_by: 编辑者ID
            edited_by_name: 编辑者名称
            edit_reason: 编辑原因
            
        Returns:
            更新后的文档对象或 None
        """
        document = self.get_document(doc_id)
        if not document:
            return None
        
        if document.is_deleted:
            raise ValueError("无法编辑已删除的文档")
        
        # 保存旧值用于版本记录
        old_title = document.title
        old_content = document.content
        
        # 更新字段
        if title is not None:
            document.title = title
        if content is not None:
            document.content = content
            document.word_count = str(len(content))
            document.char_count = len(content)
        if status is not None:
            document.status = status
            if status == DocumentStatus.PUBLISHED and not document.published_at:
                document.published_at = datetime.utcnow()
        if tags is not None:
            document.tags = tags
        if metadata is not None:
            document.metadata = metadata
        
        document.updated_at = datetime.utcnow()
        document.version += 1
        
        self.db.commit()
        self.db.refresh(document)
        
        # 创建版本记录
        if edited_by:
            change_summary = self._generate_change_summary(old_title, old_content, document.title, document.content)
            self._create_version(
                document_id=doc_id,
                version_number=document.version,
                title=document.title,
                content=document.content,
                change_type="edit",
                change_summary=change_summary,
                edited_by=edited_by,
                edited_by_name=edited_by_name or "未知用户",
                edit_reason=edit_reason
            )
        
        return document
    
    def delete_document(
        self,
        doc_id: str,
        deleted_by: str = None,
        soft_delete: bool = True
    ) -> bool:
        """
        删除文档
        
        Args:
            doc_id: 文档ID
            deleted_by: 删除者ID
            soft_delete: 是否软删除（True: 软删除，False: 硬删除）
            
        Returns:
            是否删除成功
        """
        document = self.get_document(doc_id, include_deleted=True)
        if not document:
            return False
        
        if soft_delete:
            # 软删除
            document.is_deleted = True
            document.deleted_at = datetime.utcnow()
            document.deleted_by = deleted_by
            document.status = DocumentStatus.DELETED
            self.db.commit()
        else:
            # 硬删除
            self.db.delete(document)
            self.db.commit()
        
        return True
    
    def restore_document(self, doc_id: str) -> Optional[Document]:
        """
        恢复已删除的文档
        
        Args:
            doc_id: 文档ID
            
        Returns:
            恢复后的文档对象或 None
        """
        document = self.get_document(doc_id, include_deleted=True)
        if not document or not document.is_deleted:
            return None
        
        document.is_deleted = False
        document.deleted_at = None
        document.deleted_by = None
        document.status = DocumentStatus.DRAFT
        document.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(document)
        
        return document
    
    # ========== 版本管理 ==========
    
    def get_versions(self, doc_id: str) -> List[DocumentVersion]:
        """
        获取文档的所有版本
        
        Args:
            doc_id: 文档ID
            
        Returns:
            版本列表
        """
        return self.db.query(DocumentVersion).filter(
            DocumentVersion.document_id == doc_id
        ).order_by(desc(DocumentVersion.version_number)).all()
    
    def get_version(self, version_id: str) -> Optional[DocumentVersion]:
        """
        获取特定版本
        
        Args:
            version_id: 版本ID
            
        Returns:
            版本对象或 None
        """
        return self.db.query(DocumentVersion).filter(DocumentVersion.id == version_id).first()
    
    def restore_version(
        self,
        doc_id: str,
        version_id: str,
        edited_by: str,
        edited_by_name: str
    ) -> Optional[Document]:
        """
        恢复到指定版本
        
        Args:
            doc_id: 文档ID
            version_id: 版本ID
            edited_by: 操作者ID
            edited_by_name: 操作者名称
            
        Returns:
            恢复后的文档对象或 None
        """
        document = self.get_document(doc_id)
        if not document:
            return None
        
        version = self.get_version(version_id)
        if not version or version.document_id != doc_id:
            return None
        
        # 更新文档内容
        document.title = version.title
        document.content = version.content
        document.word_count = str(len(version.content))
        document.char_count = len(version.content)
        document.version += 1
        document.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(document)
        
        # 创建恢复版本记录
        self._create_version(
            document_id=doc_id,
            version_number=document.version,
            title=document.title,
            content=document.content,
            change_type="restore",
            change_summary=f"恢复到版本 {version.version_number}",
            edited_by=edited_by,
            edited_by_name=edited_by_name
        )
        
        return document
    
    # ========== 私有方法 ==========
    
    def _create_version(
        self,
        document_id: str,
        version_number: int,
        title: str,
        content: str,
        change_type: str,
        change_summary: str,
        edited_by: str,
        edited_by_name: str,
        edit_reason: str = None
    ) -> DocumentVersion:
        """创建版本记录（私有方法）"""
        version = DocumentVersion(
            id=str(uuid.uuid4()),
            document_id=document_id,
            version_number=version_number,
            title=title,
            content=content,
            change_type=change_type,
            change_summary=change_summary,
            edited_by=edited_by,
            edited_by_name=edited_by_name,
            edit_reason=edit_reason,
            created_at=datetime.utcnow()
        )
        
        self.db.add(version)
        self.db.commit()
        self.db.refresh(version)
        
        return version
    
    def _generate_change_summary(
        self,
        old_title: str,
        old_content: str,
        new_title: str,
        new_content: str
    ) -> str:
        """生成变更摘要（私有方法）"""
        changes = []
        
        if old_title != new_title:
            changes.append("修改标题")
        
        if old_content != new_content:
            old_len = len(old_content)
            new_len = len(new_content)
            diff = new_len - old_len
            
            if diff > 0:
                changes.append(f"增加 {diff} 字符")
            elif diff < 0:
                changes.append(f"删除 {abs(diff)} 字符")
            else:
                changes.append("修改内容")
        
        return "，".join(changes) if changes else "编辑文档"


# 全局文档服务实例
document_service = DocumentService()