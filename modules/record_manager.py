"""
成绩记录管理模块

提供数据库操作、Rating计算、成绩数据处理等功能
"""

import logging
import re
from typing import List, Dict, Any, Optional
from modules.config_loader import (
    MAIMAI_VERSION,
    read_dxdata
)
from modules.user_db import get_user_field
from modules.dbpool_manager import get_connection

logger = logging.getLogger(__name__)

def get_single_ra(level: float, score: float, ap_clear: bool = False, recent_type: bool = False) -> int:
    """
    计算单曲Rating值

    根据谱面定数和达成率计算Rating值,日服AP有额外加成

    Args:
        level: 谱面定数 (如 14.5)
        score: 达成率 (如 100.5000)
        ap_clear: 是否为 AP/APP
        recent_type: 是否为 b40 计算方案

    Returns:
        计算得到的Rating整数值
    """
    if recent_type:
        return get_single_ra_recent(level, score)

    # Rating系数映射表
    if score >= 100.5000:
        ra_kake = 0.224
    elif score >= 100.4999:
        ra_kake = 0.222
    elif score >= 100.0000:
        ra_kake = 0.216
    elif score >= 99.9999:
        ra_kake = 0.214
    elif score >= 99.5000:
        ra_kake = 0.211
    elif score >= 99.0000:
        ra_kake = 0.208
    elif score >= 98.9999:
        ra_kake = 0.206
    elif score >= 98.0000:
        ra_kake = 0.203
    elif score >= 97.0000:
        ra_kake = 0.200
    elif score >= 96.9999:
        ra_kake = 0.176
    elif score >= 94.0000:
        ra_kake = 0.168
    elif score >= 90.0000:
        ra_kake = 0.152
    elif score >= 80.0000:
        ra_kake = 0.136
    elif score >= 79.9999:
        ra_kake = 0.128
    elif score >= 75.0000:
        ra_kake = 0.120
    elif score >= 70.0000:
        ra_kake = 0.112
    elif score >= 60.0000:
        ra_kake = 0.096
    elif score >= 50.0000:
        ra_kake = 0.080
    elif score >= 40.0000:
        ra_kake = 0.064
    elif score >= 30.0000:
        ra_kake = 0.048
    elif score >= 20.0000:
        ra_kake = 0.032
    elif score >= 10.0000:
        ra_kake = 0.016
    else:
        ra_kake = 0

    # 计算基础Rating
    if score <= 100.5:
        ra = int(level * score * ra_kake)
    else:
        ra = int(level * 100.5 * ra_kake)

    # AP加成
    if ap_clear:
        ra += 1

    return ra

def get_single_ra_recent(level: float, score: float) -> int:
    """
    计算旧版本单曲Rating值

    根据谱面定数和达成率计算Rating值

    Args:
        level: 谱面定数 (如 14.5)
        score: 达成率 (如 100.5000)

    Returns:
        计算得到的Rating整数值
    """
    # Rating 系数映射表
    if score >= 100.5000:
        ra_kake = 0.14
    elif score >= 100.0000:
        ra_kake = 0.135
    elif score >= 99.5000:
        ra_kake = 0.132
    elif score >= 99.0000:
        ra_kake = 0.13
    elif score >= 98.0000:
        ra_kake = 0.127
    elif score >= 97.0000:
        ra_kake = 0.125
    elif score >= 94.0000:
        ra_kake = 0.105
    elif score >= 90.0000:
        ra_kake = 0.095
    elif score >= 80.0000:
        ra_kake = 0.085
    elif score >= 75.0000:
        ra_kake = 0.075
    elif score >= 70.0000:
        ra_kake = 0.07
    elif score >= 60.0000:
        ra_kake = 0.06
    elif score >= 50.0000:
        ra_kake = 0.05
    elif score >= 40.0000:
        ra_kake = 0.04
    elif score >= 30.0000:
        ra_kake = 0.03
    elif score >= 20.0000:
        ra_kake = 0.02
    elif score >= 10.0000:
        ra_kake = 0.01
    else:
        ra_kake = 0

    if score <= 100.5:
        ra = int(level * score * ra_kake)
    else:
        ra = int(level * 100.5 * ra_kake)

    return ra

def get_ideal_score(score: float) -> float:
    if 99.0000 <= score < 99.5000:
        return 99.5000, "ssp"
    elif 99.5000 <= score < 100.0000:
        return 100.0000, "sss"
    elif 100.0000 <= score < 100.5000:
        return 100.5000, "sssp"
    elif 100.5000 <= score <= 101.0000:
        return 101.0000, "sssp"
    else:
        return score, None

