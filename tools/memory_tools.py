from __future__ import annotations

import os

from langchain.tools import tool

from app.memory_store import save_user_memory, search_user_memory


def _current_user_id(explicit_user_id: str | None = None) -> str:
    if explicit_user_id and explicit_user_id.strip():
        return explicit_user_id.strip()
    return os.getenv("AGENT_USER_ID", "demo-user")


@tool
def remember_user_fact(key: str, value: str, user_id: str = "") -> str:
    """保存用户长期记忆。适用于“我喜欢/我习惯/请记住”这类稳定信息。"""
    uid = _current_user_id(user_id)
    save_user_memory(uid, key, value)
    return f"已保存记忆: user_id={uid}, key={key}, value={value}"


@tool
def recall_user_facts(query: str, user_id: str = "", limit: int = 5) -> str:
    """检索用户长期记忆。用于回忆用户偏好、习惯或历史事实。"""
    uid = _current_user_id(user_id)
    rows = search_user_memory(uid, query=query, limit=max(1, min(limit, 20)))
    if not rows:
        return f"未找到匹配记忆。user_id={uid}, query={query}"

    lines = [f"user_id={uid} 的匹配记忆："]
    for row in rows:
        lines.append(f"- {row['key']} = {row['value']} (更新时间: {row['updated_at']})")
    return "\n".join(lines)

