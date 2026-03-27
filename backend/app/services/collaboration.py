"""
实时协作编辑服务 - WebSocket 管理
基于操作转换（OT）简化的协作方案
"""
import json
import asyncio
from typing import Dict, List, Set, Optional
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

from fastapi import WebSocket, WebSocketDisconnect


class OperationType(str, Enum):
    """操作类型"""
    INSERT = "insert"      # 插入文本
    DELETE = "delete"      # 删除文本
    RETAIN = "retain"      # 保留（位置移动）
    CURSOR = "cursor"      # 光标移动
    SELECTION = "selection"  # 选区变化


@dataclass
class Operation:
    """编辑操作"""
    type: OperationType
    position: int          # 操作位置
    text: Optional[str] = None      # 插入/删除的文本
    length: Optional[int] = None    # 删除长度
    user_id: Optional[str] = None   # 操作用户
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())
    revision: int = 0      # 版本号
    
    def to_dict(self) -> dict:
        return {
            "type": self.type.value,
            "position": self.position,
            "text": self.text,
            "length": self.length,
            "user_id": self.user_id,
            "timestamp": self.timestamp,
            "revision": self.revision
        }


@dataclass
class CursorInfo:
    """光标信息"""
    user_id: str
    user_name: str
    position: int
    selection_start: Optional[int] = None
    selection_end: Optional[int] = None
    color: str = "#1890ff"
    last_activity: float = field(default_factory=lambda: datetime.now().timestamp())
    
    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "user_name": self.user_name,
            "position": self.position,
            "selection_start": self.selection_start,
            "selection_end": self.selection_end,
            "color": self.color
        }


class CollaborativeDocument:
    """协作文档会话"""
    
    # 用户颜色池
    USER_COLORS = [
        "#1890ff",  # 蓝色
        "#52c41a",  # 绿色
        "#faad14",  # 黄色
        "#f5222d",  # 红色
        "#722ed1",  # 紫色
        "#13c2c2",  # 青色
        "#eb2f96",  # 粉色
        "#fa8c16",  # 橙色
    ]
    
    def __init__(self, document_id: str, content: str = ""):
        self.document_id = document_id
        self.content = content
        self.revision = 0                    # 当前版本号
        self.operations: List[Operation] = []  # 操作历史
        self.connections: Dict[str, WebSocket] = {}  # 用户连接
        self.cursors: Dict[str, CursorInfo] = {}     # 用户光标信息
        self.color_index = 0                 # 颜色分配索引
        self.last_activity = datetime.now()
        self._lock = asyncio.Lock()          # 异步锁
    
    def _get_user_color(self) -> str:
        """分配用户颜色"""
        color = self.USER_COLORS[self.color_index % len(self.USER_COLORS)]
        self.color_index += 1
        return color
    
    async def connect(self, websocket: WebSocket, user_id: str, user_name: str):
        """用户连接"""
        await websocket.accept()
        
        async with self._lock:
            self.connections[user_id] = websocket
            self.cursors[user_id] = CursorInfo(
                user_id=user_id,
                user_name=user_name,
                position=0,
                color=self._get_user_color()
            )
        
        # 发送当前文档状态和在线用户列表
        await self._send_initial_state(websocket)
        
        # 广播用户加入
        await self._broadcast_user_joined(user_id, user_name)
        
        self.last_activity = datetime.now()
    
    async def disconnect(self, user_id: str):
        """用户断开连接"""
        async with self._lock:
            if user_id in self.connections:
                del self.connections[user_id]
            if user_id in self.cursors:
                user_name = self.cursors[user_id].user_name
                del self.cursors[user_id]
        
        # 广播用户离开
        await self._broadcast_user_left(user_id)
        self.last_activity = datetime.now()
    
    async def _send_initial_state(self, websocket: WebSocket):
        """发送初始状态"""
        await websocket.send_json({
            "type": "init",
            "document_id": self.document_id,
            "content": self.content,
            "revision": self.revision,
            "users": [c.to_dict() for c in self.cursors.values()]
        })
    
    async def _broadcast_user_joined(self, user_id: str, user_name: str):
        """广播用户加入"""
        await self._broadcast({
            "type": "user_joined",
            "user": self.cursors[user_id].to_dict()
        }, exclude=user_id)
    
    async def _broadcast_user_left(self, user_id: str):
        """广播用户离开"""
        await self._broadcast({
            "type": "user_left",
            "user_id": user_id
        })
    
    async def apply_operation(self, operation: Operation, user_id: str) -> bool:
        """
        应用编辑操作
        简化版 OT：直接应用，不处理复杂冲突（适合低并发场景）
        """
        async with self._lock:
            # 更新版本号
            self.revision += 1
            operation.revision = self.revision
            operation.user_id = user_id
            
            # 应用操作到文档内容
            try:
                if operation.type == OperationType.INSERT:
                    pos = operation.position
                    text = operation.text or ""
                    self.content = self.content[:pos] + text + self.content[pos:]
                    
                    # 更新其他用户的光标位置
                    for cursor in self.cursors.values():
                        if cursor.user_id != user_id and cursor.position >= pos:
                            cursor.position += len(text)
                            if cursor.selection_start is not None and cursor.selection_start >= pos:
                                cursor.selection_start += len(text)
                            if cursor.selection_end is not None and cursor.selection_end >= pos:
                                cursor.selection_end += len(text)
                
                elif operation.type == OperationType.DELETE:
                    pos = operation.position
                    length = operation.length or 0
                    self.content = self.content[:pos] + self.content[pos + length:]
                    
                    # 更新其他用户的光标位置
                    for cursor in self.cursors.values():
                        if cursor.user_id != user_id:
                            if cursor.position > pos:
                                cursor.position = max(pos, cursor.position - length)
                            if cursor.selection_start is not None and cursor.selection_start > pos:
                                cursor.selection_start = max(pos, cursor.selection_start - length)
                            if cursor.selection_end is not None and cursor.selection_end > pos:
                                cursor.selection_end = max(pos, cursor.selection_end - length)
                
                # 保存操作历史
                self.operations.append(operation)
                
                # 限制历史长度
                if len(self.operations) > 1000:
                    self.operations = self.operations[-500:]
                
            except Exception as e:
                print(f"Apply operation error: {e}")
                return False
        
        # 广播操作给所有其他用户
        await self._broadcast({
            "type": "operation",
            "operation": operation.to_dict()
        }, exclude=user_id)
        
        self.last_activity = datetime.now()
        return True
    
    async def update_cursor(self, user_id: str, position: int, 
                           selection_start: Optional[int] = None,
                           selection_end: Optional[int] = None):
        """更新光标位置"""
        async with self._lock:
            if user_id in self.cursors:
                cursor = self.cursors[user_id]
                cursor.position = position
                cursor.selection_start = selection_start
                cursor.selection_end = selection_end
                cursor.last_activity = datetime.now()
        
        # 广播光标位置
        await self._broadcast({
            "type": "cursor",
            "user_id": user_id,
            "position": position,
            "selection_start": selection_start,
            "selection_end": selection_end
        }, exclude=user_id)
        
        self.last_activity = datetime.now()
    
    async def _broadcast(self, message: dict, exclude: Optional[str] = None):
        """广播消息给所有连接的用户"""
        disconnected = []
        
        for user_id, websocket in self.connections.items():
            if user_id == exclude:
                continue
            
            try:
                await websocket.send_json(message)
            except Exception as e:
                print(f"Broadcast error to {user_id}: {e}")
                disconnected.append(user_id)
        
        # 清理断开的连接
        for user_id in disconnected:
            await self.disconnect(user_id)
    
    def get_stats(self) -> dict:
        """获取文档统计信息"""
        return {
            "document_id": self.document_id,
            "content_length": len(self.content),
            "revision": self.revision,
            "online_users": len(self.connections),
            "operation_count": len(self.operations),
            "last_activity": self.last_activity.isoformat()
        }


