"""
LLM 多模型路由
以国内模型为主力，国外模型为备用
支持: Kimi、通义千问、ChatGLM、MiniMax、GPT、Claude
"""
import os
from typing import Optional, Literal
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic


class LLMRouter:
    """LLM 路由器 - 国内模型优先"""
    
    # 模型优先级配置
    PRIMARY_MODELS = ["kimi-k2p5", "qwen-max", "glm-4", "minimax-ab6"]  # 国内主力
    FALLBACK_MODELS = ["gpt-5", "claude-sonnet-4"]  # 国外备用
    
    def __init__(self):
        self.models = {}
        self._init_models()
    
    def _init_models(self):
        """初始化所有模型 - 国内模型优先"""
        
        # ========== 国内模型（主力）==========
        
        # 1. Kimi (Moonshot)
        if os.getenv("KIMI_API_KEY"):
            # Kimi 使用 OpenAI 兼容接口
            self.models["kimi-k2p5"] = ChatOpenAI(
                model="kimi-k2-5",
                temperature=0.7,
                max_tokens=4000,
                api_key=os.getenv("KIMI_API_KEY"),
                base_url="https://api.moonshot.cn/v1"
            )
            # Kimi 轻量版
            self.models["kimi-k2"] = ChatOpenAI(
                model="kimi-k2",
                temperature=0.7,
                max_tokens=2000,
                api_key=os.getenv("KIMI_API_KEY"),
                base_url="https://api.moonshot.cn/v1"
            )
        
        # 2. 通义千问 (Aliyun)
        if os.getenv("DASHSCOPE_API_KEY"):
            self.models["qwen-max"] = ChatOpenAI(
                model="qwen-max",
                temperature=0.7,
                max_tokens=4000,
                api_key=os.getenv("DASHSCOPE_API_KEY"),
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
            )
            self.models["qwen-plus"] = ChatOpenAI(
                model="qwen-plus",
                temperature=0.7,
                max_tokens=2000,
                api_key=os.getenv("DASHSCOPE_API_KEY"),
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
            )
        
        # 3. ChatGLM (Zhipu)
        if os.getenv("ZHIPU_API_KEY"):
            self.models["glm-4"] = ChatOpenAI(
                model="glm-4",
                temperature=0.7,
                max_tokens=4000,
                api_key=os.getenv("ZHIPU_API_KEY"),
                base_url="https://open.bigmodel.cn/api/paas/v4"
            )
            self.models["glm-4-flash"] = ChatOpenAI(
                model="glm-4-flash",
                temperature=0.7,
                max_tokens=2000,
                api_key=os.getenv("ZHIPU_API_KEY"),
                base_url="https://open.bigmodel.cn/api/paas/v4"
            )
        
        # 4. MiniMax
        if os.getenv("MINIMAX_API_KEY"):
            self.models["minimax-ab6"] = ChatOpenAI(
                model="abab6-chat",
                temperature=0.7,
                max_tokens=4000,
                api_key=os.getenv("MINIMAX_API_KEY"),
                base_url="https://api.minimax.chat/v1"
            )
            self.models["minimax-ab5"] = ChatOpenAI(
                model="abab5.5-chat",
                temperature=0.7,
                max_tokens=2000,
                api_key=os.getenv("MINIMAX_API_KEY"),
                base_url="https://api.minimax.chat/v1"
            )
        
        # ========== 国外模型（备用）==========
        
        # GPT (OpenAI)
        if os.getenv("OPENAI_API_KEY"):
            self.models["gpt-5"] = ChatOpenAI(
                model="gpt-5",
                temperature=0.7,
                max_tokens=4000,
                api_key=os.getenv("OPENAI_API_KEY")
            )
            self.models["gpt-4o"] = ChatOpenAI(
                model="gpt-4o",
                temperature=0.7,
                max_tokens=2000,
                api_key=os.getenv("OPENAI_API_KEY")
            )
        
        # Claude (Anthropic)
        if os.getenv("ANTHROPIC_API_KEY"):
            self.models["claude-sonnet-4"] = ChatAnthropic(
                model="claude-sonnet-4-20250529",
                temperature=0.7,
                max_tokens=4000,
                api_key=os.getenv("ANTHROPIC_API_KEY")
            )
    
    def _get_first_available(self, model_list: list) -> Optional[BaseChatModel]:
        """从列表中获取第一个可用的模型"""
        for model_name in model_list:
            if model_name in self.models:
                return self.models[model_name]
        return None
    
    def get_model(
        self,
        task_type: Literal["writing", "outline", "polish", "search"] = "writing",
        preferred: Optional[str] = None
    ) -> BaseChatModel:
        """
        根据任务类型获取合适的模型 - 国内模型优先
        
        Args:
            task_type: 任务类型
            preferred: 优先使用的模型（可选）
        
        Returns:
            对应的 LLM 模型
        """
        # 如果指定了优先模型且可用
        if preferred and preferred in self.models:
            return self.models[preferred]
        
        # 根据任务类型路由 - 优先国内模型
        if task_type == "outline":
            # 大纲生成用国内轻量级模型
            return (self._get_first_available(["kimi-k2", "qwen-plus", "glm-4-flash", "minimax-ab5"]) 
                    or self._get_first_available(self.PRIMARY_MODELS)
                    or self._get_first_available(self.FALLBACK_MODELS)
                    or list(self.models.values())[0])
        
        elif task_type == "polish":
            # 润色用国内主力模型
            return (self._get_first_available(["kimi-k2p5", "qwen-max", "glm-4"])
                    or self._get_first_available(self.PRIMARY_MODELS)
                    or self._get_first_available(self.FALLBACK_MODELS)
                    or list(self.models.values())[0])
        
        elif task_type == "search":
            # 知识检索用国内轻量级模型
            return (self._get_first_available(["kimi-k2", "qwen-plus", "glm-4-flash"])
                    or self._get_first_available(self.PRIMARY_MODELS)
                    or self._get_first_available(self.FALLBACK_MODELS)
                    or list(self.models.values())[0])
        
        else:
            # 默认用国内主力模型
            return (self._get_first_available(self.PRIMARY_MODELS)
                    or self._get_first_available(self.FALLBACK_MODELS)
                    or list(self.models.values())[0])
    
    def list_available(self) -> dict:
        """列出所有可用的模型（分类显示）"""
        return {
            "primary": [m for m in self.PRIMARY_MODELS if m in self.models],
            "fallback": [m for m in self.FALLBACK_MODELS if m in self.models],
            "all": list(self.models.keys())
        }
    
    def get_primary_model(self) -> Optional[BaseChatModel]:
        """获取首选国内主力模型"""
        return self._get_first_available(self.PRIMARY_MODELS)


# 全局路由器实例
llm_router = LLMRouter()