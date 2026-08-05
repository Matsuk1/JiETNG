"""Concurrent task execution with timeout logging and admin tracking."""

import threading
import time
import traceback
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class TaskContext:
    user_id: str | None = None
    reply_token: str | None = None
    source_type: str = "user"


@dataclass(frozen=True, slots=True)
class TaskOutcome:
    status: str
    duration: float
    error: str | None = None


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
        queued = next(
            (dict(item) for item in tracking["queued"] if item.get("id") == task_id),
            {},
        )
        tracking["queued"] = [item for item in tracking["queued"] if item.get("id") != task_id]
        tracking["running"].append(
            {
                **queued,
                "id": task_id,
                "function": queued.get("function", func.__name__),
                "user_id": queued.get("user_id", context.user_id or "Unknown"),
                "started_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        )


def _finish_tracking(task_id, outcome, tracking, lock, max_completed):
    if not task_id:
        return
    with lock:
        completed = next(
            (dict(item) for item in tracking["running"] if item.get("id") == task_id),
            None,
        )
        tracking["running"] = [item for item in tracking["running"] if item.get("id") != task_id]
        if completed:
            completed.update(
                {
                    "status": outcome.status,
                    "duration": round(outcome.duration, 3),
                    "error": outcome.error,
                    "finished_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
            )
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
    started = time.monotonic()
    error = None
    timed_out = threading.Event()

    with semaphore:
        done = threading.Event()

        def target():
            try:
                func(*args)
            except Exception as exc:
                nonlocal error
                error = exc
                logger.exception("[Task] Execution error: function=%s", func.__name__)
                if on_error:
                    on_error(func, exc, context, traceback.format_exc())
            finally:
                done.set()

        thread = threading.Thread(target=target)
        thread.start()

        def mark_timeout():
            if not done.is_set():
                timed_out.set()
                logger.warning("[Task] Execution timeout: timeout=%ss", timeout)

        timer = threading.Timer(timeout, mark_timeout)
        timer.start()
        thread.join()
        timer.cancel()

    status = "failed" if error else "completed"
    if timed_out.is_set() and not error:
        status = "timed_out"
    outcome = TaskOutcome(
        status=status,
        duration=time.monotonic() - started,
        error=f"{type(error).__name__}: {error}" if error else None,
    )
    _finish_tracking(task_id, outcome, tracking, tracking_lock, max_completed)
    if on_complete:
        on_complete(func, outcome)
    return outcome


def queue_worker(task_queue, run_item):
    while True:
        item = task_queue.get()
        try:
            run_item(item)
        finally:
            task_queue.task_done()
