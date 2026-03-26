"""
机构管理 API 路由
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query

from app.models.organization import (
    Organization, OrganizationCreate, OrganizationUpdate, OrganizationTreeNode
)
from app.services.organization import org_service

router = APIRouter(prefix="/organizations", tags=["机构管理"])


@router.post("", response_model=Organization, summary="创建机构")
async def create_organization(data: OrganizationCreate):
    """
    创建新机构
    
    会自动计算层级和路径
    """
    try:
        org = org_service.create(data)
        return org
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=List[Organization], summary="获取机构列表")
async def list_organizations(
    org_type: Optional[str] = Query(None, description="机构类型筛选"),
    level: Optional[int] = Query(None, description="层级筛选"),
    parent_id: Optional[str] = Query(None, description="上级机构ID"),
    is_active: Optional[bool] = Query(None, description="是否有效")
):
    """
    获取机构列表，支持筛选
    """
    return org_service.list(
        org_type=org_type,
        level=level,
        parent_id=parent_id,
        is_active=is_active
    )


@router.get("/tree", response_model=List[OrganizationTreeNode], summary="获取机构树")
async def get_organization_tree(
    root_id: Optional[str] = Query(None, description="根机构ID，不传则获取全部")
):
    """
    获取机构层级树
    
    返回树形结构，包含所有子机构
    """
    return org_service.get_tree(root_id)


@router.get("/{org_id}", response_model=Organization, summary="获取机构详情")
async def get_organization(org_id: str):
    """
    获取单个机构详情
    """
    org = org_service.get(org_id)
    if not org:
        raise HTTPException(status_code=404, detail="机构不存在")
    return org


@router.get("/code/{code}", response_model=Organization, summary="通过代码获取机构")
async def get_organization_by_code(code: str):
    """
    通过机构代码查询
    """
    org = org_service.get_by_code(code)
    if not org:
        raise HTTPException(status_code=404, detail="机构不存在")
    return org


@router.put("/{org_id}", response_model=Organization, summary="更新机构")
async def update_organization(org_id: str, data: OrganizationUpdate):
    """
    更新机构信息
    
    如果更改上级机构，会自动更新层级和路径
    """
    try:
        org = org_service.update(org_id, data)
        if not org:
            raise HTTPException(status_code=404, detail="机构不存在")
        return org
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{org_id}", summary="删除机构")
async def delete_organization(org_id: str):
    """
    删除机构
    
    如果机构下有子机构，将无法删除
    """
    try:
        success = org_service.delete(org_id)
        if not success:
            raise HTTPException(status_code=404, detail="机构不存在")
        return {"status": "success", "message": "机构已删除"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ========== 层级关系接口 ==========

@router.get("/{org_id}/ancestors", response_model=List[Organization], summary="获取上级机构")
async def get_ancestors(org_id: str):
    """
    获取机构的所有上级机构（从根到父级）
    """
    org = org_service.get(org_id)
    if not org:
        raise HTTPException(status_code=404, detail="机构不存在")
    
    return org_service.get_ancestors(org_id)


@router.get("/{org_id}/descendants", response_model=List[Organization], summary="获取下级机构")
async def get_descendants(org_id: str):
    """
    获取机构的所有下级机构
    """
    org = org_service.get(org_id)
    if not org:
        raise HTTPException(status_code=404, detail="机构不存在")
    
    return org_service.get_descendants(org_id)


@router.get("/{org_id}/siblings", response_model=List[Organization], summary="获取同级机构")
async def get_siblings(org_id: str):
    """
    获取同级机构
    """
    org = org_service.get(org_id)
    if not org:
        raise HTTPException(status_code=404, detail="机构不存在")
    
    return org_service.get_siblings(org_id)