"""
数据资源与持久化基础设施包。
"""

from app.resource.db import get_connection, init_database, SCHEMA_SQL

__all__ = [
    "get_connection",
    "init_database",
    "SCHEMA_SQL",
]
