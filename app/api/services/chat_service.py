from __future__ import annotations

from app.agent import run_agent_for_user


def ask_agent(*, user_id: str, thread_id: str, message: str) -> str:
    clean_message = message.strip()
    if not clean_message:
        return ""
    return run_agent_for_user(
        user_text=clean_message,
        user_id=user_id,
        thread_id=thread_id,
    )
