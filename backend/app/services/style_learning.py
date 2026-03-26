"""
写作风格学习服务
基于用户历史文档分析并学习写作风格特征
"""
import json
import re
from typing import Dict, List, Optional, TypedDict
from pathlib import Path
from datetime import datetime
from collections import Counter

from langchain_core.messages import HumanMessage

from app.core.llm_router import llm_router
from app.core.config import settings


class StyleFeature(TypedDict):
    """风格特征"""
    # 句式特征
    sentence_avg_length: float  # 平均句长
    sentence_structure: str  # 句式结构偏好
    
    # 词汇特征
    high_freq_words: List[str]  # 高频词汇
    characteristic_words: List[str]  # 特色词汇
    formal_degree: int  # 正式程度 1-10
    
    # 段落特征
    paragraph_avg_length: int  # 平均段落字数
    paragraph_structure: str  # 段落组织方式
    
    # 表达特征
    argument_style: str  # 论证方式
    example_habit: str  # 举例习惯
    transition_style: str  # 过渡方式
    
    # 整体印象
    overall_impression: str  # 整体风格描述
    typical_phrases: List[str]  # 典型用语


class WritingStyle:
    """写作风格配置"""
    
    def __init__(
        self,
        style_id: str,
        name: str,
        description: str = "",
        features: Optional[Dict] = None,
        sample_documents: List[str] = None,
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None
    ):
        self.style_id = style_id
        self.name = name
        self.description = description
        self.features = features or {}
        self.sample_documents = sample_documents or []
        self.created_at = created_at or datetime.now().isoformat()
        self.updated_at = updated_at or datetime.now().isoformat()
    
    def to_dict(self) -> dict:
        return {
            "style_id": self.style_id,
            "name": self.name,
            "description": self.description,
            "features": self.features,
            "sample_documents": self.sample_documents,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "WritingStyle":
        return cls(
            style_id=data["style_id"],
            name=data["name"],
            description=data.get("description", ""),
            features=data.get("features", {}),
            sample_documents=data.get("sample_documents", []),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at")
        )


class StyleLearningService:
    """风格学习服务"""
    
    def __init__(self):
        self.styles_dir = Path(settings.KNOWLEDGE_BASE_PATH) / "styles"
        self.styles_dir.mkdir(parents=True, exist_ok=True)
        
        # 预定义风格模板
        self.default_styles = {
            "formal": {
                "name": "正式严谨",
                "description": "语言规范、逻辑严密，适合重要讲话",
                "features": {
                    "formal_degree": 9,
                    "sentence_structure": "以完整长句为主，善用排比、对偶",
                    "argument_style": "层层递进，理论联系实际",
                    "transition_style": "使用规范过渡词，如'此外'、'同时'、'综上所述'"
                }
            },
            "pragmatic": {
                "name": "务实简洁",
                "description": "直切主题、数据说话，适合工作部署",
                "features": {
                    "formal_degree": 6,
                    "sentence_structure": "简洁明快，长短结合，多用短句",
                    "argument_style": "问题导向，数据支撑，措施具体",
                    "transition_style": "简洁过渡，直接切入"
                }
            },
            "vivid": {
                "name": "生动形象",
                "description": "语言活泼、案例丰富，适合交流发言",
                "features": {
                    "formal_degree": 5,
                    "sentence_structure": "灵活多变，善用比喻、引用",
                    "argument_style": "案例引入，情理结合",
                    "transition_style": "自然过渡，故事性强"
                }
            },
            "academic": {
                "name": "学术专业",
                "description": "术语准确、论述深入，适合专业报告",
                "features": {
                    "formal_degree": 8,
                    "sentence_structure": "严谨规范，逻辑严密",
                    "argument_style": "理论分析为主，引用权威",
                    "transition_style": "学术性过渡，如'基于以上分析'"
                }
            }
        }
    
    def _get_style_path(self, style_id: str) -> Path:
        """获取风格文件路径"""
        return self.styles_dir / f"{style_id}.json"
    
    def list_styles(self) -> List[dict]:
        """列出所有风格"""
        styles = []
        
        # 加载自定义风格
        for style_file in self.styles_dir.glob("*.json"):
            try:
                style = WritingStyle.from_dict(
                    json.loads(style_file.read_text(encoding="utf-8"))
                )
                styles.append({
                    **style.to_dict(),
                    "is_default": False
                })
            except Exception as e:
                print(f"Error loading style {style_file}: {e}")
        
        # 添加预定义风格
        for style_id, style_data in self.default_styles.items():
            styles.append({
                "style_id": style_id,
                "name": style_data["name"],
                "description": style_data["description"],
                "features": style_data["features"],
                "is_default": True,
                "created_at": None,
                "updated_at": None
            })
        
        return sorted(styles, key=lambda x: (not x["is_default"], x["name"]))
    
    def get_style(self, style_id: str) -> Optional[WritingStyle]:
        """获取特定风格"""
        # 检查预定义风格
        if style_id in self.default_styles:
            default = self.default_styles[style_id]
            return WritingStyle(
                style_id=style_id,
                name=default["name"],
                description=default["description"],
                features=default["features"]
            )
        
        # 检查自定义风格
        style_path = self._get_style_path(style_id)
        if style_path.exists():
            return WritingStyle.from_dict(
                json.loads(style_path.read_text(encoding="utf-8"))
            )
        
        return None
    
    def create_style(
        self,
        name: str,
        description: str = "",
        sample_documents: List[str] = None
    ) -> WritingStyle:
        """创建新风格"""
        style_id = f"custom_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        style = WritingStyle(
            style_id=style_id,
            name=name,
            description=description,
            sample_documents=sample_documents or []
        )
        
        # 如果有样本文档，自动分析风格
        if sample_documents:
            features = self._analyze_style_features(sample_documents)
            style.features = features
        
        # 保存
        style_path = self._get_style_path(style_id)
        style_path.write_text(
            json.dumps(style.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        
        return style
    
    def update_style(
        self,
        style_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        features: Optional[Dict] = None
    ) -> Optional[WritingStyle]:
        """更新风格"""
        style = self.get_style(style_id)
        if not style or style_id in self.default_styles:
            return None  # 不能修改预定义风格
        
        if name:
            style.name = name
        if description:
            style.description = description
        if features:
            style.features = features
        
        style.updated_at = datetime.now().isoformat()
        
        # 保存
        style_path = self._get_style_path(style_id)
        style_path.write_text(
            json.dumps(style.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        
        return style
    
    def delete_style(self, style_id: str) -> bool:
        """删除风格"""
        if style_id in self.default_styles:
            return False  # 不能删除预定义风格
        
        style_path = self._get_style_path(style_id)
        if style_path.exists():
            style_path.unlink()
            return True
        return False
    
    def _analyze_style_features(self, documents: List[str]) -> Dict:
        """分析文档的风格特征"""
        if not documents:
            return {}
        
        # 合并所有文档
        combined_text = "\n\n".join(documents)
        
        # 基础统计
        # 分句（简化处理）
        sentences = re.split(r'[。！？；\n]', combined_text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # 分词统计（简化版，实际可用jieba）
        words = re.findall(r'[\u4e00-\u9fff]+', combined_text)
        word_freq = Counter(words)
        high_freq_words = [w for w, c in word_freq.most_common(20) if len(w) >= 2]
        
        # 段落统计
        paragraphs = [p.strip() for p in combined_text.split('\n\n') if p.strip()]
        para_lengths = [len(p) for p in paragraphs]
        avg_para_length = sum(para_lengths) / len(para_lengths) if para_lengths else 0
        
        # 句长统计
        sentence_lengths = [len(s) for s in sentences]
        avg_sentence_length = sum(sentence_lengths) / len(sentence_lengths) if sentence_lengths else 0
        
        # 使用 LLM 进行深度分析
        model = llm_router.get_model(task_type="search")
        
        # 取样分析（避免token过多）
        sample_text = combined_text[:3000] if len(combined_text) > 3000 else combined_text
        
        prompt = f"""请分析以下公文的写作风格特征：

样本文本：
{sample_text}

请从以下维度分析并返回JSON格式：
{{
    "sentence_structure": "句式结构特点，如长短句比例、偏好句式等",
    "characteristic_words": ["特色词汇1", "特色词汇2", ...],
    "formal_degree": 8, // 正式程度评分 1-10
    "paragraph_structure": "段落组织方式",
    "argument_style": "论证方式和逻辑特点",
    "example_habit": "举例习惯",
    "transition_style": "过渡衔接方式",
    "overall_impression": "整体风格印象描述",
    "typical_phrases": ["典型用语1", "典型用语2", ...]
}}"""
        
        try:
            import asyncio
            response = asyncio.run(model.ainvoke([HumanMessage(content=prompt)]))
            content = response.content
            
            # 提取 JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            llm_features = json.loads(content.strip())
            
            # 合并统计特征
            return {
                **llm_features,
                "sentence_avg_length": round(avg_sentence_length, 1),
                "paragraph_avg_length": int(avg_para_length),
                "high_freq_words": high_freq_words[:10],
                "sample_count": len(documents),
                "analyzed_at": datetime.now().isoformat()
            }
        
        except Exception as e:
            print(f"LLM style analysis error: {e}")
            # 返回基础统计特征
            return {
                "sentence_avg_length": round(avg_sentence_length, 1),
                "paragraph_avg_length": int(avg_para_length),
                "high_freq_words": high_freq_words[:10],
                "sentence_structure": "待分析",
                "formal_degree": 7,
                "overall_impression": "基于统计的风格特征",
                "sample_count": len(documents),
                "analyzed_at": datetime.now().isoformat()
            }
    
    async def learn_from_document(self, style_id: str, document: str) -> bool:
        """从单个文档学习并更新风格"""
        style = self.get_style(style_id)
        if not style or style_id in self.default_styles:
            return False
        
        # 添加到样本文档
        style.sample_documents.append(document)
        
        # 重新分析（使用所有样本）
        # 限制样本数量，避免过多
        recent_samples = style.sample_documents[-10:]  # 最近10篇
        features = self._analyze_style_features(recent_samples)
        style.features = features
        style.updated_at = datetime.now().isoformat()
        
        # 保存
        style_path = self._get_style_path(style_id)
        style_path.write_text(
            json.dumps(style.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        
        return True
    
    def get_style_prompt(self, style_id: str) -> str:
        """获取风格提示词（用于写作时）"""
        style = self.get_style(style_id)
        if not style:
            return ""
        
        features = style.features
        
        prompt_parts = [f"【写作风格：{style.name}】"]
        
        if features.get("overall_impression"):
            prompt_parts.append(f"整体风格：{features['overall_impression']}")
        
        if features.get("sentence_structure"):
            prompt_parts.append(f"句式特点：{features['sentence_structure']}")
        
        if features.get("formal_degree"):
            formal_desc = [
                "非常口语化", "较口语化", "偏口语", "稍随意",
                "中性", "较正式", "正式", "很正式", "非常正式", "极致严谨"
            ][min(features["formal_degree"]-1, 9)]
            prompt_parts.append(f"正式程度：{formal_desc}({features['formal_degree']}/10)")
        
        if features.get("argument_style"):
            prompt_parts.append(f"论证方式：{features['argument_style']}")
        
        if features.get("transition_style"):
            prompt_parts.append(f"过渡衔接：{features['transition_style']}")
        
        if features.get("typical_phrases"):
            phrases = features["typical_phrases"][:5]
            prompt_parts.append(f"典型用语：{', '.join(phrases)}")
        
        if features.get("characteristic_words"):
            words = features["characteristic_words"][:5]
            prompt_parts.append(f"常用词汇：{', '.join(words)}")
        
        return "\n".join(prompt_parts)


# 全局服务实例
style_learning_service = StyleLearningService()
