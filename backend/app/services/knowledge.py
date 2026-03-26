"""
知识库服务 - 向量检索 + 文件系统
"""
import os
import yaml
from typing import List, Optional, Dict
from pathlib import Path

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from langchain_openai import OpenAIEmbeddings

from app.core.config import settings


class KnowledgeService:
    """知识库服务"""
    
    def __init__(self):
        self.base_path = Path(settings.KNOWLEDGE_BASE_PATH)
        self.qdrant = None
        self.embeddings = None
        self._init_vector_db()
    
    def _init_vector_db(self):
        """初始化向量数据库"""
        try:
            self.qdrant = QdrantClient(
                host=settings.QDRANT_HOST,
                port=settings.QDRANT_PORT
            )
            
            # 初始化 embedding
            if os.getenv("OPENAI_API_KEY"):
                self.embeddings = OpenAIEmbeddings(
                    api_key=os.getenv("OPENAI_API_KEY")
                )
            
            # 创建集合（如果不存在）
            collections = ["people", "policies", "templates"]
            for collection in collections:
                try:
                    self.qdrant.create_collection(
                        collection_name=collection,
                        vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
                    )
                except Exception:
                    pass  # 集合已存在
                    
        except Exception as e:
            print(f"Vector DB init error: {e}")
            self.qdrant = None
    
    def get_person(self, name: str) -> Optional[Dict]:
        """
        获取人物档案
        
        Args:
            name: 人物姓名
            
        Returns:
            人物信息字典
        """
        person_file = self.base_path / "people" / f"{name}.md"
        
        if not person_file.exists():
            return None
        
        try:
            content = person_file.read_text(encoding="utf-8")
            return self._parse_person_md(content)
        except Exception as e:
            print(f"Error reading person file: {e}")
            return None
    
    def _parse_person_md(self, content: str) -> Dict:
        """解析人物 Markdown 文件"""
        person = {
            "name": "",
            "current_position": "",
            "level": "",
            "addressing_rules": {},
            "career": [],
            "responsibilities": []
        }
        
        lines = content.split("\n")
        current_section = None
        
        for line in lines:
            line = line.strip()
            
            if line.startswith("# "):
                person["name"] = line.replace("# ", "").strip()
            
            elif line.startswith("- **姓名**:"):
                person["name"] = line.split(":")[1].strip()
            
            elif line.startswith("- **现任职务**:"):
                person["current_position"] = line.split(":")[1].strip()
            
            elif line.startswith("- **行政级别**:"):
                person["level"] = line.split(":")[1].strip()
            
            elif "## 称谓规范" in line:
                current_section = "addressing"
            
            elif "## 履历" in line:
                current_section = "career"
            
            elif "## 分管领域" in line:
                current_section = "responsibilities"
            
            elif line.startswith("- **") and current_section == "addressing":
                key = line.split("**:")[0].replace("- **", "").strip()
                value = line.split(":")[1].strip()
                person["addressing_rules"][key] = value
            
            elif line.startswith("- ") and current_section == "career":
                person["career"].append(line.replace("- ", "").strip())
            
            elif line.startswith("- ") and current_section == "responsibilities":
                person["responsibilities"].append(line.replace("- ", "").strip())
        
        return person
    
    def search_people(self, query: str, limit: int = 5) -> List[Dict]:
        """
        搜索人物
        
        Args:
            query: 搜索关键词
            limit: 返回数量
            
        Returns:
            人物列表
        """
        people_dir = self.base_path / "people"
        results = []
        
        if not people_dir.exists():
            return results
        
        for md_file in people_dir.glob("*.md"):
            try:
                content = md_file.read_text(encoding="utf-8")
                # 简单关键词匹配（后续可用向量检索）
                if query in content or query in md_file.stem:
                    person = self._parse_person_md(content)
                    if person["name"]:
                        results.append(person)
            except Exception as e:
                print(f"Error reading {md_file}: {e}")
        
        return results[:limit]
    
    def list_all_people(self) -> List[str]:
        """列出所有人物姓名"""
        people_dir = self.base_path / "people"
        
        if not people_dir.exists():
            return []
        
        return [f.stem for f in people_dir.glob("*.md")]
    
    def add_person(self, name: str, data: Dict) -> bool:
        """
        添加人物档案
        
        Args:
            name: 姓名
            data: 人物数据
            
        Returns:
            是否成功
        """
        try:
            person_file = self.base_path / "people" / f"{name}.md"
            person_file.parent.mkdir(parents=True, exist_ok=True)
            
            content = self._generate_person_md(data)
            person_file.write_text(content, encoding="utf-8")
            
            return True
        except Exception as e:
            print(f"Error adding person: {e}")
            return False
    
    def _generate_person_md(self, data: Dict) -> str:
        """生成人物 Markdown 内容"""
        content = f"# {data.get('name', '')}\n\n"
        content += f"## 基本信息\n"
        content += f"- **姓名**: {data.get('name', '')}\n"
        content += f"- **现任职务**: {data.get('current_position', '')}\n"
        content += f"- **行政级别**: {data.get('level', '')}\n\n"
        
        content += "## 称谓规范\n"
        for key, value in data.get('addressing_rules', {}).items():
            content += f"- **{key}**: {value}\n"
        
        content += "\n## 履历\n"
        for item in data.get('career', []):
            content += f"- {item}\n"
        
        content += "\n## 分管领域\n"
        for item in data.get('responsibilities', []):
            content += f"- {item}\n"
        
        return content


# 全局知识库服务实例
knowledge_service = KnowledgeService()