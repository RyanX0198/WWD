"""
对话润色服务
处理多轮对话和润色逻辑
"""
import json
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path

from app.models.polish_conversation import (
    PolishConversation, PolishMessage, MessageRole, ConversationStatus,
    PolishMode, MessageResponse, POLISH_MODES
)
from app.core.config import settings
from app.core.llm_router import llm_router


class PolishConversationService:
    """对话润色服务"""
    
    def __init__(self):
        self.data_dir = Path(settings.KNOWLEDGE_BASE_PATH) / "conversations"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._cache: Dict[str, PolishConversation] = {}
        self._load_data()
    
    def _load_data(self):
        """从文件加载对话数据"""
        for file_path in self.data_dir.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    conversation = PolishConversation(**data)
                    self._cache[conversation.id] = conversation
            except Exception as e:
                print(f"加载对话数据失败 {file_path}: {e}")
    
    def _save_conversation(self, conversation: PolishConversation):
        """保存单个对话到文件"""
        file_path = self.data_dir / f"{conversation.id}.json"
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(conversation.to_dict(), f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存对话失败: {e}")
    
    def _get_system_prompt(self, mode: PolishMode) -> str:
        """根据润色模式获取系统提示词"""
        prompts = {
            PolishMode.GENERAL: """你是一位专业的公文润色助手。请优化用户的文本表达，使其更加清晰、流畅、专业。

润色原则：
- 保持原意不变
- 优化句式结构
- 提升语言规范性
- 去除口语化表达

请直接给出润色后的文本，并简要说明修改理由。""",
            
            PolishMode.FORMAL: """你是一位政府公文专家。请将用户的文本转换为正式的公文语言风格。

转换原则：
- 使用规范的公文用语
- 采用正式的语气和称谓
- 遵循公文格式要求
- 增强权威性和严肃性

请直接给出正式化后的文本。""",
            
            PolishMode.CONCISE: """你是一位文字精简专家。请对用户的文本进行精简，去除冗余内容。

精简原则：
- 保留核心观点和关键信息
- 删除重复和冗余表述
- 压缩过长的句子
- 合并相似内容

请给出精简后的文本，并说明删除的内容。""",
            
            PolishMode.EXPAND: """你是一位内容扩充专家。请对用户的文本进行丰富和扩充。

扩充原则：
- 增加具体事例和数据支撑
- 补充背景信息和上下文
- 深化论述层次
- 增强说服力

请给出扩充后的文本，并说明新增的内容。""",
            
            PolishMode.POLICY: """你是一位政策文件专家。请对用户的文本进行政策化处理。

政策化原则：
- 使用准确的政策术语
- 引用相关政策法规
- 体现政策精神
- 增强规范性和权威性

请给出政策化后的文本，并说明修改依据。""",
            
            PolishMode.STYLE_LEARN: """你是一位写作风格学习专家。请基于用户的历史文档学习其写作风格，并应用润色。

风格学习原则：
- 分析用户的用词习惯
- 学习句式结构特点
- 保持语言风格一致
- 个性化润色建议

请给出符合用户风格的润色结果。"""
        }
        return prompts.get(mode, prompts[PolishMode.GENERAL])
    
    def _build_messages_for_llm(
        self,
        conversation: PolishConversation,
        new_user_message: str
    ) -> List[Dict[str, str]]:
        """构建发送给 LLM 的消息列表"""
        messages = []
        
        # 系统提示
        system_prompt = self._get_system_prompt(conversation.current_mode)
        
        # 如果有选中的文本，添加到上下文
        if conversation.selected_text:
            system_prompt += f"\n\n用户当前选中的文本：\n{conversation.selected_text}"
        
        messages.append({"role": "system", "content": system_prompt})
        
        # 添加历史消息（最近 10 条，避免超出上下文）
        recent_messages = conversation.messages[-10:] if len(conversation.messages) > 10 else conversation.messages
        
        for msg in recent_messages:
            if msg.role == MessageRole.USER:
                messages.append({"role": "user", "content": msg.content})
            elif msg.role == MessageRole.ASSISTANT:
                messages.append({"role": "assistant", "content": msg.content})
        
        # 添加新消息
        messages.append({"role": "user", "content": new_user_message})
        
        return messages
    
    def _parse_ai_response(self, response: str) -> Dict[str, Any]:
        """解析 AI 响应，提取润色后的文本"""
        # 简单的解析逻辑，后续可以优化
        lines = response.strip().split('\n')
        
        # 尝试找到润色后的文本（通常在开头或标记之后）
        polished_text = response
        explanation = ""
        
        # 如果包含 "润色后" 或类似标记
        if "润色后" in response or "修改后" in response:
            parts = response.split("\n\n", 1)
            if len(parts) > 1:
                polished_text = parts[0].replace("润色后：", "").replace("修改后：", "").strip()
                explanation = parts[1]
        
        return {
            "polished_text": polished_text,
            "explanation": explanation,
            "raw_response": response
        }
    
    # ========== 对话管理 ==========
    
    def create_conversation(
        self,
        title: str,
        user_id: str,
        document_id: Optional[str] = None,
        document_context: Optional[str] = None,
        initial_mode: PolishMode = PolishMode.GENERAL
    ) -> PolishConversation:
        """创建新对话"""
        conversation = PolishConversation(
            id=str(uuid.uuid4()),
            title=title,
            user_id=user_id,
            document_id=document_id,
            document_context=document_context,
            current_mode=initial_mode,
            messages=[],
            message_count=0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self._cache[conversation.id] = conversation
        self._save_conversation(conversation)
        
        return conversation
    
    def get_conversation(self, conversation_id: str) -> Optional[PolishConversation]:
        """获取对话"""
        return self._cache.get(conversation_id)
    
    def list_conversations(
        self,
        user_id: str,
        document_id: Optional[str] = None,
        status: Optional[ConversationStatus] = None
    ) -> List[PolishConversation]:
        """获取用户的对话列表"""
        result = []
        
        for conv in self._cache.values():
            if conv.user_id != user_id:
                continue
            
            if document_id and conv.document_id != document_id:
                continue
            
            if status and conv.status != status:
                continue
            
            result.append(conv)
        
        # 按更新时间排序
        result.sort(key=lambda x: x.updated_at, reverse=True)
        return result
    
    def update_conversation(
        self,
        conversation_id: str,
        title: Optional[str] = None,
        status: Optional[ConversationStatus] = None,
        current_mode: Optional[PolishMode] = None
    ) -> Optional[PolishConversation]:
        """更新对话"""
        conversation = self._cache.get(conversation_id)
        if not conversation:
            return None
        
        if title is not None:
            conversation.title = title
        if status is not None:
            conversation.status = status
        if current_mode is not None:
            conversation.current_mode = current_mode
        
        conversation.updated_at = datetime.utcnow()
        self._save_conversation(conversation)
        
        return conversation
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """删除对话"""
        if conversation_id not in self._cache:
            return False
        
        del self._cache[conversation_id]
        
        file_path = self.data_dir / f"{conversation_id}.json"
        if file_path.exists():
            file_path.unlink()
        
        return True
    
    # ========== 消息交互 ==========
    
    async def send_message(
        self,
        conversation_id: str,
        content: str,
        selected_text: Optional[str] = None
    ) -> Optional[MessageResponse]:
        """
        发送消息并获取 AI 回复
        
        Args:
            conversation_id: 对话ID
            content: 用户消息内容
            selected_text: 选中的文本（可选）
            
        Returns:
            包含用户消息、AI回复和更新后文档的响应
        """
        conversation = self._cache.get(conversation_id)
        if not conversation:
            return None
        
        if conversation.status != ConversationStatus.ACTIVE:
            raise ValueError("对话不在活跃状态，无法发送消息")
        
        # 更新选中的文本
        if selected_text:
            conversation.selected_text = selected_text
        
        # 创建用户消息
        user_message = PolishMessage(
            id=str(uuid.uuid4()),
            role=MessageRole.USER,
            content=content,
            polish_mode=conversation.current_mode,
            original_text=selected_text
        )
        
        conversation.messages.append(user_message)
        
        # 构建 LLM 消息
        llm_messages = self._build_messages_for_llm(conversation, content)
        
        # 调用 LLM
        try:
            response = await llm_router.generate(
                messages=llm_messages,
                temperature=0.7,
                task="polish"
            )
            
            ai_content = response.get("content", "")
            
            # 解析响应
            parsed = self._parse_ai_response(ai_content)
            
            # 创建 AI 回复消息
            ai_message = PolishMessage(
                id=str(uuid.uuid4()),
                role=MessageRole.ASSISTANT,
                content=ai_content,
                polish_mode=conversation.current_mode,
                original_text=selected_text,
                polished_text=parsed.get("polished_text"),
                metadata={"explanation": parsed.get("explanation", "")}
            )
            
            conversation.messages.append(ai_message)
            conversation.message_count = len(conversation.messages)
            conversation.updated_at = datetime.utcnow()
            
            self._save_conversation(conversation)
            
            return MessageResponse(
                message=user_message,
                ai_response=ai_message,
                updated_document=parsed.get("polished_text") if selected_text else None
            )
            
        except Exception as e:
            print(f"AI 调用失败: {e}")
            raise ValueError(f"润色服务暂时不可用: {str(e)}")
    
    # ========== 润色模式 ==========
    
    def get_polish_modes(self) -> List[Dict[str, Any]]:
        """获取所有润色模式信息"""
        return [
            {
                "mode": pm.mode.value,
                "name": pm.name,
                "description": pm.description,
                "icon": pm.icon
            }
            for pm in POLISH_MODES
        ]
    
    def switch_mode(self, conversation_id: str, mode: PolishMode) -> Optional[PolishConversation]:
        """切换润色模式"""
        conversation = self._cache.get(conversation_id)
        if not conversation:
            return None
        
        conversation.current_mode = mode
        conversation.updated_at = datetime.utcnow()
        
        self._save_conversation(conversation)
        
        return conversation
    
    # ========== 工具方法 ==========
    
    def get_conversation_history(self, conversation_id: str) -> Optional[List[Dict[str, Any]]]:
        """获取对话历史（用于显示）"""
        conversation = self._cache.get(conversation_id)
        if not conversation:
            return None
        
        return [msg.to_dict() for msg in conversation.messages]
    
    def apply_polish(
        self,
        conversation_id: str,
        message_id: str
    ) -> Optional[str]:
        """
        应用指定消息的润色结果到文档
        
        Returns:
            润色后的文本，如果找不到则返回 None
        """
        conversation = self._cache.get(conversation_id)
        if not conversation:
            return None
        
        for msg in conversation.messages:
            if msg.id == message_id and msg.polished_text:
                return msg.polished_text
        
        return None


# 全局服务实例
polish_service = PolishConversationService()