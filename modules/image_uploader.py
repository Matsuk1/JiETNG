import logging
import os
import time
import secrets
import threading
import asyncio
from datetime import datetime
from io import BytesIO
from PIL import Image
import aioboto3
from modules.config_loader import (
    IMG_DIR, DOMAIN,
    R2_ENABLED, R2_ACCOUNT_ID, R2_ACCESS_KEY_ID,
    R2_SECRET_ACCESS_KEY, R2_BUCKET_NAME, R2_PUBLIC_URL
)

logger = logging.getLogger(__name__)

# 永久保留的文件名前缀
PERMANENT_PREFIX = "keep_"

# 图片清理任务列表 {image_id: cleanup_time}
_image_cleanup_tasks = {}
_cleanup_lock = threading.Lock()
_periodic_cleanup_thread = None

def cleanup_expired_images(expiry_seconds = 7200):
    """清理所有过期的图片（基于文件修改时间）"""
    try:
        if not os.path.exists(IMG_DIR):
            return

        current_time = time.time()

        deleted_count = 0
        skipped_count = 0
        for filename in os.listdir(IMG_DIR):
            if not filename.endswith('.png'):
                continue

            # 跳过永久保留的文件
            if filename.startswith(PERMANENT_PREFIX):
                skipped_count += 1
                continue

            file_path = os.path.join(IMG_DIR, filename)
            try:
                # 获取文件修改时间
                file_mtime = os.path.getmtime(file_path)
                age = current_time - file_mtime

                # 如果文件超过时间，删除
                if age > expiry_seconds:
                    os.remove(file_path)
                    deleted_count += 1
                    image_id = filename.replace('.png', '')
                    logger.info(f"[ImageCleanup] ✓ Deleted expired image: id={image_id}, age={int(age)}s")
            except Exception as e:
                logger.error(f"[ImageCleanup] ✗ Failed to process file: file={filename}, error={e}")

        if deleted_count > 0:
            logger.info(f"[ImageCleanup] ✓ Cleanup complete: deleted={deleted_count}")
    except Exception as e:
        logger.error(f"[ImageCleanup] ✗ Cleanup failed: error={e}")

def _start_periodic_cleanup():
    """启动定期清理任务（每5分钟执行一次）"""
    def periodic_task():
        while True:
            time.sleep(300)  # 5分钟
            logger.debug("[ImageCleanup] → Running periodic cleanup")
            cleanup_expired_images()

    global _periodic_cleanup_thread
    if _periodic_cleanup_thread is None or not _periodic_cleanup_thread.is_alive():
        _periodic_cleanup_thread = threading.Thread(
            target=periodic_task,
            daemon=True,
            name="PeriodicImageCleanup"
        )
        _periodic_cleanup_thread.start()
        logger.info("[ImageCleanup] ✓ Periodic cleanup thread started")

def _schedule_image_cleanup(image_id, delay_seconds=1800):
    """安排图片清理任务（默认30分钟）

    Args:
        image_id: 图片ID
        delay_seconds: 延迟时间（秒），默认1800秒（30分钟）
    """
    cleanup_time = time.time() + delay_seconds

    with _cleanup_lock:
        _image_cleanup_tasks[image_id] = cleanup_time

    def cleanup():
        time.sleep(delay_seconds)

        image_path = os.path.join(IMG_DIR, f"{image_id}.png")
        try:
            if os.path.exists(image_path):
                os.remove(image_path)
                logger.info(f"[ImageCleanup] ✓ Deleted expired image: id={image_id}")

            with _cleanup_lock:
                _image_cleanup_tasks.pop(image_id, None)
        except Exception as e:
            logger.error(f"[ImageCleanup] ✗ Failed to delete image: id={image_id}, error={e}")

    # 在后台线程中执行清理
    cleanup_thread = threading.Thread(target=cleanup, daemon=True, name=f"ImageCleanup-{image_id}")
    cleanup_thread.start()

