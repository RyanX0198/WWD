"""
政府公文智能写作助手 - 后端服务入口
"""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import documents, documents_v2, knowledge, writing, templates, auth, organizations, polish, styles, collaboration
from app.core.config import settings
from app.db import init_database
from app.services.collaboration import collaboration_manager

# 初始化数据库
init_database()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时：启动协作清理任务
    await collaboration_manager.start_cleanup_task()
    yield
    # 关闭时：清理资源


app = FastAPI(
    title="政府公文智能写作助手 API",
    description="基于 Agent Harness 架构的智能公文写作系统",
    version="0.2.0",
    lifespan=lifespan
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
app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(collaboration.router, prefix="/api", tags=["实时协作"])
app.include_router(styles.router, prefix="/api", tags=["写作风格"])
app.include_router(organizations.router, prefix="/api/orgs", tags=["机构管理"])
app.include_router(polish.router, prefix="/api/polish", tags=["对话润色"])
app.include_router(writing.router, prefix="/api/writing", tags=["写作"])
app.include_router(knowledge.router, prefix="/api/knowledge", tags=["知识库"])
app.include_router(templates.router, prefix="/api/templates", tags=["模板中心"])
app.include_router(documents_v2.router, prefix="/api/v2/documents", tags=["文档管理"])
app.include_router(documents.router, prefix="/api/documents", tags=["文档导出"])

# 静态文件服务（用于测试页面）
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


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