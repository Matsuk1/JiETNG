from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
import pytz
import datetime
import logging
import time
import main
import os

log_path = os.path.join("logs", "timely_mission.log")  # 相对路径：./logs/timely_mission.log
os.makedirs(os.path.dirname(log_path), exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_path, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

def job_0():
    logging.info("用户状态重置任务 00:00 执行")
    main.reset_user_status()

def job_4():
    logging.info("机厅人数清零任务 4:00 执行")
    main.clear_arcade()

def job_listener(event):
    if event.exception:
        logging.error(f"任务 {event.job_id} 执行失败")
    else:
        logging.info(f"任务 {event.job_id} 执行成功")

def main_loop():
    timezone = pytz.timezone('Asia/Tokyo')
    scheduler = BackgroundScheduler(timezone=timezone)

    scheduler.add_job(job_0, 'cron', hour=0, minute=0, id='用户状态重置', replace_existing=True)
    scheduler.add_job(job_4, 'cron', hour=4, minute=0, id='机厅人数清零', replace_existing=True)

    scheduler.add_listener(job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
    scheduler.start()
    logging.info("定时任务调度器已启动")

    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        logging.info("定时任务服务正在关闭...")
        scheduler.shutdown()

if __name__ == "__main__":
    main_loop()
