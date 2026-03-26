"""
LLM 多模型路由
支持 GPT-5、Claude、Kimi 等多个模型，按场景智能路由
"""
import os
from typing import Optional, Literal
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic


class LLMRouter:
    """LLM 路由器"""
    
    def __init__(self):
        self.models = {}
        self._init_models()
    
    def _init_models(self):
        """初始化所有模型"""
        # GPT-5 (主力)
        if os.getenv("OPENAI_API_KEY"):
            self.models["gpt-5"] = ChatOpenAI(
                model="gpt-5",
                temperature=0.7,
                max_tokens=4000,
                api_key=os.getenv("OPENAI_API_KEY")
            )
            self.models["gpt-5-mini"] = ChatOpenAI(
                model="gpt-5-mini",
                temperature=0.7,
                api_key=os.getenv("OPENAI_API_KEY")
            )
        
        # Claude (备用)
        if os.getenv("ANTHROPIC_API_KEY"):
            self.models["claude-sonnet-4"] = ChatAnthropic(
                model="claude-sonnet-4-20250529",
                temperature=0.7,
                max_tokens=4000,
                api_key=os.getenv("ANTHROPIC_API_KEY")
            )
        
        # TODO: 添加 Kimi 支持
        # if os.getenv("KIMI_API_KEY"):
        #     self.models["kimi-k2p5"] = ...
    
    def get_model(
        self,
        task_type: Literal["writing", "outline", "polish", "search"] = "writing",
        preferred: Optional[str] = None
    ) -> BaseChatModel:
        """
        根据任务类型获取合适的模型
        
        Args:
            task_type: 任务类型
            preferred: 优先使用的模型（可选）
        
        Returns:
            对应的 LLM 模型
        """
        # 如果指定了优先模型且可用
        if preferred and preferred in self.models:
            return self.models[preferred]
        
        # 根据任务类型路由
        if task_type == "outline":
            # 大纲生成用轻量级模型
            return self.models.get("gpt-5-mini") or self.models.get("gpt-5")
        
        elif task_type == "polish":
            # 润色用 Claude（文风更好）
            return self.models.get("claude-sonnet-4") or self.models.get("gpt-5")
        
        elif task_type == "search":
            # 知识检索用轻量级模型
            return self.models.get("gpt-5-mini") or self.models.get("gpt-5")
        
        else:
            # 默认用 GPT-5
            return self.models.get("gpt-5") or list(self.models.values())[0]
    
    def list_available(self) -> list:
        """列出所有可用的模型"""
        return list(self.models.keys())


# 全局路由器实例
llm_router = LLMRouter()