import requests
import logging
import os
import time
import secrets
import threading
from io import BytesIO
from PIL import Image
from modules.config_loader import IMGUR_CLIENT_ID, IMG_DIR, DOMAIN

logger = logging.getLogger(__name__)

# 图片清理任务列表 {image_id: cleanup_time}
_image_cleanup_tasks = {}
_cleanup_lock = threading.Lock()
_periodic_cleanup_thread = None

def cleanup_expired_images():
    """清理所有过期的图片（基于文件修改时间）"""
    try:
        if not os.path.exists(IMG_DIR):
            return

        current_time = time.time()
        expiry_seconds = 1800  # 30分钟

        deleted_count = 0
        for filename in os.listdir(IMG_DIR):
            if not filename.endswith('.png'):
                continue

            file_path = os.path.join(IMG_DIR, filename)
            try:
                # 获取文件修改时间
                file_mtime = os.path.getmtime(file_path)
                age = current_time - file_mtime

                # 如果文件超过30分钟，删除它
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

def _upload_to_uguu(img):
    url = "https://uguu.se/upload.php"

    img_io = BytesIO()
    try:
        img.save(img_io, format='PNG')
        img_io.seek(0)
        files = {'files[]': ('image.png', img_io, 'image/png')}
        resp = requests.post(url, files=files)

        try:
            if resp.status_code == 200:
                data = resp.json()
                if data.get("success") and data.get("files"):
                    return data["files"][0]["url"]
                else:
                    logger.error(f"[ImageUploader] ✗ Uguu upload failed: data={data}")
            else:
                logger.error(f"[ImageUploader] ✗ Uguu request failed: status={resp.status_code}")
        except Exception as e:
            logger.error(f"[ImageUploader] ✗ Uguu response parsing error: error={e}")

        return None
    finally:
        img_io.close()

def _upload_to_0x0(img):
    url = "https://0x0.st"

    img_io = BytesIO()
    try:
        img.save(img_io, format='PNG')
        img_io.seek(0)
        files = {'file': ('image.png', img_io, 'image/png')}
        response = requests.post(url, files=files)

        try:
            if response.status_code == 200 and response.text.startswith("https://0x0.st/"):
                return response.text.strip()
            else:
                logger.error(f"[ImageUploader] ✗ 0x0 upload failed: response={response.text}")
        except Exception as e:
            logger.error(f"[ImageUploader] ✗ 0x0 exception: error={e}")

        return None
    finally:
        img_io.close()

def _upload_to_imgur(img):
    """上传图片到 Imgur"""
    if not IMGUR_CLIENT_ID:
        logger.error("[ImageUploader] ✗ Imgur client ID not configured")
        return None

    url = "https://api.imgur.com/3/image"
    headers = {"Authorization": f"Client-ID {IMGUR_CLIENT_ID}"}

    img_io = BytesIO()
    try:
        img.save(img_io, format='PNG')
        img_io.seek(0)

        files = {'image': img_io}

        try:
            response = requests.post(url, headers=headers, files=files)
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and data.get("data"):
                    return data["data"]["link"]
                else:
                    logger.error(f"[ImageUploader] ✗ Imgur upload failed: data={data}")
            else:
                logger.error(f"[ImageUploader] ✗ Imgur request failed: status={response.status_code}, response={response.text}")
        except Exception as e:
            logger.error(f"[ImageUploader] ✗ Imgur exception: error={e}")

        return None
    finally:
        img_io.close()

# 智能图床上传（上传原图和预览图）
def smart_upload(img):
    """上传图片到图床，返回原图和预览图链接

    Args:
        img: PIL Image 对象

    Returns:
        tuple: (original_url, preview_url) 如果上传失败返回 (None, None)
    """
    # 优先使用本地图床
    logger.info("[ImageUploader] → Using local image host")
    local_url = _save_to_local(img)
    if local_url:
        logger.info(f"[ImageUploader] ✓ Local upload complete: url={local_url}")
        return local_url, local_url

    # 本地图床失败时，回退到外部图床
    logger.warning("[ImageUploader] ⚠ Local image host failed, falling back to external hosts")

    # 一次性转换为 BytesIO，避免重复序列化
    original_io = BytesIO()
    try:
        img.save(original_io, format='PNG')
        original_io.seek(0)

        # 上传原图
        logger.info("[ImageUploader] → Uploading original image")
        original_url = None

        # 优先尝试 imgur
        if IMGUR_CLIENT_ID:
            logger.info("[ImageUploader] → Using imgur to upload original")
            url = "https://api.imgur.com/3/image"
            headers = {"Authorization": f"Client-ID {IMGUR_CLIENT_ID}"}
            files = {'image': original_io}

            try:
                response = requests.post(url, headers=headers, files=files)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success") and data.get("data"):
                        original_url = data["data"]["link"]
            except Exception as e:
                logger.error(f"[ImageUploader] ✗ Imgur upload exception: error={e}")

            original_io.seek(0)  # 重置指针以供后续使用

        if not original_url:
            logger.info("[ImageUploader] → Using uguu to upload original")
            files = {'files[]': ('image.png', original_io, 'image/png')}
            try:
                resp = requests.post("https://uguu.se/upload.php", files=files)
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("success") and data.get("files"):
                        original_url = data["files"][0]["url"]
            except Exception as e:
                logger.error(f"[ImageUploader] ✗ Uguu upload exception: error={e}")

            original_io.seek(0)

        if not original_url:
            logger.info("[ImageUploader] → Using 0x0 to upload original")
            files = {'file': ('image.png', original_io, 'image/png')}
            try:
                response = requests.post("https://0x0.st", files=files)
                if response.status_code == 200 and response.text.startswith("https://0x0.st/"):
                    original_url = response.text.strip()
            except Exception as e:
                logger.error(f"[ImageUploader] ✗ 0x0 upload exception: error={e}")

        if not original_url:
            logger.error("[ImageUploader] ✗ All upload methods failed")
            return None, None

        # 不再上传预览图，直接使用原图
        logger.info(f"[ImageUploader] ✓ Upload complete: url={original_url}")
        return original_url, original_url
    finally:
        original_io.close()
