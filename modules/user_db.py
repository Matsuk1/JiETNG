"""
用户数据库模块

将用户数据从加密 JSON 文件迁移到 MySQL 存储
采用 user_id + JSON data 列方案，完全兼容现有 USERS 字典结构
"""

import json
import logging
from modules.dbpool_manager import get_connection

logger = logging.getLogger(__name__)


def init_users_table():
    """检查 users 表是否存在，不存在则尝试创建"""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        # 检查表是否存在
        cursor.execute("SHOW TABLES LIKE 'users'")
        if cursor.fetchone():
            logger.info("[UserDB] ✓ users table ready")
            return
        # 表不存在，创建
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id VARCHAR(64) PRIMARY KEY,
                data JSON NOT NULL,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        conn.commit()
        logger.info("[UserDB] ✓ users table created")
    except Exception as e:
        logger.error(f"[UserDB] ✗ Failed to init users table: {e}", exc_info=True)
    finally:
        if cursor:
            try: cursor.close()
            except Exception: pass
        if conn:
            try: conn.close()
            except Exception: pass


def load_all_users() -> dict:
    """从 DB 加载所有用户数据，返回 {user_id: data_dict} 格式"""
    users = {}
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, data FROM users")
        for row in cursor.fetchall():
            user_id = row[0]
            data = row[1]
            if isinstance(data, str):
                data = json.loads(data)
            users[user_id] = data
        logger.info(f"[UserDB] ✓ Loaded {len(users)} users from DB")
    except Exception as e:
        logger.error(f"[UserDB] ✗ Failed to load users: {e}", exc_info=True)
        raise
    finally:
        if cursor:
            try: cursor.close()
            except Exception: pass
        if conn:
            try: conn.close()
            except Exception: pass
    return users


def save_user(user_id: str, user_data: dict):
    """保存单个用户数据到 DB（INSERT or UPDATE）"""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        data_json = json.dumps(user_data, ensure_ascii=False, default=str)
        cursor.execute(
            "INSERT INTO users (user_id, data) VALUES (%s, %s) "
            "ON DUPLICATE KEY UPDATE data = %s, updated_at = CURRENT_TIMESTAMP",
            (user_id, data_json, data_json)
        )
        conn.commit()
    except Exception as e:
        logger.error(f"[UserDB] ✗ Failed to save user: user_id={user_id}, error={e}", exc_info=True)
    finally:
        if cursor:
            try: cursor.close()
            except Exception: pass
        if conn:
            try: conn.close()
            except Exception: pass


def delete_user_from_db(user_id: str):
    """从 DB 删除单个用户"""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
        conn.commit()
    except Exception as e:
        logger.error(f"[UserDB] ✗ Failed to delete user: user_id={user_id}, error={e}", exc_info=True)
    finally:
        if cursor:
            try: cursor.close()
            except Exception: pass
        if conn:
            try: conn.close()
            except Exception: pass


def increment_user_field(user_id: str, field: str, delta):
    """原子递增/递减用户的数值字段"""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET data = JSON_SET(data, %s, "
            "COALESCE(JSON_EXTRACT(data, %s), 0) + %s), "
            "updated_at = CURRENT_TIMESTAMP WHERE user_id = %s",
            (f'$.{field}', f'$.{field}', delta, user_id)
        )
        conn.commit()
    except Exception as e:
        logger.error(f"[UserDB] ✗ Failed to increment field: user_id={user_id}, field={field}, error={e}")
    finally:
        if cursor:
            try: cursor.close()
            except Exception: pass
        if conn:
            try: conn.close()
            except Exception: pass


def migrate_from_json(users_dict: dict) -> int:
    """将 JSON 用户数据批量导入 DB，返回导入数量"""
    if not users_dict:
        return 0
    conn = None
    cursor = None
    count = 0
    try:
        conn = get_connection()
        cursor = conn.cursor()
        for user_id, user_data in users_dict.items():
            data_json = json.dumps(user_data, ensure_ascii=False, default=str)
            cursor.execute(
                "INSERT INTO users (user_id, data) VALUES (%s, %s) "
                "ON DUPLICATE KEY UPDATE data = %s",
                (user_id, data_json, data_json)
            )
            count += 1
        conn.commit()
        logger.info(f"[UserDB] ✓ Migrated {count} users from JSON to DB")
    except Exception as e:
        logger.error(f"[UserDB] ✗ Migration failed: {e}", exc_info=True)
        if conn:
            try: conn.rollback()
            except Exception: pass
        raise
    finally:
        if cursor:
            try: cursor.close()
            except Exception: pass
        if conn:
            try: conn.close()
            except Exception: pass
    return count