def parse_dx_score(dx_score_str):
    """解析 dx_score 字符串 (如 '613 / 666') 为浮点数"""
    try:
        match = re.match(r'^\s*(\d+)\s*/\s*(\d+)\s*$', str(dx_score_str))
        if match:
            numerator = int(match.group(1))
            denominator = int(match.group(2))
            if denominator == 0:
                return 0.0
            return numerator / denominator
        return float(dx_score_str)
    except (ValueError, TypeError):
        return 0.0

def calc_dx_star(dx_percentage):
    star_num = 0
    if 0 <= dx_percentage < 0.85:
        star_num = 0
    elif 0.85 <= dx_percentage < 0.9:
        star_num = 1
    elif 0.9 <= dx_percentage < 0.93:
        star_num = 2
    elif 0.93 <= dx_percentage < 0.95:
        star_num = 3
    elif 0.95 <= dx_percentage < 0.97:
        star_num = 4
    elif 0.97 <= dx_percentage <= 1:
        star_num = 5

    return star_num

def read_record(user_id: str, recent: bool = False, recent_type: bool = False) -> List[Dict[str, Any]]:
    """
    从数据库读取用户成绩记录

    Args:
        user_id: 用户ID
        recent: 是否读取最近记录 (False=Best记录, True=Recent记录)

    Returns:
        成绩记录列表,每条记录为字典,包含详细信息
    """
    table = "recent_records" if recent else "best_records"
    logger = logging.getLogger(__name__)
    logger.info(f"[Record] → Reading records: table={table}, user_id={user_id}")

    conn = get_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute(f"SELECT * FROM {table} WHERE user_id = %s", (user_id,))
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]

        records = []
        for row in rows:
            item = dict(zip(columns, row))
            item.pop("id", None)
            item.pop("user_id", None)
            records.append(item)

        return get_detailed_info(records, get_user_field(user_id, 'version', "jp"), recent_type)

    finally:
        conn.close()

def write_record(user_id, record_json, recent=False):
    table = "recent_records" if recent else "best_records"
    logger.info(f"[Record] → Writing records: table={table}, user_id={user_id}")

    conn = get_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute(f"DELETE FROM {table} WHERE user_id = %s", (user_id,))

            sql = f"""
            INSERT INTO {table} (
                user_id, name, difficulty, type, score, dx_score,
                score_icon, combo_icon, sync_icon
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            # 优化：批量插入数据，减少数据库往返次数
            batch_data = [
                (
                    user_id,
                    song.get("name"),
                    song.get("difficulty"),
                    song.get("type"),
                    song.get("score"),
                    song.get("dx_score"),
                    song.get("score_icon"),
                    song.get("combo_icon"),
                    song.get("sync_icon"),
                )
                for song in record_json
            ]

            if batch_data:
                cursor.executemany(sql, batch_data)

        conn.commit()
    finally:
        conn.close()

def delete_record(user_id, recent=False):
    table = "recent_records" if recent else "best_records"
    logger.info(f"[Record] → Deleting records: table={table}, user_id={user_id}")

    conn = get_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute(f"DELETE FROM {table} WHERE user_id = %s", (user_id,))
        conn.commit()
    finally:
        conn.close()

def filter_highest_achievement(data: list) -> list:
    result = {}
    for entry in data:
        key = (entry.get("name"), entry.get("difficulty"), entry.get("type"))
        if key not in result or float(entry.get("score", "0")[:-1]) > float(result[key].get("score", "0")[:-1]):
            result[key] = entry
    return list(result.values())

def get_detailed_info(song_record, ver="jp", recent_type=False):
    songs, _ = read_dxdata(ver)

    # 构建哈希表加速查找 O(1)
    song_map = {}
    for song in songs:
        key = (song['title'], song['type'])
        if key not in song_map:
            song_map[key] = song

    for record in song_record:
        found = False
        key = (record['name'], record['type'])

        if key in song_map:
            song = song_map[key]
            for sheet in song['sheets']:
                if record['difficulty'] == sheet['difficulty']:
                    found = True
                    record['internalLevelValue'] = sheet['internalLevelValue']
                    record['new_song'] = True if song['version'] in MAIMAI_VERSION[ver] else False
                    record['version'] = song['version']
                    ap_clear = "ap" in record['combo_icon']
                    record['ra'] = get_single_ra(float(record['internalLevelValue']), float(record['score'][:-1]), ap_clear, recent_type)
                    record['cover_url'] = song['cover_url']
                    record['cover_name'] = song['cover_name']
                    record['dx_percentage'] = parse_dx_score(record['dx_score'])
                    record['dx_star'] = calc_dx_star(record['dx_percentage'])
                    break

        if not found:
            record['internalLevelValue'] = 0
            record['new_song'] = True
            record['version'] = "UNKNOWN"
            record['ra'] = 0
            record['cover_url'] = None
            record['cover_name'] = "UNKNOWN"

    return song_record