class CollaborationManager:
    """协作会话管理器"""
    
    def __init__(self):
        self.documents: Dict[str, CollaborativeDocument] = {}
        self._cleanup_task: Optional[asyncio.Task] = None
    
    def get_or_create_document(self, document_id: str, content: str = "") -> CollaborativeDocument:
        """获取或创建协作文档"""
        if document_id not in self.documents:
            self.documents[document_id] = CollaborativeDocument(document_id, content)
        return self.documents[document_id]
    
    def get_document(self, document_id: str) -> Optional[CollaborativeDocument]:
        """获取协作文档"""
        return self.documents.get(document_id)
    
    def remove_document(self, document_id: str):
        """移除协作文档"""
        if document_id in self.documents:
            del self.documents[document_id]
    
    def list_documents(self) -> List[dict]:
        """列出所有协作文档"""
        return [doc.get_stats() for doc in self.documents.values()]
    
    async def start_cleanup_task(self):
        """启动清理任务（清理长时间不活动的文档）"""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def _cleanup_loop(self):
        """定期清理不活动的文档"""
        while True:
            await asyncio.sleep(300)  # 每5分钟检查一次
            
            now = datetime.now()
            to_remove = []
            
            for doc_id, doc in self.documents.items():
                # 清理30分钟无活动且无人连接的文档
                inactive_time = (now - doc.last_activity).total_seconds()
                if inactive_time > 1800 and len(doc.connections) == 0:
                    to_remove.append(doc_id)
            
            for doc_id in to_remove:
                print(f"Removing inactive collaborative document: {doc_id}")
                self.remove_document(doc_id)


# 全局协作管理器
collaboration_manager = CollaborationManager()
