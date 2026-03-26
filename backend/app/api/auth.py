"""
认证 API 路由
处理登录、注册、用户信息等
"""
from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from app.core.config import settings
from app.core.security import create_access_token, get_current_active_user
from app.core.users import authenticate_user, create_user, get_user_by_username

router = APIRouter(prefix="/auth", tags=["认证"])


# ========== 请求/响应模型 ==========

class Token(BaseModel):
    """令牌响应模型"""
    access_token: str
    token_type: str
    expires_in: int


class UserCreate(BaseModel):
    """用户创建请求模型"""
    username: str
    email: str
    password: str


class UserResponse(BaseModel):
    """用户响应模型"""
    id: str
    username: str
    email: str
    is_active: bool


class UserLogin(BaseModel):
    """用户登录请求模型（用于文档）"""
    username: str
    password: str


# ========== API 端点 ==========

@router.post("/login", response_model=Token, summary="用户登录")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    用户登录接口
    
    使用 OAuth2 密码模式获取访问令牌
    
    - **username**: 用户名
    - **password**: 密码
    """
    user = authenticate_user(form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户未激活"
        )
    
    # 创建访问令牌
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user.id,
            "username": user.username,
            "is_active": user.is_active
        },
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


@router.post("/register", response_model=UserResponse, summary="用户注册")
async def register(user_data: UserCreate):
    """
    用户注册接口
    
    创建新用户账号
    """
    try:
        user = create_user(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password
        )
        
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_active": user.is_active
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/me", response_model=UserResponse, summary="获取当前用户信息")
async def get_me(current_user: dict = Depends(get_current_active_user)):
    """
    获取当前登录用户信息
    
    需要有效的访问令牌
    """
    return {
        "id": current_user["id"],
        "username": current_user["username"],
        "email": current_user.get("email", ""),
        "is_active": current_user["is_active"]
    }


@router.post("/refresh", response_model=Token, summary="刷新访问令牌")
async def refresh_token(current_user: dict = Depends(get_current_active_user)):
    """
    刷新访问令牌
    
    使用当前有效的令牌获取新的令牌
    """
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": current_user["id"],
            "username": current_user["username"],
            "is_active": current_user["is_active"]
        },
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }