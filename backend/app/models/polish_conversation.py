"""
对话润色数据模型
支持多轮对话和润色模式
"""
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field


class PolishMode(str, Enum):
    """润色模式"""
    GENERAL = "general"         # 通用润色
    FORMAL = "formal"           # 正式化
    CONCISE = "concise"         # 精简
    EXPAND = "expand"           # 扩充
    POLICY = "policy"           # 政策化
    STYLE_LEARN = "style_learn" # 风格学习


class MessageRole(str, Enum):
    """消息角色"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ConversationStatus(str, Enum):
    """对话状态"""
    ACTIVE = "active"           # 进行中
    PAUSED = "paused"           # 暂停
    COMPLETED = "completed"     # 已完成
    ARCHIVED = "archived"       # 已归档


class PolishMessage(BaseModel):
    """润色消息"""
    id: str
    role: MessageRole
    content: str
    
    # 润色相关
    polish_mode: Optional[PolishMode] = None
    original_text: Optional[str] = None  # 修改前的文本
    polished_text: Optional[str] = None  # 修改后的文本
    
    # 元数据
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # 时间戳
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "polish_mode": self.polish_mode,
            "original_text": self.original_text,
            "polished_text": self.polished_text,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat()
        }


class PolishConversation(BaseModel):
    """润色对话会话"""
    id: str
    title: str
    
    # 关联信息
    document_id: Optional[str] = None  # 关联的文档ID
    user_id: str
    
    # 当前状态
    status: ConversationStatus = ConversationStatus.ACTIVE
    current_mode: PolishMode = PolishMode.GENERAL
    
    # 消息历史
    messages: List[PolishMessage] = Field(default_factory=list)
    
    # 上下文信息
    document_context: Optional[str] = None  # 当前文档内容快照
    selected_text: Optional[str] = None     # 选中的文本范围
    
    # 统计
    message_count: int = 0
    
    # 时间戳
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "document_id": self.document_id,
            "user_id": self.user_id,
            "status": self.status,
            "current_mode": self.current_mode,
            "messages": [m.to_dict() for m in self.messages],
            "document_context": self.document_context,
            "selected_text": self.selected_text,
            "message_count": self.message_count,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class ConversationCreate(BaseModel):
    """创建对话请求"""
    title: str
    document_id: Optional[str] = None
    document_context: Optional[str] = None
    initial_mode: PolishMode = PolishMode.GENERAL


class ConversationUpdate(BaseModel):
    """更新对话请求"""
    title: Optional[str] = None
    status: Optional[ConversationStatus] = None
    current_mode: Optional[PolishMode] = None


class MessageCreate(BaseModel):
    """发送消息请求"""
    content: str
    polish_mode: Optional[PolishMode] = None
    selected_text: Optional[str] = None  # 选中的文本（如果有）


class MessageResponse(BaseModel):
    """消息响应"""
    message: PolishMessage
    ai_response: PolishMessage
    updated_document: Optional[str] = None  # 润色后的文档内容（如果有）


class PolishModeInfo(BaseModel):
    """润色模式信息"""
    mode: PolishMode
    name: str
    description: str
    icon: str


# 润色模式定义
POLISH_MODES = [
    PolishModeInfo(
        mode=PolishMode.GENERAL,
        name="通用润色",
        description="优化语言表达，提升可读性",
        icon="✨"
    ),
    PolishModeInfo(
        mode=PolishMode.FORMAL,
        name="正式化",
        description="转换为正式的公文语言风格",
        icon="📋"
    ),
    PolishModeInfo(
        mode=PolishMode.CONCISE,
        name="精简",
        description="去除冗余，保留核心要点",
        icon="✂️"
    ),
    PolishModeInfo(
        mode=PolishMode.EXPAND,
        name="扩充",
        description="丰富内容，增加细节描述",
        icon="📝"
    ),
    PolishModeInfo(
        mode=PolishMode.POLICY,
        name="政策化",
        description="增强政策表述的规范性和准确性",
        icon="🏛️"
    ),
    PolishModeInfo(
        mode=PolishMode.STYLE_LEARN,
        name="风格学习",
        description="基于历史文档学习用户写作风格",
        icon="🎭"
    )
]