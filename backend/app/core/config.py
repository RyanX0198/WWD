"""
应用配置
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 应用配置
    APP_NAME: str = "政府公文智能写作助手"
    DEBUG: bool = True
    
    # API 配置
    API_V1_STR: str = "/api"
    
    # LLM 配置 - 国内模型（主力）
    KIMI_API_KEY: str = ""
    DASHSCOPE_API_KEY: str = ""  # 通义千问
    ZHIPU_API_KEY: str = ""       # ChatGLM
    MINIMAX_API_KEY: str = ""
    
    # LLM 配置 - 国外模型（备用）
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    
    # 默认模型
    DEFAULT_MODEL: str = "kimi-k2.5"
    
    # Qdrant 配置
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    
    # Redis 配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    
    # 知识库路径
    KNOWLEDGE_BASE_PATH: str = "./knowledge"
    
    # JWT 认证配置
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 小时
    
    class Config:
        env_file = ".env"
        extra = "ignore"  # 忽略未定义的额外字段，避免报错


settings = Settings()