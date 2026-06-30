"""Background task queues used by JiETNG.

This module owns the generic queue mechanics: concurrency limits, task
tracking, timeout logging, and worker loops. The application passes callbacks
for app-specific behavior such as admin notification and LINE replies.
"""

import logging
import queue
import threading
import traceback
from typing import Callable, Optional


class TaskQueueManager:
    def __init__(
        self,
        *,
        max_queue_size: int,
        max_image_tasks: int,
        max_web_tasks: int,
        task_timeout_seconds: int,
        max_completed_tasks: int = 20,
        on_error: Optional[Callable] = None,
        user_error_message: Optional[Callable[[str], object]] = None,
        reply_user: Optional[Callable[[str, str, object], None]] = None,
        logger: Optional[logging.Logger] = None,
    ):
        self.logger = logger or logging.getLogger(__name__)
        self.task_timeout_seconds = task_timeout_seconds
        self.max_completed_tasks = max_completed_tasks
        self.on_error = on_error
        self.user_error_message = user_error_message
        self.reply_user = reply_user

        self.image_queue = queue.Queue(maxsize=max_queue_size)
        self.webtask_queue = queue.Queue(maxsize=max_queue_size)
        self.image_concurrency_limit = threading.Semaphore(max_image_tasks)
        self.webtask_concurrency_limit = threading.Semaphore(max_web_tasks)

        self.stats = {"tasks_processed": 0}
        self.stats_lock = threading.Lock()
        self.task_tracking = {
            "running": [],
            "queued": [],
            "completed": [],
        }
        self.task_tracking_lock = threading.Lock()

    def bump_stats(self) -> None:
        with self.stats_lock:
            self.stats["tasks_processed"] += 1

    def _extract_user_context(self, args):
        user_id = None
        reply_token = None
        if args:
            first = args[0]
            if hasattr(first, "source") and hasattr(first, "reply_token"):
                user_id = first.source.user_id
                reply_token = first.reply_token
            elif isinstance(first, str) and first.startswith("U"):
                user_id = first
                if len(args) > 1 and isinstance(args[1], str):
                    reply_token = args[1]
        return user_id, reply_token

    def _tracking_user_id(self, args):
        user_id, _ = self._extract_user_context(args)
        return user_id or "Unknown"

    def _cancel_if_timeout(self, task_done: threading.Event) -> None:
        if not task_done.is_set():
            self.logger.warning(
                f"[Task] \u26a0 Execution timeout: timeout={self.task_timeout_seconds}s"
            )

    def _notify_worker_error(self, title: str, worker: str, exc: Exception) -> None:
        self.logger.error(f"[Task] Worker error: worker={worker}, error={exc}", exc_info=True)
        if self.on_error:
            self.on_error(
                error_title=title,
                error_details=f"{type(exc).__name__}: {str(exc)}\n\n{traceback.format_exc()}",
                context={"Worker": worker},
                user_id=None,
            )

    def run_task_with_limit(
        self,
        func: callable,
        args: tuple,
        sem: threading.Semaphore,
        task_id: str = None,
    ) -> None:
        if task_id:
            with self.task_tracking_lock:
                self.task_tracking["queued"] = [
                    t for t in self.task_tracking["queued"]
                    if t.get("id") != task_id
                ]
                self.task_tracking["running"].append({
                    "id": task_id,
                    "function": func.__name__,
                    "user_id": self._tracking_user_id(args),
                })

        with sem:
            task_done = threading.Event()

            def target():
                try:
                    func(*args)
                except Exception as e:
                    self.logger.error(
                        f"[Task] \u2717 Execution error: function={func.__name__}, error={e}",
                        exc_info=True,
                    )
                    user_id, reply_token = self._extract_user_context(args)

                    if self.on_error:
                        self.on_error(
                            error_title=f"Task Execution Failed: {func.__name__}",
                            error_details=(
                                f"{type(e).__name__}: {str(e)}\n\n"
                                f"{traceback.format_exc()}"
                            ),
                            context={
                                "Task": func.__name__,
                                "Error Type": type(e).__name__,
                            },
                            user_id=user_id,
                        )

                    if user_id and reply_token and self.reply_user and self.user_error_message:
                        try:
                            self.reply_user(user_id, reply_token, self.user_error_message(user_id))
                        except Exception:
                            pass
                finally:
                    task_done.set()

            thread = threading.Thread(target=target)
            thread.start()

            timer = threading.Timer(
                self.task_timeout_seconds,
                self._cancel_if_timeout,
                args=(task_done,),
            )
            timer.start()

            thread.join()
            timer.cancel()

            if task_id:
                with self.task_tracking_lock:
                    task_info = None
                    for item in self.task_tracking["running"]:
                        if item.get("id") == task_id:
                            task_info = item.copy()
                            break
                    self.task_tracking["running"] = [
                        t for t in self.task_tracking["running"]
                        if t.get("id") != task_id
                    ]
                    if task_info:
                        self.task_tracking["completed"].insert(0, task_info)
                        self.task_tracking["completed"] = (
                            self.task_tracking["completed"][:self.max_completed_tasks]
                        )

            self.bump_stats()
            total = self.stats["tasks_processed"]
            self.logger.info(f"[Task] \u2713 Completed: function={func.__name__}, total={total}")

    def _run_image_task(self, item) -> None:
        func, args, task_id = (item if len(item) == 3 else (*item, None))
        self.run_task_with_limit(func, args, self.image_concurrency_limit, task_id)

    def image_worker(self) -> None:
        while True:
            item = self.image_queue.get()
            try:
                self._run_image_task(item)
            except Exception as e:
                self._notify_worker_error("Image Task Worker Error", "image_worker", e)
            finally:
                self.image_queue.task_done()

    def _run_webtask(self, item) -> None:
        func, args, task_id = (item if len(item) == 3 else (*item, None))
        self.run_task_with_limit(func, args, self.webtask_concurrency_limit, task_id)

    def webtask_worker(self) -> None:
        while True:
            item = self.webtask_queue.get()
            try:
                self._run_webtask(item)
            except Exception as e:
                self._notify_worker_error("Web Task Worker Error", "webtask_worker", e)
            finally:
                self.webtask_queue.task_done()

    def start_workers(self, image_workers: int, web_workers: int) -> None:
        for i in range(image_workers):
            threading.Thread(
                target=self.image_worker,
                daemon=True,
                name=f"ImageWorker-{i+1}",
            ).start()

        for i in range(web_workers):
            threading.Thread(
                target=self.webtask_worker,
                daemon=True,
                name=f"WebTaskWorker-{i+1}",
            ).start()
