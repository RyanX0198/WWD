"""
政府公文智能写作助手 - 后端服务入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import documents, knowledge, writing
from app.core.config import settings

app = FastAPI(
    title="政府公文智能写作助手 API",
    description="基于 Agent Harness 架构的智能公文写作系统",
    version="0.1.0"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:1420", "http://localhost:3000"],  # Tauri 默认端口
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(writing.router, prefix="/api/writing", tags=["写作"])
app.include_router(knowledge.router, prefix="/api/knowledge", tags=["知识库"])
app.include_router(documents.router, prefix="/api/documents", tags=["文档"])


@app.get("/")
async def root():
    return {
        "message": "政府公文智能写作助手 API",
        "version": "0.1.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    return {"status": "ok"}