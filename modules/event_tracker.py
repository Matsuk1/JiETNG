"""
事件追踪与业务指标聚合模块

记录业务事件（webhook 调用、图片生成、绑定、同步任务等），
并提供 DAU/WAU/MAU 等指标聚合查询。
"""
import json
import logging
import queue
import threading
import time
from datetime import timedelta

from modules.dbpool_manager import get_connection

# events 表保留天数（超过后由后台任务清理）
EVENTS_RETENTION_DAYS = 90

# 批量 flush 参数
_BATCH_MAX_SIZE = 100
_BATCH_MAX_WAIT = 1.0  # 秒

# get_business_stats 结果 TTL 缓存（秒）
_STATS_CACHE_TTL = 30

logger = logging.getLogger(__name__)

_init_lock = threading.Lock()
_initialized = False

# 后台事件写入队列：避免在 webhook / API 热路径上阻塞 DB
_event_queue: "queue.Queue[tuple]" = queue.Queue(maxsize=10000)
_worker_started = False
_worker_lock = threading.Lock()


def _flush_batch(batch):
    """批量写入一组事件；失败时记录日志，行丢弃。"""
    if not batch:
        return
    # 元组顺序对齐 INSERT 列：(user_id, event_type, metadata)
    rows = [(uid, et, mj) for (et, uid, mj) in batch]
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.executemany(
            "INSERT INTO events (user_id, event_type, metadata) VALUES (%s, %s, %s)",
            rows,
        )
        conn.commit()
    except Exception as e:
        msg = str(e).lower()
        # 表尚未初始化时短暂退避，不丢事件
        if "doesn't exist" in msg or "no such table" in msg or "1146" in msg:
            logger.warning(f"[EventTracker] ⚠ events table not ready, requeue {len(batch)} events")
            for item in batch:
                try:
                    _event_queue.put_nowait(item)
                except queue.Full:
                    break
            time.sleep(2.0)
        else:
            logger.error(f"[EventTracker] ✗ batch insert({len(batch)}) failed: {e}")
    finally:
        if cursor:
            try: cursor.close()
            except Exception: pass
        if conn:
            try: conn.close()
            except Exception: pass


def _event_worker():
    """后台线程：从队列取事件，按 batch 合并后写入 DB。"""
    while True:
        try:
            first = _event_queue.get()
        except Exception:
            continue
        batch = [first]
        deadline = time.monotonic() + _BATCH_MAX_WAIT
        while len(batch) < _BATCH_MAX_SIZE:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            try:
                batch.append(_event_queue.get(timeout=remaining))
            except queue.Empty:
                break
        try:
            _flush_batch(batch)
        finally:
            for _ in batch:
                _event_queue.task_done()


def _purge_loop():
    """每 24 小时清理一次历史 events。"""
    while True:
        try:
            purge_old_events()
        except Exception as e:
            logger.error(f"[EventTracker] ✗ purge loop error: {e}")
        time.sleep(24 * 3600)


def _ensure_worker():
    global _worker_started
    if _worker_started:
        return
    with _worker_lock:
        if _worker_started:
            return
        t = threading.Thread(target=_event_worker, name="event-tracker-worker", daemon=True)
        t.start()
        _worker_started = True


def init_events_table():
    """初始化 events 表（启动时调用）"""
    global _initialized
    with _init_lock:
        if _initialized:
            return
        conn = None
        cursor = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    user_id VARCHAR(64) NULL,
                    event_type VARCHAR(32) NOT NULL,
                    metadata JSON NULL,
                    ts DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_ts (ts),
                    INDEX idx_event_ts (event_type, ts),
                    INDEX idx_user_ts (user_id, ts)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            conn.commit()
            _initialized = True
            logger.info("[EventTracker] ✓ events table ready")
            # 启动每日清理线程
            threading.Thread(target=_purge_loop, name="event-tracker-purge", daemon=True).start()
        except Exception as e:
            logger.error(f"[EventTracker] ✗ init table failed: {e}")
        finally:
            if cursor:
                try: cursor.close()
                except Exception: pass
            if conn:
                try: conn.close()
                except Exception: pass


def purge_old_events(retention_days: int = EVENTS_RETENTION_DAYS) -> int:
    """删除超过保留期的 events 行，返回删除行数。分批删除避免长事务。"""
    total = 0
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        while True:
            cursor.execute(
                "DELETE FROM events WHERE ts < DATE_SUB(NOW(), INTERVAL %s DAY) LIMIT 5000",
                (retention_days,),
            )
            conn.commit()
            affected = cursor.rowcount or 0
            total += affected
            if affected < 5000:
                break
        if total:
            logger.info(f"[EventTracker] ✓ purged {total} old events (> {retention_days}d)")
    except Exception as e:
        logger.error(f"[EventTracker] ✗ purge_old_events failed: {e}")
    finally:
        if cursor:
            try: cursor.close()
            except Exception: pass
        if conn:
            try: conn.close()
            except Exception: pass
    return total


def track_event(event_type: str, user_id: str | None = None, metadata: dict | None = None):
    """记录一个业务事件（非阻塞）。队列满或序列化失败时静默丢弃。"""
    try:
        _ensure_worker()
        metadata_json = json.dumps(metadata, ensure_ascii=False) if metadata else None
        _event_queue.put_nowait((event_type, user_id, metadata_json))
    except queue.Full:
        logger.warning(f"[EventTracker] ⚠ queue full, dropping event: {event_type}")
    except Exception as e:
        logger.error(f"[EventTracker] ✗ track_event({event_type}) enqueue failed: {e}")


def _scalar(cursor, sql, args=()):
    cursor.execute(sql, args)
    row = cursor.fetchone()
    return row[0] if row else 0


_stats_cache_lock = threading.Lock()
_stats_cache = {'ts': 0.0, 'data': None}


def get_business_stats(force_refresh: bool = False) -> dict:
    """带 TTL 缓存的业务指标查询（默认 30s）。force_refresh=True 跳过缓存。"""
    now = time.monotonic()
    if not force_refresh:
        cached = _stats_cache['data']
        if cached is not None and (now - _stats_cache['ts']) < _STATS_CACHE_TTL:
            return cached
    data = _compute_business_stats()
    with _stats_cache_lock:
        _stats_cache['ts'] = time.monotonic()
        _stats_cache['data'] = data
    return data


