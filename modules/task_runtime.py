"""Concurrent task execution with timeout logging and admin tracking."""

import threading
import traceback
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TaskContext:
    user_id: str | None = None
    reply_token: str | None = None
    source_type: str = "user"


def task_context(args):
    if not args:
        return TaskContext()
    first = args[0]
    if hasattr(first, "source"):
        source = first.source
        return TaskContext(
            user_id=getattr(source, "user_id", None),
            reply_token=getattr(first, "reply_token", None),
            source_type=getattr(source, "type", "user"),
        )
    if isinstance(first, str) and first.startswith("U"):
        reply_token = args[1] if len(args) > 1 and isinstance(args[1], str) else None
        return TaskContext(user_id=first, reply_token=reply_token)
    return TaskContext()


def track_queued(tracking, lock, task):
    with lock:
        tracking["queued"].append(task)


def discard_queued(tracking, lock, task_id):
    with lock:
        tracking["queued"] = [
            item for item in tracking["queued"] if item.get("id") != task_id
        ]


def _start_tracking(task_id, func, context, tracking, lock):
    if not task_id:
        return
    with lock:
        tracking["queued"] = [item for item in tracking["queued"] if item.get("id") != task_id]
        tracking["running"].append({
            "id": task_id,
            "function": func.__name__,
            "user_id": context.user_id or "Unknown",
        })


def _finish_tracking(task_id, tracking, lock, max_completed):
    if not task_id:
        return
    with lock:
        completed = next(
            (dict(item) for item in tracking["running"] if item.get("id") == task_id),
            None,
        )
        tracking["running"] = [item for item in tracking["running"] if item.get("id") != task_id]
        if completed:
            tracking["completed"].insert(0, completed)
            del tracking["completed"][max_completed:]


def execute_task(
    func,
    args,
    semaphore,
    *,
    task_id=None,
    tracking,
    tracking_lock,
    max_completed=20,
    timeout=120,
    logger,
    on_error=None,
    on_complete=None,
):
    context = task_context(args)
    _start_tracking(task_id, func, context, tracking, tracking_lock)

    with semaphore:
        done = threading.Event()

        def target():
            try:
                func(*args)
            except Exception as error:
                logger.exception("[Task] Execution error: function=%s", func.__name__)
                if on_error:
                    on_error(func, error, context, traceback.format_exc())
            finally:
                done.set()

        thread = threading.Thread(target=target)
        thread.start()
        timer = threading.Timer(
            timeout,
            lambda: logger.warning("[Task] Execution timeout: timeout=%ss", timeout)
            if not done.is_set() else None,
        )
        timer.start()
        thread.join()
        timer.cancel()

    _finish_tracking(task_id, tracking, tracking_lock, max_completed)
    if on_complete:
        on_complete(func)


def queue_worker(task_queue, run_item):
    while True:
        item = task_queue.get()
        try:
            run_item(item)
        finally:
            task_queue.task_done()
