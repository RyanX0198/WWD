"""
知识库 API 路由
"""
from fastapi import APIRouter, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional

from app.services.knowledge import knowledge_service

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
async def search_people(query: str, limit: int = 5):
    """搜索人物"""
    results = knowledge_service.search_people(query, limit)
    return {"results": results, "count": len(results)}


@router.get("/policies")
async def list_policies(year: Optional[int] = None):
    """获取政策列表"""
    # TODO: 实现政策列表查询
    return {"policies": [], "count": 0}


@router.post("/policies/upload")
async def upload_policy(file: UploadFile = File(...)):
    """上传政策文件"""
    # TODO: 实现政策文件上传和解析
    return {"status": "success", "filename": file.filename}