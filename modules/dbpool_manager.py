"""
数据库连接池模块
使用连接池复用数据库连接，避免频繁创建/关闭连接
"""
import os

import pymysql
from dbutils.pooled_db import PooledDB
from modules.config_loader import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME

# 创建连接池
_pool = None


def _env_int(name: str, default: int) -> int:
    try:
        return max(1, int(os.getenv(name, default)))
    except (TypeError, ValueError):
        return default

def get_pool():
    """获取数据库连接池（优化后配置）"""
    global _pool
    if _pool is None:
        maxconnections = _env_int("JIETNG_DB_MAX_CONNECTIONS", 20)
        maxcached = min(_env_int("JIETNG_DB_MAX_CACHED", 8), maxconnections)
        mincached = min(_env_int("JIETNG_DB_MIN_CACHED", 2), maxcached)

        _pool = PooledDB(
            creator=pymysql,
            maxconnections=maxconnections,  # 最大连接数
            mincached=mincached,            # 初始化时至少创建的空闲连接
            maxcached=maxcached,            # 连接池中最多闲置的连接
            maxshared=0,                    # PyMySQL 连接不跨线程共享
            blocking=True,          # 连接池满时等待
            ping=4,                 # 查询前检查有效性，避免每次取连接都 ping
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            charset="utf8mb4"
        )
    return _pool

def get_connection():
    """从连接池获取一个连接"""
    pool = get_pool()
    return pool.connection()
