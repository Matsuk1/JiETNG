"""Example chat-scoped long-session plugin.

Copy this file to `plugins/guess_number.py` and restart JiETNG to enable it.
"""

import random


def register(api):
    api.command("guess", start_guess, name="plugin_guess_number")


def start_guess(ctx, api):
    answer = random.randint(1, 100)
    api.start_session(
        ctx,
        handle_guess,
        state={"answer": answer, "attempts": 0},
        ttl=1800,
        scope="chat",
    )
    return api.text("猜数字开始：请输入 1-100。发送 结束猜数字 可结束。")


def handle_guess(ctx, session, api):
    text = ctx.text.strip()
    if text in {"结束猜数字", "结束", "quit", "exit"}:
        session.end()
        return api.text("猜数字已结束。")

    try:
        guess = int(text)
    except ValueError:
        return api.text("请输入数字，或发送 结束猜数字。")

    session.state["attempts"] += 1
    answer = session.state["answer"]
    if guess < answer:
        return api.text("太小了。")
    if guess > answer:
        return api.text("太大了。")

    attempts = session.state["attempts"]
    session.end()
    return api.text(f"猜对了！答案是 {answer}，共用了 {attempts} 次。")
