"""
写作 API 路由
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.harness import writing_harness

router = APIRouter()


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
async def generate_document(request: WritingRequest):
    """
    生成公文
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
async def generate_outline(request: WritingRequest):
    """
    仅生成大纲
    """
    # TODO: 实现大纲生成接口
    return {"status": "success", "outline": []}


@router.post("/polish")
async def polish_document(text: str, style: str = "formal"):
    """
    润色文档
    """
    # TODO: 实现润色接口
    return {"status": "success", "polished_text": text}