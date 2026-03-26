"""
机构管理服务
处理机构的 CRUD 和层级关系
"""
import json
import uuid
from datetime import datetime
from typing import List, Optional, Dict
from pathlib import Path

from app.models.organization import Organization, OrganizationCreate, OrganizationUpdate, OrganizationTreeNode
from app.core.config import settings


class OrganizationService:
    """机构服务"""
    
    def __init__(self):
        self.data_dir = Path(settings.KNOWLEDGE_BASE_PATH) / "organizations"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.orgs_file = self.data_dir / "organizations.json"
        self._cache: Dict[str, Organization] = {}
        self._load_data()
    
    def _load_data(self):
        """从文件加载机构数据"""
        if self.orgs_file.exists():
            try:
                with open(self.orgs_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for org_data in data:
                        org = Organization(**org_data)
                        self._cache[org.id] = org
            except Exception as e:
                print(f"加载机构数据失败: {e}")
    
    def _save_data(self):
        """保存机构数据到文件"""
        try:
            data = [org.model_dump() for org in self._cache.values()]
            with open(self.orgs_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        except Exception as e:
            print(f"保存机构数据失败: {e}")
    
    def _calculate_path(self, org_id: str, parent_id: Optional[str]) -> str:
        """计算机构的层级路径"""
        if not parent_id:
            return f"/{org_id}/"
        
        parent = self._cache.get(parent_id)
        if not parent:
            return f"/{org_id}/"
        
        return f"{parent.path}{org_id}/"
    
    def _calculate_level(self, parent_id: Optional[str]) -> int:
        """计算机构的层级"""
        if not parent_id:
            return 1
        
        parent = self._cache.get(parent_id)
        if not parent:
            return 1
        
        return parent.level + 1
    
    # ========== CRUD 操作 ==========
    
    def create(self, data: OrganizationCreate) -> Organization:
        """创建机构"""
        org_id = str(uuid.uuid4())
        
        # 检查编码是否重复
        for org in self._cache.values():
            if org.code == data.code:
                raise ValueError(f"机构代码 '{data.code}' 已存在")
        
        # 检查上级机构是否存在
        if data.parent_id and data.parent_id not in self._cache:
            raise ValueError(f"上级机构 '{data.parent_id}' 不存在")
        
        # 计算层级和路径
        level = self._calculate_level(data.parent_id)
        path = self._calculate_path(org_id, data.parent_id)
        
        org = Organization(
            id=org_id,
            name=data.name,
            short_name=data.short_name,
            code=data.code,
            parent_id=data.parent_id,
            level=level,
            path=path,
            org_type=data.org_type,
            address=data.address,
            phone=data.phone,
            website=data.website,
            responsibilities=data.responsibilities,
            tags=data.tags,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self._cache[org_id] = org
        self._save_data()
        
        return org
    
    def get(self, org_id: str) -> Optional[Organization]:
        """获取机构"""
        return self._cache.get(org_id)
    
    def get_by_code(self, code: str) -> Optional[Organization]:
        """通过代码获取机构"""
        for org in self._cache.values():
            if org.code == code:
                return org
        return None
    
    def list(
        self,
        org_type: Optional[str] = None,
        level: Optional[int] = None,
        parent_id: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[Organization]:
        """获取机构列表"""
        result = list(self._cache.values())
        
        if org_type:
            result = [o for o in result if o.org_type == org_type]
        
        if level is not None:
            result = [o for o in result if o.level == level]
        
        if parent_id is not None:
            result = [o for o in result if o.parent_id == parent_id]
        
        if is_active is not None:
            result = [o for o in result if o.is_active == is_active]
        
        # 按层级和名称排序
        result.sort(key=lambda x: (x.level, x.name))
        
        return result
    
    def update(self, org_id: str, data: OrganizationUpdate) -> Optional[Organization]:
        """更新机构"""
        org = self._cache.get(org_id)
        if not org:
            return None
        
        # 如果更改了上级机构，需要重新计算层级和路径
        if data.parent_id is not None and data.parent_id != org.parent_id:
            if data.parent_id and data.parent_id not in self._cache:
                raise ValueError(f"上级机构 '{data.parent_id}' 不存在")
            
            # 防止循环引用
            if data.parent_id == org_id:
                raise ValueError("不能将机构的上级设置为自己")
            
            org.parent_id = data.parent_id
            org.level = self._calculate_level(data.parent_id)
            org.path = self._calculate_path(org_id, data.parent_id)
            
            # 更新所有子机构的层级和路径
            self._update_children_path(org_id, org.path)
        
        # 更新其他字段
        update_fields = [
            'name', 'short_name', 'code', 'org_type',
            'address', 'phone', 'website', 'responsibilities',
            'is_active', 'tags'
        ]
        
        for field in update_fields:
            value = getattr(data, field)
            if value is not None:
                setattr(org, field, value)
        
        org.updated_at = datetime.utcnow()
        
        self._save_data()
        return org
    
    def _update_children_path(self, parent_id: str, parent_path: str):
        """递归更新子机构的路径"""
        children = [o for o in self._cache.values() if o.parent_id == parent_id]
        
        for child in children:
            child.path = f"{parent_path}{child.id}/"
            child.level = self._calculate_level(parent_id)
            self._update_children_path(child.id, child.path)
    
    def delete(self, org_id: str) -> bool:
        """删除机构"""
        if org_id not in self._cache:
            return False
        
        # 检查是否有子机构
        children = [o for o in self._cache.values() if o.parent_id == org_id]
        if children:
            raise ValueError(f"该机构下有 {len(children)} 个子机构，无法删除")
        
        del self._cache[org_id]
        self._save_data()
        return True
    
    # ========== 层级关系 ==========
    
    def get_tree(self, root_id: Optional[str] = None) -> List[OrganizationTreeNode]:
        """获取机构树"""
        # 获取根级机构或指定机构的子机构
        if root_id:
            root = self._cache.get(root_id)
            if not root:
                return []
            root_orgs = [o for o in self._cache.values() if o.parent_id == root_id]
        else:
            root_orgs = [o for o in self._cache.values() if o.parent_id is None]
        
        # 构建树
        def build_tree(org: Organization) -> OrganizationTreeNode:
            children = [o for o in self._cache.values() if o.parent_id == org.id]
            return OrganizationTreeNode(
                id=org.id,
                name=org.name,
                short_name=org.short_name,
                level=org.level,
                org_type=org.org_type,
                is_active=org.is_active,
                children=[build_tree(child) for child in children]
            )
        
        return [build_tree(org) for org in root_orgs]
    
    def get_ancestors(self, org_id: str) -> List[Organization]:
        """获取机构的所有上级机构"""
        result = []
        org = self._cache.get(org_id)
        
        while org and org.parent_id:
            parent = self._cache.get(org.parent_id)
            if parent:
                result.append(parent)
                org = parent
            else:
                break
        
        # 反转，从根到当前
        result.reverse()
        return result
    
    def get_descendants(self, org_id: str) -> List[Organization]:
        """获取机构的所有下级机构"""
        result = []
        org = self._cache.get(org_id)
        
        if not org:
            return result
        
        def collect_children(parent_id: str):
            children = [o for o in self._cache.values() if o.parent_id == parent_id]
            for child in children:
                result.append(child)
                collect_children(child.id)
        
        collect_children(org_id)
        return result
    
    def get_siblings(self, org_id: str) -> List[Organization]:
        """获取同级机构"""
        org = self._cache.get(org_id)
        if not org:
            return []
        
        return [
            o for o in self._cache.values()
            if o.parent_id == org.parent_id and o.id != org_id
        ]


# 全局服务实例
org_service = OrganizationService()