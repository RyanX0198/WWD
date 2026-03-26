"""
写作 API 路由
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.config import settings
from app.core.harness import writing_harness
from app.core.security import get_current_active_user

router = APIRouter()


# 根据配置决定是否启用认证
# 开发环境可以设置为 False
ENABLE_AUTH = False  # 可以在 .env 中配置


def get_auth_dependency():
    """获取认证依赖（可配置）"""
    if ENABLE_AUTH:
        return Depends(get_current_active_user)
    else:
        # 返回一个空依赖，不执行认证
        return Depends(lambda: None)


class WritingRequest(BaseModel):
    document_type: str  # 公文类型
    topic: str  # 主题
    requirements: str = ""  # 具体要求（可选）


class WritingResponse(BaseModel):
    status: str
    document_type: str
    topic: str
    outline: list = []
    draft: str = ""
    references: list = []


@router.post("/generate", response_model=WritingResponse)
async def generate_document(
    request: WritingRequest,
    current_user: Optional[dict] = get_auth_dependency()
):
    """
    生成公文
    
    需要认证（如果启用了 ENABLE_AUTH）
    """
    try:
        result = await writing_harness.write(
            document_type=request.document_type,
            topic=request.topic
        )
        
        return WritingResponse(
            status="success",
            document_type=request.document_type,
            topic=request.topic,
            outline=result.get("outline", []),
            draft=result.get("draft", ""),
            references=result.get("references", [])
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/outline")
async def generate_outline(
    request: WritingRequest,
    current_user: Optional[dict] = get_auth_dependency()
):
    """
    仅生成大纲
    """
    # TODO: 实现大纲生成接口
    return {"status": "success", "outline": []}


@router.post("/polish")
async def polish_document(
    text: str, 
    style: str = "formal",
    current_user: Optional[dict] = get_auth_dependency()
):
    """
    润色文档
    """
    # TODO: 实现润色接口
    return {"status": "success", "polished_text": text}