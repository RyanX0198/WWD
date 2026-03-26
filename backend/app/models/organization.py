"""
机构数据模型
管理行政机构层级关系
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class Organization(BaseModel):
    """机构模型"""
    id: str
    name: str  # 机构全称
    short_name: str  # 简称
    code: str  # 机构代码（统一社会信用代码或内部编码）
    
    # 层级关系
    parent_id: Optional[str] = None  # 上级机构ID
    level: int = 1  # 层级：1-省级, 2-市级, 3-区级, 4-街道, 等等
    path: str = ""  # 层级路径，如："/1/2/3/"
    
    # 机构类型
    org_type: str  # 政府/党委/人大/政协/法院/检察院/群团/事业单位/国企
    
    # 基本信息
    address: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    
    # 职责描述
    responsibilities: Optional[str] = None
    
    # 状态
    is_active: bool = True  # 是否有效
    established_at: Optional[datetime] = None  # 成立时间
    
    # 元数据
    metadata: dict = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    
    # 时间戳
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        from_attributes = True


class OrganizationCreate(BaseModel):
    """创建机构请求"""
    name: str
    short_name: str
    code: str
    parent_id: Optional[str] = None
    org_type: str
    address: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    responsibilities: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class OrganizationUpdate(BaseModel):
    """更新机构请求"""
    name: Optional[str] = None
    short_name: Optional[str] = None
    code: Optional[str] = None
    parent_id: Optional[str] = None
    org_type: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    responsibilities: Optional[str] = None
    is_active: Optional[bool] = None
    tags: Optional[List[str]] = None


class OrganizationTreeNode(BaseModel):
    """机构树节点"""
    id: str
    name: str
    short_name: str
    level: int
    org_type: str
    is_active: bool
    children: List['OrganizationTreeNode'] = Field(default_factory=list)
    
    class Config:
        from_attributes = True


# 递归模型需要重新构建
OrganizationTreeNode.model_rebuild()