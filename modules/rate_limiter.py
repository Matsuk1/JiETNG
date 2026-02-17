"""
请求频率限制模块
用于限制用户短时间内重复发送相同请求
"""
import time
import threading
import logging

logger = logging.getLogger(__name__)


# ==================== 用户请求频率限制 ====================

# 用户请求频率限制配置
user_request_tracking = {}  # {user_id: {task_type: [timestamp1, timestamp2, ...]}}
user_request_lock = threading.Lock()
REQUEST_LIMIT_WINDOW = 20  # 时间窗口
MAX_SAME_REQUESTS = 2  # 同一时间窗口内允许的最大相同请求数


def check_rate_limit(user_id: str, task_type: str) -> bool:
    """
    检查用户请求是否超过频率限制

    Args:
        user_id: 用户ID
        task_type: 任务类型（如 'maimai_update', 'b50' 等）

    Returns:
        bool: True 表示超过限制（应该拒绝），False 表示可以继续
    """
    current_time = time.time()

    with user_request_lock:
        # 初始化用户追踪
        if user_id not in user_request_tracking:
            user_request_tracking[user_id] = {}

        if task_type not in user_request_tracking[user_id]:
            user_request_tracking[user_id][task_type] = []

        # 清理过期的请求记录
        user_request_tracking[user_id][task_type] = [
            ts for ts in user_request_tracking[user_id][task_type]
            if current_time - ts < REQUEST_LIMIT_WINDOW
        ]

        # 检查是否超过限制
        if len(user_request_tracking[user_id][task_type]) >= MAX_SAME_REQUESTS:
            logger.warning(f"[RateLimit] ⚠ Limit exceeded: user_id={user_id}, task_type={task_type}")
            return True  # 超过限制

        # 记录本次请求
        user_request_tracking[user_id][task_type].append(current_time)
        return False  # 未超过限制
