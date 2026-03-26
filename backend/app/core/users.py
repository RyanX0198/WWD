"""
用户数据存储
简化版：内存存储，生产环境应使用数据库
"""
from typing import Dict, Optional
from app.core.security import get_password_hash, verify_password


class User:
    """用户模型"""
    def __init__(self, id: str, username: str, email: str, hashed_password: str, is_active: bool = True):
        self.id = id
        self.username = username
        self.email = email
        self.hashed_password = hashed_password
        self.is_active = is_active


# 内存用户存储（生产环境应使用数据库）
_users: Dict[str, User] = {}

# 初始化默认用户（开发测试用）
def init_default_users():
    """初始化默认用户"""
    if not _users:
        # 创建默认管理员用户
        admin = User(
            id="1",
            username="admin",
            email="admin@govwriting.local",
            hashed_password=get_password_hash("admin123"),
            is_active=True
        )
        _users[admin.username] = admin
        
        # 创建测试用户
        test_user = User(
            id="2",
            username="test",
            email="test@govwriting.local",
            hashed_password=get_password_hash("test123"),
            is_active=True
        )
        _users[test_user.username] = test_user


def get_user_by_username(username: str) -> Optional[User]:
    """通过用户名获取用户"""
    return _users.get(username)


def get_user_by_id(user_id: str) -> Optional[User]:
    """通过 ID 获取用户"""
    for user in _users.values():
        if user.id == user_id:
            return user
    return None


def authenticate_user(username: str, password: str) -> Optional[User]:
    """
    认证用户
    
    Args:
        username: 用户名
        password: 明文密码
        
    Returns:
        认证成功返回 User 对象，失败返回 None
    """
    user = get_user_by_username(username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_user(username: str, email: str, password: str) -> User:
    """
    创建新用户
    
    Args:
        username: 用户名
        email: 邮箱
        password: 明文密码
        
    Returns:
        新创建的 User 对象
    """
    import uuid
    
    if username in _users:
        raise ValueError(f"用户名 '{username}' 已存在")
    
    user = User(
        id=str(uuid.uuid4()),
        username=username,
        email=email,
        hashed_password=get_password_hash(password),
        is_active=True
    )
    
    _users[username] = user
    return user


# 初始化默认用户
init_default_users()