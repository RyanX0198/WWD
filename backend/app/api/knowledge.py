"""
知识库 API 路由
"""
from fastapi import APIRouter, UploadFile, File, Query
from pydantic import BaseModel
from typing import List, Optional

from app.services.knowledge import knowledge_service
from app.services.vector_search import vector_search

router = APIRouter()


class PersonProfile(BaseModel):
    name: str
    current_position: str
    level: str
    addressing_rules: dict = {}
    career: List[dict] = []
    responsibilities: List[str] = []


class PolicyDoc(BaseModel):
    title: str
    year: int
    key_points: List[str]
    content: str


@router.get("/people")
async def list_people():
    """获取人物列表"""
    people = knowledge_service.list_all_people()
    return {"people": people, "count": len(people)}


@router.get("/people/{name}")
async def get_person(name: str):
    """获取人物详情"""
    person = knowledge_service.get_person(name)
    if not person:
        return {"error": f"未找到人物: {name}"}
    return {"person": person}


@router.post("/people")
async def create_person(profile: PersonProfile):
    """创建人物档案"""
    success = knowledge_service.add_person(profile.name, profile.model_dump())
    if success:
        return {"status": "success", "message": f"已创建人物档案: {profile.name}"}
    return {"status": "error", "message": "创建失败"}


@router.get("/people/search")
async def search_people(query: str = Query(...), limit: int = 5):
    """搜索人物（支持语义搜索）"""
    # 先尝试向量搜索
    if vector_search.qdrant:
        results = await vector_search.search_people(query, limit)
        if results:
            return {"results": results, "count": len(results), "source": "vector"}
    
    # 回退到关键词搜索
    results = knowledge_service.search_people(query, limit)
    return {"results": results, "count": len(results), "source": "keyword"}


@router.get("/policies")
async def list_policies(year: Optional[int] = None):
    """获取政策列表"""
    from app.services.policy import policy_service
    policies = policy_service.list_policies(year)
    return {"policies": policies, "count": len(policies)}


@router.get("/policies/search")
async def search_policies(
    query: str = Query(...),
    year: Optional[int] = None,
    limit: int = 5
):
    """语义搜索政策文件"""
    from app.services.policy import policy_service
    results = await policy_service.search_policies(query, year, limit)
    return {"results": results, "count": len(results)}


@router.get("/policies/{doc_id}")
async def get_policy(doc_id: str, year: Optional[int] = None):
    """获取政策文件详情"""
    from app.services.policy import policy_service
    policy = policy_service.get_policy(doc_id, year)
    if not policy:
        return {"error": "未找到政策文件"}
    return {"policy": policy}


@router.post("/policies/upload")
async def upload_policy(file: UploadFile = File(...)):
    """上传政策文件"""
    from app.services.policy import policy_service
    
    try:
        content = await file.read()
        text = content.decode("utf-8")
        
        result = await policy_service.add_policy(
            filename=file.filename,
            content=text
        )
        
        return {
            "status": "success",
            "message": "上传成功",
            "data": result
        }
    except Exception as e:
        return {"status": "error", "message": f"上传失败: {str(e)}"}


@router.get("/search")
async def global_search(
    query: str = Query(...),
    collection: str = Query("all"),  # all, people, policies, templates
    limit: int = 5
):
    """
    全局语义搜索
    
    Args:
        query: 查询内容
        collection: 搜索范围
        limit: 返回数量
    """
    results = {}
    
    if collection in ["all", "people"]:
        results["people"] = await vector_search.search_people(query, limit)
    
    if collection in ["all", "policies"]:
        results["policies"] = await vector_search.search_policies(query, limit=limit)
    
    if collection in ["all", "templates"]:
        results["templates"] = await vector_search.search_templates(query, limit=limit)
    
    return {"query": query, "results": results}