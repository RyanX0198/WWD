"""
知识库 API 路由
"""
from fastapi import APIRouter, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()


class PersonProfile(BaseModel):
    name: str
    current_position: str
    level: str
    addressing_rules: dict
    career: List[dict]
    responsibilities: List[str]


class PolicyDoc(BaseModel):
    title: str
    year: int
    key_points: List[str]
    content: str


@router.get("/people")
async def list_people():
    """获取人物列表"""
    # TODO: 实现人物列表查询
    return {"people": []}


@router.get("/people/{name}")
async def get_person(name: str):
    """获取人物详情"""
    # TODO: 实现人物详情查询
    return {"person": None}


@router.post("/people")
async def create_person(profile: PersonProfile):
    """创建人物档案"""
    # TODO: 实现人物档案创建
    return {"status": "success", "id": "xxx"}


@router.get("/policies")
async def list_policies(year: Optional[int] = None):
    """获取政策列表"""
    # TODO: 实现政策列表查询
    return {"policies": []}


@router.post("/policies/upload")
async def upload_policy(file: UploadFile = File(...)):
    """上传政策文件"""
    # TODO: 实现政策文件上传和解析
    return {"status": "success", "filename": file.filename}