"""
备份管理模块

提供数据库和配置文件的备份功能
"""

import os
import json
import subprocess
import tempfile
import logging
from datetime import datetime
from typing import Tuple, Optional
import pyzipper
from modules.config_loader import BACKUP_DIR

logger = logging.getLogger(__name__)


def create_backup(
    users_data: dict,
    config_data: dict,
    db_config: dict,
    backup_password: str,
) -> Tuple[bool, str, Optional[str]]:
    """
    创建系统备份

    Args:
        users_data: 用户数据字典（未加密）
        config_data: 配置数据字典
        db_config: 数据库配置 {"host", "user", "password", "database"}
        backup_password: 备份文件密码

    Returns:
        (成功标志, 消息, 备份文件路径)
    """
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            logger.info("[Backup] → Creating backup files...")

            # 1. 导出MySQL数据库
            sql_file = os.path.join(temp_dir, "maimai_records.sql")
            success, msg = _export_mysql_database(db_config, sql_file)
            if not success:
                logger.warning(f"[Backup] ⚠ Database export warning: {msg}")
                with open(sql_file, 'w') as f:
                    f.write(f"-- Database export failed: {msg}\n")

            # 2. 保存未加密的用户数据
            user_json_file = os.path.join(temp_dir, "user.json")
            with open(user_json_file, 'w', encoding='utf-8') as f:
                json.dump(users_data, f, ensure_ascii=False, indent=2)
            logger.info("[Backup] ✓ User data saved")

            # 3. 保存配置文件
            config_json_file = os.path.join(temp_dir, "config.json")
            with open(config_json_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            logger.info("[Backup] ✓ Config data saved")

            # 4. 创建加密的ZIP文件
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"backup_{timestamp}.zip"
            backup_path = os.path.join(BACKUP_DIR, backup_filename)

            # 创建加密压缩包
            with pyzipper.AESZipFile(backup_path, 'w', compression=pyzipper.ZIP_DEFLATED, encryption=pyzipper.WZ_AES) as zf:
                zf.setpassword(backup_password.encode('utf-8'))
                zf.write(sql_file, arcname="maimai_records.sql")
                zf.write(user_json_file, arcname="user.json")
                zf.write(config_json_file, arcname="config.json")
            password_note = "🔒 Password: config.admin_password (AES encrypted)"
            logger.info(f"[Backup] ✓ Encrypted backup created: {backup_path}")

            # 获取文件大小
            file_size = os.path.getsize(backup_path)
            size_mb = file_size / (1024 * 1024)

            return (
                True,
                f"✅ Backup created successfully\n"
                f"📦 File: {backup_filename}\n"
                f"📊 Size: {size_mb:.2f} MB\n"
                f"{password_note}\n"
                f"📁 Location: {BACKUP_DIR}/",
                backup_path
            )

    except Exception as e:
        logger.error(f"[Backup] ✗ Backup failed: error={e}", exc_info=True)
        return (
            False,
            f"❌ Backup failed\nError: {str(e)}",
            None
        )


def _export_mysql_database(db_config: dict, output_file: str) -> Tuple[bool, str]:
    """
    使用mysqldump导出MySQL数据库

    Args:
        db_config: 数据库配置
        output_file: 输出SQL文件路径

    Returns:
        (成功标志, 消息)
    """
    try:
        host = db_config.get('host', 'localhost')
        user = db_config.get('user', 'root')
        password = db_config.get('password', '')
        database = db_config.get('database', 'maimai_records')

        cmd = [
            'mysqldump',
            f'--host={host}',
            f'--user={user}',
        ]

        if password:
            cmd.append(f'--password={password}')

        cmd.extend([
            '--single-transaction',
            '--quick',
            '--lock-tables=false',
            database
        ])

        # 执行导出
        with open(output_file, 'w') as f:
            result = subprocess.run(
                cmd,
                stdout=f,
                stderr=subprocess.PIPE,
                text=True,
                timeout=300
            )

        if result.returncode != 0:
            error_msg = result.stderr.strip() if result.stderr else "Unknown error"
            logger.error(f"[Backup] ✗ mysqldump failed: {error_msg}")
            return False, f"mysqldump error: {error_msg}"

        logger.info(f"[Backup] ✓ Database exported: {database}")
        return True, "Database exported successfully"

    except FileNotFoundError:
        return False, "mysqldump command not found (MySQL client not installed)"
    except subprocess.TimeoutExpired:
        return False, "Database export timeout (>5 minutes)"
    except Exception as e:
        return False, f"Export error: {str(e)}"