def get_user(user_id: str) -> dict | None:
    """从 DB 查询单个用户的完整数据"""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT data FROM users WHERE user_id = %s", (user_id,))
        row = cursor.fetchone()
        if row is None:
            return None
        data = row[0]
        if isinstance(data, str):
            data = json.loads(data)
        return data
    except Exception as e:
        logger.error(f"[UserDB] ✗ Failed to get user: user_id={user_id}, error={e}")
        return None
    finally:
        if cursor:
            try: cursor.close()
            except Exception: pass
        if conn:
            try: conn.close()
            except Exception: pass


def user_exists(user_id: str) -> bool:
    """检查用户是否存在"""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM users WHERE user_id = %s", (user_id,))
        return cursor.fetchone() is not None
    except Exception:
        return False
    finally:
        if cursor:
            try: cursor.close()
            except Exception: pass
        if conn:
            try: conn.close()
            except Exception: pass


def get_user_field(user_id: str, field: str, default=None):
    """从 DB 查询用户的单个字段值（利用 MySQL JSON 提取）"""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT JSON_EXTRACT(data, %s) FROM users WHERE user_id = %s",
            (f'$.{field}', user_id)
        )
        row = cursor.fetchone()
        if row is None or row[0] is None:
            return default
        value = row[0]
        # JSON_EXTRACT 返回 JSON 格式字符串，需要解析
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except (json.JSONDecodeError, ValueError):
                pass
        return value
    except Exception as e:
        logger.error(f"[UserDB] ✗ Failed to get field: user_id={user_id}, field={field}, error={e}")
        return default
    finally:
        if cursor:
            try: cursor.close()
            except Exception: pass
        if conn:
            try: conn.close()
            except Exception: pass


def update_user_field(user_id: str, field: str, value):
    """更新用户的单个字段（利用 MySQL JSON_SET）"""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        value_json = json.dumps(value, ensure_ascii=False, default=str)
        cursor.execute(
            "UPDATE users SET data = JSON_SET(data, %s, CAST(%s AS JSON)), "
            "updated_at = CURRENT_TIMESTAMP WHERE user_id = %s",
            (f'$.{field}', value_json, user_id)
        )
        conn.commit()
    except Exception as e:
        logger.error(f"[UserDB] ✗ Failed to update field: user_id={user_id}, field={field}, error={e}")
    finally:
        if cursor:
            try: cursor.close()
            except Exception: pass
        if conn:
            try: conn.close()
            except Exception: pass


def remove_user_field(user_id: str, field: str):
    """删除用户的单个字段（利用 MySQL JSON_REMOVE）"""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET data = JSON_REMOVE(data, %s), "
            "updated_at = CURRENT_TIMESTAMP WHERE user_id = %s",
            (f'$.{field}', user_id)
        )
        conn.commit()
    except Exception as e:
        logger.error(f"[UserDB] ✗ Failed to remove field: user_id={user_id}, field={field}, error={e}")
    finally:
        if cursor:
            try: cursor.close()
            except Exception: pass
        if conn:
            try: conn.close()
            except Exception: pass


def get_all_user_ids() -> list:
    """获取所有用户 ID 列表"""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users")
        return [row[0] for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"[UserDB] ✗ Failed to get user IDs: {e}")
        return []
    finally:
        if cursor:
            try: cursor.close()
            except Exception: pass
        if conn:
            try: conn.close()
            except Exception: pass


def get_user_count() -> int:
    """获取 DB 中的用户数量"""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        return cursor.fetchone()[0]
    except Exception:
        return 0
    finally:
        if cursor:
            try: cursor.close()
            except Exception: pass
        if conn:
            try: conn.close()
            except Exception: pass
