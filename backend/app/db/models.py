"""
数据库模型定义
使用 SQLAlchemy ORM
"""
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import create_engine, Column, String, Text, DateTime, Boolean, ForeignKey, JSON, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

from app.core.config import settings

# 创建引擎（使用 SQLite 作为开发环境，生产环境使用 PostgreSQL）
# 后续可以通过配置切换
SQLALCHEMY_DATABASE_URL = "sqlite:///./gov_writing.db"
# PostgreSQL: "postgresql://user:password@localhost/gov_writing"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}  # SQLite 需要
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# ========== 枚举类型 ==========

class DocumentStatus(str, Enum):
    """文档状态"""
    DRAFT = "draft"           # 草稿
    REVIEWING = "reviewing"   # 审核中
    PUBLISHED = "published"   # 已发布
    ARCHIVED = "archived"     # 已归档
    DELETED = "deleted"       # 已删除（软删除）


class DocumentType(str, Enum):
    """文档类型"""
    SPEECH = "speech"               # 讲话稿
    SUMMARY = "summary"             # 工作总结
    EVENT_PLAN = "event_plan"       # 活动策划
    MEETING_MINUTES = "meeting_minutes"  # 会议纪要
    NOTICE = "notice"               # 通知公告
    REPORT = "report"               # 工作报告
    OTHER = "other"                 # 其他


# ========== 文档表 ==========

class Document(Base):
    """文档表"""
    __tablename__ = "documents"
    
    id = Column(String(36), primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    content = Column(Text, nullable=False, default="")
    
    # 文档类型和状态
    doc_type = Column(String(50), nullable=False, default=DocumentType.OTHER)
    status = Column(String(50), nullable=False, default=DocumentStatus.DRAFT)
    
    # 作者信息
    author_id = Column(String(36), nullable=False, index=True)
    author_name = Column(String(100), nullable=False)
    
    # 组织信息（支持多租户）
    org_id = Column(String(36), nullable=True, index=True)
    org_name = Column(String(100), nullable=True)
    
    # 统计信息
    word_count = Column(String(50), nullable=True)  # 字数统计
    char_count = Column(Integer, nullable=True)     # 字符数
    
    # 版本控制
    version = Column(Integer, nullable=False, default=1)
    latest_version_id = Column(String(36), nullable=True)  # 最新版本ID
    
    # 标签和元数据
    tags = Column(JSON, nullable=True, default=list)  # 标签列表
    metadata = Column(JSON, nullable=True, default=dict)  # 扩展元数据
    
    # 时间戳
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = Column(DateTime, nullable=True)
    
    # 软删除
    is_deleted = Column(Boolean, nullable=False, default=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(String(36), nullable=True)
    
    # 关系
    versions = relationship("DocumentVersion", back_populates="document", cascade="all, delete-orphan")
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "doc_type": self.doc_type,
            "status": self.status,
            "author_id": self.author_id,
            "author_name": self.author_name,
            "org_id": self.org_id,
            "org_name": self.org_name,
            "word_count": self.word_count,
            "char_count": self.char_count,
            "version": self.version,
            "tags": self.tags or [],
            "metadata": self.metadata or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "is_deleted": self.is_deleted
        }


# ========== 文档版本历史表 ==========

class DocumentVersion(Base):
    """文档版本历史表"""
    __tablename__ = "document_versions"
    
    id = Column(String(36), primary_key=True, index=True)
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False, index=True)
    
    # 版本号
    version_number = Column(Integer, nullable=False)
    
    # 版本内容快照
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    
    # 变更信息
    change_summary = Column(Text, nullable=True)  # 变更摘要
    change_type = Column(String(50), nullable=True)  # 变更类型：create, edit, polish, etc.
    
    # 编辑者信息
    edited_by = Column(String(36), nullable=False)
    edited_by_name = Column(String(100), nullable=False)
    
    # 编辑原因/备注
    edit_reason = Column(Text, nullable=True)
    
    # 时间戳
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # 关系
    document = relationship("Document", back_populates="versions")
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "document_id": self.document_id,
            "version_number": self.version_number,
            "title": self.title,
            "content": self.content,
            "change_summary": self.change_summary,
            "change_type": self.change_type,
            "edited_by": self.edited_by,
            "edited_by_name": self.edited_by_name,
            "edit_reason": self.edit_reason,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


# ========== 数据库会话管理 ==========

class Database:
    """数据库管理类"""
    
    def __init__(self):
        self.SessionLocal = SessionLocal
        self.engine = engine
        self.Base = Base
    
    def create_tables(self):
        """创建所有表"""
        self.Base.metadata.create_all(bind=self.engine)
    
    def get_db(self):
        """获取数据库会话（生成器，用于依赖注入）"""
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    def get_db_session(self):
        """获取数据库会话（直接返回）"""
        return self.SessionLocal()


# 全局数据库实例
db = Database()


# 依赖注入函数（用于 FastAPI）
def get_db():
    """FastAPI 依赖注入函数"""
    db_session = SessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()