"""
写作风格管理 API
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.services.style_learning import style_learning_service
from app.core.security import get_current_active_user

router = APIRouter(prefix="/styles", tags=["写作风格"])


# 可配置认证开关
ENABLE_AUTH = False


def get_auth_dependency():
    """获取认证依赖（可配置）"""
    if ENABLE_AUTH:
        return Depends(get_current_active_user)
    else:
        return Depends(lambda: None)


# ========== 请求/响应模型 ==========

class StyleCreateRequest(BaseModel):
    name: str
    description: str = ""
    sample_documents: List[str] = []


class StyleUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    features: Optional[dict] = None


class StyleLearnRequest(BaseModel):
    document: str


class StyleResponse(BaseModel):
    style_id: str
    name: str
    description: str
    features: dict
    is_default: bool
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


# ========== API 路由 ==========

@router.get("", response_model=List[StyleResponse])
async def list_styles(
    current_user: Optional[dict] = get_auth_dependency()
):
    """获取所有写作风格列表"""
    styles = style_learning_service.list_styles()
    return styles


@router.get("/{style_id}", response_model=StyleResponse)
async def get_style(
    style_id: str,
    current_user: Optional[dict] = get_auth_dependency()
):
    """获取特定风格的详细信息"""
    style = style_learning_service.get_style(style_id)
    if not style:
        raise HTTPException(status_code=404, detail="风格不存在")
    
    return {
        **style.to_dict(),
        "is_default": style_id in style_learning_service.default_styles
    }


@router.post("", response_model=StyleResponse)
async def create_style(
    request: StyleCreateRequest,
    current_user: Optional[dict] = get_auth_dependency()
):
    """创建新风格（基于样本文档自动分析）"""
    style = style_learning_service.create_style(
        name=request.name,
        description=request.description,
        sample_documents=request.sample_documents
    )
    
    return {
        **style.to_dict(),
        "is_default": False
    }


@router.put("/{style_id}", response_model=StyleResponse)
async def update_style(
    style_id: str,
    request: StyleUpdateRequest,
    current_user: Optional[dict] = get_auth_dependency()
):
    """更新风格信息"""
    style = style_learning_service.update_style(
        style_id=style_id,
        name=request.name,
        description=request.description,
        features=request.features
    )
    
    if not style:
        raise HTTPException(status_code=404, detail="风格不存在或不能修改默认风格")
    
    return {
        **style.to_dict(),
        "is_default": False
    }


@router.delete("/{style_id}")
async def delete_style(
    style_id: str,
    current_user: Optional[dict] = get_auth_dependency()
):
    """删除风格"""
    success = style_learning_service.delete_style(style_id)
    if not success:
        raise HTTPException(status_code=404, detail="风格不存在或不能删除默认风格")
    
    return {"status": "success", "message": "风格已删除"}


@router.post("/{style_id}/learn")
async def learn_from_document(
    style_id: str,
    request: StyleLearnRequest,
    current_user: Optional[dict] = get_auth_dependency()
):
    """从文档学习并更新风格"""
    success = await style_learning_service.learn_from_document(
        style_id=style_id,
        document=request.document
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="风格不存在或不能修改默认风格")
    
    return {"status": "success", "message": "风格学习完成"}


@router.post("/{style_id}/analyze")
async def analyze_documents(
    style_id: str,
    documents: List[str],
    current_user: Optional[dict] = get_auth_dependency()
):
    """分析一组文档的风格特征（不保存）"""
    features = style_learning_service._analyze_style_features(documents)
    return {
        "status": "success",
        "features": features
    }


@router.get("/{style_id}/prompt")
async def get_style_prompt(
    style_id: str,
    current_user: Optional[dict] = get_auth_dependency()
):
    """获取风格提示词（用于写作）"""
    prompt = style_learning_service.get_style_prompt(style_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="风格不存在")
    
    return {
        "style_id": style_id,
        "prompt": prompt
    }


# ========== 预定义风格快捷接口 ==========

@router.get("/defaults/list")
async def list_default_styles(
    current_user: Optional[dict] = get_auth_dependency()
):
    """获取预定义风格列表"""
    return [
        {
            "style_id": style_id,
            "name": data["name"],
            "description": data["description"],
            "features": data["features"]
        }
        for style_id, data in style_learning_service.default_styles.items()
    ]