def _compute_business_stats() -> dict:
    """
    聚合返回业务指标：
      dau / wau / mau / stickiness
      today_new_users / today_image_calls / today_webhook_msgs
      today_bindings / today_unbinds / today_sync_total / today_sync_success / sync_success_rate
      image_command_breakdown
      dau_30d  (日期 → DAU，近 30 天)
      hourly_today  (0-23 小时 → 调用量)
    """
    out = {
        'dau': 0, 'wau': 0, 'mau': 0, 'stickiness': 0.0,
        'today_new_users': 0, 'today_image_calls': 0, 'today_webhook_msgs': 0,
        'today_bindings': 0, 'today_unbinds': 0,
        'today_sync_total': 0, 'today_sync_success': 0, 'sync_success_rate': 0.0,
        'image_command_breakdown': [],
        'dau_30d': [],
        'hourly_today': [0] * 24,
    }
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # DAU / WAU / MAU（active = 产生任意事件的 distinct user_id）
        out['dau'] = _scalar(cursor,
            "SELECT COUNT(DISTINCT user_id) FROM events WHERE user_id IS NOT NULL AND ts >= CURDATE()")
        out['wau'] = _scalar(cursor,
            "SELECT COUNT(DISTINCT user_id) FROM events WHERE user_id IS NOT NULL AND ts >= DATE_SUB(CURDATE(), INTERVAL 6 DAY)")
        out['mau'] = _scalar(cursor,
            "SELECT COUNT(DISTINCT user_id) FROM events WHERE user_id IS NOT NULL AND ts >= DATE_SUB(CURDATE(), INTERVAL 29 DAY)")
        if out['mau']:
            out['stickiness'] = round(out['dau'] / out['mau'] * 100, 1)

        # 今日分事件统计
        # today_new_users：今日首次有 user_bind 事件、且该 user_id 历史上从未 bind 过的 distinct 用户数
        out['today_new_users'] = _scalar(cursor, """
            SELECT COUNT(*) FROM (
                SELECT user_id, MIN(ts) AS first_bind
                FROM events
                WHERE event_type='user_bind' AND user_id IS NOT NULL
                GROUP BY user_id
                HAVING first_bind >= CURDATE()
            ) t
        """)
        out['today_image_calls'] = _scalar(cursor,
            "SELECT COUNT(*) FROM events WHERE event_type='image_gen' AND ts >= CURDATE()")
        out['today_webhook_msgs'] = _scalar(cursor,
            "SELECT COUNT(*) FROM events WHERE event_type='line_webhook' AND ts >= CURDATE()")
        # today_bindings：今日全部绑定动作（首绑 + 重绑），按 distinct user_id 去重
        out['today_bindings'] = _scalar(cursor,
            "SELECT COUNT(DISTINCT user_id) FROM events "
            "WHERE event_type IN ('user_bind','user_rebind') AND user_id IS NOT NULL AND ts >= CURDATE()")
        out['today_unbinds'] = _scalar(cursor,
            "SELECT COUNT(DISTINCT user_id) FROM events "
            "WHERE event_type='user_unbind' AND user_id IS NOT NULL AND ts >= CURDATE()")
        out['today_sync_total'] = _scalar(cursor,
            "SELECT COUNT(*) FROM events WHERE event_type='sync_task' AND ts >= CURDATE()")
        out['today_sync_success'] = _scalar(cursor,
            "SELECT COUNT(*) FROM events WHERE event_type='sync_task' AND ts >= CURDATE() "
            "AND JSON_UNQUOTE(JSON_EXTRACT(metadata, '$.success')) = 'true'")
        if out['today_sync_total']:
            out['sync_success_rate'] = round(out['today_sync_success'] / out['today_sync_total'] * 100, 1)

        # 图片命令分布（今日）
        cursor.execute("""
            SELECT JSON_UNQUOTE(JSON_EXTRACT(metadata, '$.command')) AS cmd, COUNT(*) AS cnt
            FROM events
            WHERE event_type='image_gen' AND ts >= CURDATE()
            GROUP BY cmd
            ORDER BY cnt DESC
        """)
        out['image_command_breakdown'] = [
            {'command': (r[0] or 'unknown'), 'count': r[1]} for r in cursor.fetchall()
        ]

        # DAU 近 30 天（按日聚合，日期全部由 DB 侧生成以避免进程与 DB 时区错位）
        cursor.execute("""
            SELECT DATE(ts) AS d, COUNT(DISTINCT user_id) AS c
            FROM events
            WHERE user_id IS NOT NULL AND ts >= DATE_SUB(CURDATE(), INTERVAL 29 DAY)
            GROUP BY d
            ORDER BY d
        """)
        by_date = {str(r[0]): r[1] for r in cursor.fetchall()}
        cursor.execute("SELECT CURDATE()")
        today = cursor.fetchone()[0]
        series = []
        for i in range(29, -1, -1):
            d = today - timedelta(days=i)
            series.append({'date': d.strftime('%m-%d'), 'dau': by_date.get(str(d), 0)})
        out['dau_30d'] = series

        # 今日小时分布（所有事件调用量）
        cursor.execute("""
            SELECT HOUR(ts) AS h, COUNT(*) AS c
            FROM events
            WHERE ts >= CURDATE()
            GROUP BY h
        """)
        hourly = [0] * 24
        for r in cursor.fetchall():
            hourly[int(r[0])] = r[1]
        out['hourly_today'] = hourly
    except Exception as e:
        logger.error(f"[EventTracker] ✗ get_business_stats failed: {e}")
    finally:
        if cursor:
            try: cursor.close()
            except Exception: pass
        if conn:
            try: conn.close()
            except Exception: pass

    return out
