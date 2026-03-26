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
    
    # LLM 配置
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    KIMI_API_KEY: str = ""
    
    # 默认模型
    DEFAULT_MODEL: str = "gpt-5"
    
    # Qdrant 配置
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    
    # Redis 配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    
    # 知识库路径
    KNOWLEDGE_BASE_PATH: str = "./knowledge"
    
    class Config:
        env_file = ".env"


settings = Settings()