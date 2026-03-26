"""
数据库初始化脚本
"""
import logging

from app.db.models import db

logger = logging.getLogger(__name__)


def init_database():
    """初始化数据库（创建所有表）"""
    try:
        db.create_tables()
        logger.info("数据库表创建成功")
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        raise


if __name__ == "__main__":
    # 直接运行此脚本初始化数据库
    print("正在初始化数据库...")
    init_database()
    print("数据库初始化完成！")