def _save_to_local(img):
    """保存图片到本地图床

    Args:
        img: PIL Image 对象

    Returns:
        str: 图片URL，如果失败返回None
    """
    try:
        # 生成唯一ID（16字节 = 22个URL安全字符）
        image_id = secrets.token_urlsafe(16)
        image_path = os.path.join(IMG_DIR, f"{image_id}.png")

        # 保存图片
        img.save(image_path, format='PNG')

        # 安排30分钟后清理
        _schedule_image_cleanup(image_id, delay_seconds=1800)

        # 生成URL
        image_url = f"https://{DOMAIN}/linebot/img/{image_id}"

        logger.info(f"[LocalImageHost] ✓ Image saved: id={image_id}, url={image_url}")
        return image_url
    except Exception as e:
        logger.error(f"[LocalImageHost] ✗ Failed to save image: error={e}")
        return None

async def _upload_to_r2(img, user_id=None):
    """异步上传图片到 Cloudflare R2

    Args:
        img: PIL Image 对象
        user_id: 用户ID（可选）

    Returns:
        str: 图片URL，如果失败返回None
    """
    if not R2_ENABLED:
        return None

    img_io = BytesIO()
    try:
        # 生成唯一文件名，添加 gen/ 前缀
        image_id = secrets.token_urlsafe(16)
        file_name = f"gen/{image_id}.png"

        # 转换图片为字节流（在线程池中执行，避免阻塞）
        await asyncio.to_thread(img.save, img_io, format='PNG')
        img_io.seek(0)
        img_bytes = img_io.getvalue()

        # 准备元数据
        metadata = {
            'upload-time': datetime.now().isoformat()
        }
        if user_id:
            metadata['user-id'] = str(user_id)

        # 异步上传到 R2
        session = aioboto3.Session()
        async with session.client(
            's3',
            endpoint_url=f'https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com',
            aws_access_key_id=R2_ACCESS_KEY_ID,
            aws_secret_access_key=R2_SECRET_ACCESS_KEY,
            region_name='auto'
        ) as s3_client:
            await s3_client.put_object(
                Bucket=R2_BUCKET_NAME,
                Key=file_name,
                Body=img_bytes,
                ContentType='image/png',
                CacheControl='public, max-age=259200',  # 缓存3天
                Metadata=metadata
            )

        # 生成公开URL
        if R2_PUBLIC_URL:
            image_url = f"{R2_PUBLIC_URL.rstrip('/')}/{file_name}"
        else:
            image_url = f"https://pub-{R2_ACCOUNT_ID}.r2.dev/{file_name}"

        logger.info(f"[R2] ✓ Image uploaded: id={image_id}, path={file_name}, url={image_url}")
        return image_url

    except Exception as e:
        logger.error(f"[R2] ✗ Upload failed: error={e}")
        return None
    finally:
        img_io.close()

# 智能图床上传（异步）
async def smart_upload(img, user_id=None):
    """异步上传图片到图床，返回原图和预览图链接

    Args:
        img: PIL Image 对象
        user_id: 用户ID（可选，用于R2元数据）

    Returns:
        tuple: (original_url, preview_url) 如果上传失败返回 (None, None)
    """
    # 优先使用 Cloudflare R2（异步，永久存储，全球CDN加速）
    if R2_ENABLED:
        logger.info("[ImageUploader] → Using Cloudflare R2")
        r2_url = await _upload_to_r2(img, user_id)
        if r2_url:
            logger.info(f"[ImageUploader] ✓ R2 upload complete: url={r2_url}")
            return r2_url, r2_url

    # R2 失败或未启用时，使用本地图床（在线程池中执行）
    logger.info("[ImageUploader] → Using local image host")
    local_url = await asyncio.to_thread(_save_to_local, img)
    if local_url:
        logger.info(f"[ImageUploader] ✓ Local upload complete: url={local_url}")
        return local_url, local_url

    # 所有上传方法都失败
    logger.error("[ImageUploader] ✗ All upload methods failed (R2 and Local)")
    return None, None
