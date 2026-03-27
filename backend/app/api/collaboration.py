"""
实时协作编辑 WebSocket 路由
"""
import json
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query

from app.services.collaboration import (
    collaboration_manager, 
    CollaborativeDocument,
    Operation,
    OperationType
)
from app.services.document_db import document_service
from app.core.security import get_current_active_user

router = APIRouter(tags=["实时协作"])


# WebSocket 连接管理器
class ConnectionManager:
    """WebSocket 连接管理"""
    
    async def connect(
        self,
        websocket: WebSocket,
        document_id: str,
        user_id: str,
        user_name: str
    ):
        """建立 WebSocket 连接"""
        # 获取文档内容（如果文档存在）
        content = ""
        try:
            doc = document_service.get_document(document_id)
            if doc:
                content = doc.get("content", "")
        except Exception as e:
            print(f"Failed to load document {document_id}: {e}")
        
        # 获取或创建协作文档
        collab_doc = collaboration_manager.get_or_create_document(document_id, content)
        
        # 连接用户
        await collab_doc.connect(websocket, user_id, user_name)
        
        return collab_doc
    
    async def handle_messages(
        self,
        websocket: WebSocket,
        collab_doc: CollaborativeDocument,
        user_id: str
    ):
        """处理 WebSocket 消息"""
        try:
            while True:
                # 接收消息
                data = await websocket.receive_text()
                message = json.loads(data)
                
                msg_type = message.get("type")
                
                if msg_type == "operation":
                    # 处理编辑操作
                    await self._handle_operation(message, collab_doc, user_id)
                
                elif msg_type == "cursor":
                    # 处理光标更新
                    await self._handle_cursor(message, collab_doc, user_id)
                
                elif msg_type == "selection":
                    # 处理选区更新
                    await self._handle_selection(message, collab_doc, user_id)
                
                elif msg_type == "sync_request":
                    # 请求同步文档状态
                    await self._handle_sync_request(websocket, collab_doc)
                
                elif msg_type == "ping":
                    # 心跳响应
                    await websocket.send_json({"type": "pong"})
        
        except WebSocketDisconnect:
            # 用户断开连接
            await collab_doc.disconnect(user_id)
        except Exception as e:
            print(f"WebSocket error for user {user_id}: {e}")
            await collab_doc.disconnect(user_id)
    
    async def _handle_operation(
        self,
        message: dict,
        collab_doc: CollaborativeDocument,
        user_id: str
    ):
        """处理编辑操作"""
        op_data = message.get("operation", {})
        
        operation = Operation(
            type=OperationType(op_data.get("type", "retain")),
            position=op_data.get("position", 0),
            text=op_data.get("text"),
            length=op_data.get("length"),
            user_id=user_id
        )
        
        # 应用操作
        success = await collab_doc.apply_operation(operation, user_id)
        
        if not success:
            # 操作失败，请求客户端重同步
            if user_id in collab_doc.connections:
                await collab_doc.connections[user_id].send_json({
                    "type": "error",
                    "message": "Operation failed, please resync"
                })
    
    async def _handle_cursor(
        self,
        message: dict,
        collab_doc: CollaborativeDocument,
        user_id: str
    ):
        """处理光标移动"""
        position = message.get("position", 0)
        await collab_doc.update_cursor(user_id, position)
    
    async def _handle_selection(
        self,
        message: dict,
        collab_doc: CollaborativeDocument,
        user_id: str
    ):
        """处理选区变化"""
        position = message.get("position", 0)
        selection_start = message.get("selection_start")
        selection_end = message.get("selection_end")
        await collab_doc.update_cursor(user_id, position, selection_start, selection_end)
    
    async def _handle_sync_request(
        self,
        websocket: WebSocket,
        collab_doc: CollaborativeDocument
    ):
        """处理同步请求"""
        await websocket.send_json({
            "type": "sync",
            "content": collab_doc.content,
            "revision": collab_doc.revision
        })


# 全局连接管理器
connection_manager = ConnectionManager()


@router.websocket("/ws/collaborate/{document_id}")
async def collaborate_websocket(
    websocket: WebSocket,
    document_id: str,
    user_id: str = Query(..., description="用户ID"),
    user_name: str = Query(..., description="用户名称")
):
    """
    实时协作编辑 WebSocket 端点
    
    连接参数：
    - document_id: 文档ID（路径参数）
    - user_id: 用户ID（查询参数）
    - user_name: 用户名称（查询参数）
    
    WebSocket 消息协议：
    
    **客户端 -> 服务器：**
    
    1. 编辑操作
    ```json
    {
        "type": "operation",
        "operation": {
            "type": "insert|delete",
            "position": 10,
            "text": "插入的文本",  // insert 时必填
            "length": 5           // delete 时必填
        }
    }
    ```
    
    2. 光标移动
    ```json
    {
        "type": "cursor",
        "position": 25
    }
    ```
    
    3. 选区变化
    ```json
    {
        "type": "selection",
        "position": 30,
        "selection_start": 20,
        "selection_end": 30
    }
    ```
    
    4. 心跳
    ```json
    {
        "type": "ping"
    }
    ```
    
    **服务器 -> 客户端：**
    
    1. 初始状态
    ```json
    {
        "type": "init",
        "document_id": "doc_id",
        "content": "文档内容",
        "revision": 5,
        "users": [{"user_id": "...", "user_name": "...", "position": 0, "color": "#1890ff"}]
    }
    ```
    
    2. 操作广播
    ```json
    {
        "type": "operation",
        "operation": {
            "type": "insert",
            "position": 10,
            "text": "文本",
            "user_id": "...",
            "revision": 6
        }
    }
    ```
    
    3. 光标广播
    ```json
    {
        "type": "cursor",
        "user_id": "...",
        "position": 25
    }
    ```
    
    4. 用户加入/离开
    ```json
    {
        "type": "user_joined|user_left",
        "user": {"user_id": "...", "user_name": "...", ...},
        "user_id": "..."
    }
    ```
    """
    # 建立连接
    collab_doc = await connection_manager.connect(
        websocket, document_id, user_id, user_name
    )
    
    # 处理消息
    await connection_manager.handle_messages(websocket, collab_doc, user_id)


# ========== REST API 用于协作管理 ==========

@router.get("/collaboration/documents")
async def list_collaborative_documents():
    """获取所有正在协作的文档列表"""
    return {
        "status": "success",
        "documents": collaboration_manager.list_documents()
    }


@router.get("/collaboration/documents/{document_id}/users")
async def get_document_collaborators(document_id: str):
    """获取文档的协作者列表"""
    doc = collaboration_manager.get_document(document_id)
    if not doc:
        return {"status": "error", "message": "Document not being collaborated"}
    
    return {
        "status": "success",
        "document_id": document_id,
        "users": [c.to_dict() for c in doc.cursors.values()]
    }


@router.post("/collaboration/documents/{document_id}/sync")
async def sync_document_to_db(document_id: str):
    """
    将协作文档内容同步回数据库
    建议在协作结束后调用，保存最终版本
    """
    doc = collaboration_manager.get_document(document_id)
    if not doc:
        return {"status": "error", "message": "Document not being collaborated"}
    
    try:
        # 更新数据库中的文档
        updated = document_service.update_document(
            document_id=document_id,
            content=doc.content
        )
        
        if updated:
            return {
                "status": "success",
                "message": "Document synced to database",
                "revision": doc.revision,
                "content_length": len(doc.content)
            }
        else:
            return {"status": "error", "message": "Failed to sync document"}
    
    except Exception as e:
        return {"status": "error", "message": str(e)}
