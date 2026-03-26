"""
对话润色 API 路由
提供多轮对话润色功能
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query

from app.models.polish_conversation import (
    PolishConversation, PolishMessage, ConversationCreate, ConversationUpdate,
    MessageCreate, MessageResponse, PolishMode, ConversationStatus
)
from app.services.polish_conversation import polish_service

router = APIRouter(prefix="/polish", tags=["对话润色"])


# ========== 对话管理 ==========

@router.post("/conversations", response_model=PolishConversation, summary="创建润色对话")
async def create_conversation(
    data: ConversationCreate,
    current_user_id: str = "test_user"
):
    """
    创建新的润色对话会话
    
    可以关联到特定文档，也可以独立使用
    """
    try:
        conversation = polish_service.create_conversation(
            title=data.title,
            user_id=current_user_id,
            document_id=data.document_id,
            document_context=data.document_context,
            initial_mode=data.initial_mode
        )
        return conversation
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建对话失败: {str(e)}")


@router.get("/conversations", response_model=List[PolishConversation], summary="获取对话列表")
async def list_conversations(
    document_id: Optional[str] = Query(None, description="关联文档ID"),
    status: Optional[ConversationStatus] = Query(None, description="状态筛选"),
    current_user_id: str = "test_user"
):
    """
    获取当前用户的润色对话列表
    """
    return polish_service.list_conversations(
        user_id=current_user_id,
        document_id=document_id,
        status=status
    )


@router.get("/conversations/{conversation_id}", response_model=PolishConversation, summary="获取对话详情")
async def get_conversation(
    conversation_id: str,
    current_user_id: str = "test_user"
):
    """
    获取单个对话的详细信息，包括所有消息
    """
    conversation = polish_service.get_conversation(conversation_id)
    
    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    if conversation.user_id != current_user_id:
        raise HTTPException(status_code=403, detail="无权访问此对话")
    
    return conversation


@router.put("/conversations/{conversation_id}", response_model=PolishConversation, summary="更新对话")
async def update_conversation(
    conversation_id: str,
    data: ConversationUpdate,
    current_user_id: str = "test_user"
):
    """
    更新对话信息（标题、状态、润色模式）
    """
    conversation = polish_service.get_conversation(conversation_id)
    
    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    if conversation.user_id != current_user_id:
        raise HTTPException(status_code=403, detail="无权修改此对话")
    
    updated = polish_service.update_conversation(
        conversation_id=conversation_id,
        title=data.title,
        status=data.status,
        current_mode=data.current_mode
    )
    
    return updated


@router.delete("/conversations/{conversation_id}", summary="删除对话")
async def delete_conversation(
    conversation_id: str,
    current_user_id: str = "test_user"
):
    """
    删除对话及其所有消息历史
    """
    conversation = polish_service.get_conversation(conversation_id)
    
    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    if conversation.user_id != current_user_id:
        raise HTTPException(status_code=403, detail="无权删除此对话")
    
    success = polish_service.delete_conversation(conversation_id)
    
    if success:
        return {"status": "success", "message": "对话已删除"}
    else:
        raise HTTPException(status_code=500, detail="删除失败")


# ========== 消息交互 ==========

@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=MessageResponse,
    summary="发送消息"
)
async def send_message(
    conversation_id: str,
    data: MessageCreate,
    current_user_id: str = "test_user"
):
    """
    向对话发送消息，AI 会回复润色建议
    
    如果有选中的文本，AI 会专门针对该文本进行润色
    """
    conversation = polish_service.get_conversation(conversation_id)
    
    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    if conversation.user_id != current_user_id:
        raise HTTPException(status_code=403, detail="无权访问此对话")
    
    try:
        response = await polish_service.send_message(
            conversation_id=conversation_id,
            content=data.content,
            selected_text=data.selected_text
        )
        
        return response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"润色服务错误: {str(e)}")


@router.get(
    "/conversations/{conversation_id}/history",
    summary="获取对话历史"
)
async def get_conversation_history(
    conversation_id: str,
    current_user_id: str = "test_user"
):
    """
    获取对话的消息历史（用于显示）
    """
    conversation = polish_service.get_conversation(conversation_id)
    
    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    if conversation.user_id != current_user_id:
        raise HTTPException(status_code=403, detail="无权访问此对话")
    
    history = polish_service.get_conversation_history(conversation_id)
    return {"messages": history}


# ========== 润色模式 ==========

@router.get("/modes", summary="获取润色模式列表")
async def get_polish_modes():
    """
    获取所有可用的润色模式
    
    包括：通用润色、正式化、精简、扩充、政策化、风格学习
    """
    return {
        "modes": polish_service.get_polish_modes()
    }


@router.post(
    "/conversations/{conversation_id}/mode/{mode}",
    response_model=PolishConversation,
    summary="切换润色模式"
)
async def switch_mode(
    conversation_id: str,
    mode: PolishMode,
    current_user_id: str = "test_user"
):
    """
    切换当前对话的润色模式
    
    模式会立即生效，后续消息将使用新模式
    """
    conversation = polish_service.get_conversation(conversation_id)
    
    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    if conversation.user_id != current_user_id:
        raise HTTPException(status_code=403, detail="无权访问此对话")
    
    updated = polish_service.switch_mode(conversation_id, mode)
    
    if not updated:
        raise HTTPException(status_code=500, detail="切换模式失败")
    
    return updated


# ========== 应用润色结果 ==========

@router.post(
    "/conversations/{conversation_id}/apply/{message_id}",
    summary="应用润色结果"
)
async def apply_polish(
    conversation_id: str,
    message_id: str,
    current_user_id: str = "test_user"
):
    """
    应用指定消息的润色结果到文档
    
    返回润色后的文本内容，客户端可将其应用到文档
    """
    conversation = polish_service.get_conversation(conversation_id)
    
    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    if conversation.user_id != current_user_id:
        raise HTTPException(status_code=403, detail="无权访问此对话")
    
    polished_text = polish_service.apply_polish(conversation_id, message_id)
    
    if not polished_text:
        raise HTTPException(status_code=404, detail="找不到可应用的润色结果")
    
    return {
        "status": "success",
        "polished_text": polished_text
    }