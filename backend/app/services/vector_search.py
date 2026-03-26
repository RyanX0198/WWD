"""
向量检索服务 - Qdrant
实现语义搜索和文档向量化
"""
import os
from typing import List, Dict, Optional
from pathlib import Path

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, 
    VectorParams, 
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue
)
from langchain_openai import OpenAIEmbeddings
from langchain_core.embeddings import Embeddings

from app.core.config import settings


class VectorSearchService:
    """向量检索服务"""
    
    # 集合名称
    COLLECTION_PEOPLE = "people_vectors"
    COLLECTION_POLICIES = "policies_vectors"
    COLLECTION_TEMPLATES = "templates_vectors"
    
    # 向量维度（OpenAI text-embedding-3-small 是 1536 维）
    VECTOR_SIZE = 1536
    
    def __init__(self):
        self.qdrant: Optional[QdrantClient] = None
        self.embeddings: Optional[Embeddings] = None
        self._init_service()
    
    def _init_service(self):
        """初始化服务"""
        try:
            # 连接 Qdrant
            self.qdrant = QdrantClient(
                host=settings.QDRANT_HOST,
                port=settings.QDRANT_PORT
            )
            
            # 初始化 embedding 模型
            # 优先使用国内模型，如果配置了对应的 embedding 接口
            if os.getenv("KIMI_API_KEY"):
                # Kimi 暂时没有独立的 embedding API，使用 OpenAI 兼容模式
                self.embeddings = OpenAIEmbeddings(
                    api_key=os.getenv("KIMI_API_KEY"),
                    base_url="https://api.moonshot.cn/v1",
                    model="text-embedding-3-small"
                )
            elif os.getenv("DASHSCOPE_API_KEY"):
                # 千问 embedding
                self.embeddings = OpenAIEmbeddings(
                    api_key=os.getenv("DASHSCOPE_API_KEY"),
                    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                    model="text-embedding-v3"
                )
            elif os.getenv("OPENAI_API_KEY"):
                self.embeddings = OpenAIEmbeddings(
                    api_key=os.getenv("OPENAI_API_KEY")
                )
            
            # 初始化集合
            self._init_collections()
            
        except Exception as e:
            print(f"Vector search init error: {e}")
            self.qdrant = None
    
    def _init_collections(self):
        """初始化向量集合"""
        if not self.qdrant:
            return
        
        collections = [
            self.COLLECTION_PEOPLE,
            self.COLLECTION_POLICIES,
            self.COLLECTION_TEMPLATES
        ]
        
        for collection in collections:
            try:
                # 检查集合是否存在
                self.qdrant.get_collection(collection)
            except Exception:
                # 创建新集合
                try:
                    self.qdrant.create_collection(
                        collection_name=collection,
                        vectors_config=VectorParams(
                            size=self.VECTOR_SIZE,
                            distance=Distance.COSINE
                        )
                    )
                    print(f"Created collection: {collection}")
                except Exception as e:
                    print(f"Create collection error: {e}")
    
    async def add_document(
        self,
        collection: str,
        doc_id: str,
        content: str,
        metadata: Dict = None
    ) -> bool:
        """
        添加文档到向量库
        
        Args:
            collection: 集合名称
            doc_id: 文档ID
            content: 文档内容
            metadata: 元数据
            
        Returns:
            是否成功
        """
        if not self.qdrant or not self.embeddings:
            return False
        
        try:
            # 生成向量
            vector = await self.embeddings.aembed_query(content)
            
            # 插入到 Qdrant
            self.qdrant.upsert(
                collection_name=collection,
                points=[
                    PointStruct(
                        id=doc_id,
                        vector=vector,
                        payload=metadata or {"content": content}
                    )
                ]
            )
            return True
        except Exception as e:
            print(f"Add document error: {e}")
            return False
    
    async def search(
        self,
        collection: str,
        query: str,
        limit: int = 5,
        filter_conditions: Dict = None
    ) -> List[Dict]:
        """
        语义搜索
        
        Args:
            collection: 集合名称
            query: 查询文本
            limit: 返回数量
            filter_conditions: 过滤条件
            
        Returns:
            搜索结果列表
        """
        if not self.qdrant or not self.embeddings:
            return []
        
        try:
            # 生成查询向量
            query_vector = await self.embeddings.aembed_query(query)
            
            # 构建过滤条件
            search_filter = None
            if filter_conditions:
                conditions = []
                for key, value in filter_conditions.items():
                    conditions.append(
                        FieldCondition(
                            key=key,
                            match=MatchValue(value=value)
                        )
                    )
                if conditions:
                    search_filter = Filter(must=conditions)
            
            # 执行搜索
            results = self.qdrant.search(
                collection_name=collection,
                query_vector=query_vector,
                limit=limit,
                query_filter=search_filter
            )
            
            # 格式化结果
            return [
                {
                    "id": hit.id,
                    "score": hit.score,
                    "payload": hit.payload
                }
                for hit in results
            ]
        except Exception as e:
            print(f"Search error: {e}")
            return []
    
    async def search_people(self, query: str, limit: int = 5) -> List[Dict]:
        """搜索人物"""
        return await self.search(
            self.COLLECTION_PEOPLE,
            query,
            limit
        )
    
    async def search_policies(self, query: str, year: int = None, limit: int = 5) -> List[Dict]:
        """搜索政策文件"""
        filter_conditions = {}
        if year:
            filter_conditions["year"] = year
        
        return await self.search(
            self.COLLECTION_POLICIES,
            query,
            limit,
            filter_conditions
        )
    
    async def search_templates(self, query: str, doc_type: str = None, limit: int = 5) -> List[Dict]:
        """搜索模板"""
        filter_conditions = {}
        if doc_type:
            filter_conditions["doc_type"] = doc_type
        
        return await self.search(
            self.COLLECTION_TEMPLATES,
            query,
            limit,
            filter_conditions
        )
    
    def delete_document(self, collection: str, doc_id: str) -> bool:
        """删除文档"""
        if not self.qdrant:
            return False
        
        try:
            self.qdrant.delete(
                collection_name=collection,
                points_selector=[doc_id]
            )
            return True
        except Exception as e:
            print(f"Delete document error: {e}")
            return False


# 全局向量检索服务实例
vector_search = VectorSearchService()