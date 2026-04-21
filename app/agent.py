"""使用 LangChain Agent + 通义千问（DashScope ChatTongyi）。"""

from __future__ import annotations

import os
from functools import lru_cache

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage, SystemMessage
from tools.search import search
from tools.baseTool import multiply, get_current_time, get_weather_for_location
from langgraph.checkpoint.memory import InMemorySaver
from app.memory_store import list_user_memory
from tools.memory_tools import remember_user_fact, recall_user_facts

load_dotenv()


def _require_dashscope_key() -> None:
    if not os.getenv("DASHSCOPE_API_KEY"):
        raise RuntimeError(
            "未设置环境变量 DASHSCOPE_API_KEY"
        )


@lru_cache(maxsize=1)
def get_agent_graph():
    """构建并缓存编译后的 LangGraph（避免每条消息重复初始化）。"""
    _require_dashscope_key()
    model_name = os.getenv("QWEN_MODEL", "qwen-turbo")
    llm = ChatTongyi(model=model_name, streaming=True)
    tools = [
        multiply,
        get_current_time,
        search,
        get_weather_for_location,
        remember_user_fact,
        recall_user_facts,
    ]
    system_prompt = (
        "你是一个乐于助人的助手，回答简洁清晰。"
        "当用户表达稳定偏好/习惯/个人事实（如喜欢什么、常住地、作息）时，"
        "调用 remember_user_fact 保存长期记忆；回答相关问题前可调用 recall_user_facts 检索。"
    )
    return create_agent(
        model=llm,
        tools=tools,
        system_prompt=system_prompt,
        checkpointer=InMemorySaver(),
    )


def _aimessage_text(msg: AIMessage) -> str:
    content = msg.content
    if isinstance(content, str):
        return content
    return str(content)


def _is_enabled(env_name: str, default: str = "0") -> bool:
    return os.getenv(env_name, default) in {"1", "true", "True", "yes", "on"}


def _message_chunk_text(msg: AIMessageChunk) -> str:
    content = msg.content
    if isinstance(content, str):
        return content
    return msg.text()


def _print_stream_step(step: str, data: object) -> None:
    if not isinstance(data, dict):
        print(f"[step] {step}")
        return
    print(f"[step] {step}")
    messages = data.get("messages") or []
    if not messages:
        return
    last_msg = messages[-1]
    if isinstance(last_msg, AIMessage):
        for call in getattr(last_msg, "tool_calls", []) or []:
            name = call.get("name", "unknown")
            args = call.get("args", {})
            print(f"[tool-call] name={name} args={args}")
        return
    tool_name = getattr(last_msg, "name", None)
    tool_call_id = getattr(last_msg, "tool_call_id", None)
    if tool_name or tool_call_id:
        content = getattr(last_msg, "content", "")
        print(
            f"[tool-result] name={tool_name or 'unknown'} "
            f"tool_call_id={tool_call_id or '-'} content={content}"
        )


def _log_tool_calls(messages: list[object]) -> None:
    """打印工具调用观测日志：工具名、参数、返回内容。"""
    if os.getenv("AGENT_LOG_TOOLS", "1") not in {"1", "true", "True"}:
        return

    for msg in messages:
        if isinstance(msg, AIMessage):
            for call in getattr(msg, "tool_calls", []) or []:
                name = call.get("name", "unknown")
                args = call.get("args", {})
                print(f"[tool-call] name={name} args={args}")
            continue

        # ToolMessage 通常包含 name / tool_call_id / content，这里用 getattr 保持兼容。
        tool_name = getattr(msg, "name", None)
        tool_call_id = getattr(msg, "tool_call_id", None)
        if tool_name or tool_call_id:
            content = getattr(msg, "content", "")
            print(
                f"[tool-result] name={tool_name or 'unknown'} "
                f"tool_call_id={tool_call_id or '-'} content={content}"
            )


def run_agent(user_text: str) -> str:
    """对用户输入运行 ReAct 智能体，返回最后一条助手回复文本。"""
    graph = get_agent_graph()
    # todo 会话id
    thread_id = os.getenv("AGENT_THREAD_ID", "cli-default")
    user_id = os.getenv("AGENT_USER_ID", "demo-user")
    memory_rows = list_user_memory(user_id, limit=8)
    memory_context = ("\n".join([f"- {row['key']}: {row['value']}" for row in memory_rows])
        if memory_rows
        else "（暂无长期记忆）"
    )
    injected_system = SystemMessage(
        content=(
            f"当前用户ID: {user_id}\n"
            "以下是该用户已保存的长期记忆，请在回答中合理利用：\n"
            f"{memory_context}"
        )
    )

    invoke_message = [injected_system, HumanMessage(content=user_text)]
    graph_input = {"messages": invoke_message}
    config = {"configurable": {"thread_id": thread_id, "user_id": user_id}}
    enable_stream_output = _is_enabled("AGENT_STREAM_OUTPUT")
    show_steps = _is_enabled("AGENT_STREAM_SHOW_STEPS")

    if enable_stream_output:
        chunks: list[str] = []
        stream_mode = ["messages", "updates"] if show_steps else "messages"
        for event in graph.stream(graph_input, config=config, stream_mode=stream_mode):
            if show_steps:
                mode, payload = event
                if mode == "messages":
                    msg_chunk, _ = payload
                    if not isinstance(msg_chunk, AIMessageChunk):
                        continue
                    text = _message_chunk_text(msg_chunk)
                    if not text:
                        continue
                    chunks.append(text)
                    print(text, end="", flush=True)
                    continue
                if mode == "updates":
                    for step, data in payload.items():
                        _print_stream_step(step, data)
                continue

            msg_chunk, _ = event
            if not isinstance(msg_chunk, AIMessageChunk):
                continue
            text = _message_chunk_text(msg_chunk)
            if not text:
                continue
            chunks.append(text)
            print(text, end="", flush=True)
        if chunks:
            print()
            return "".join(chunks)

    result = graph.invoke(graph_input, config=config)
    messages = result.get("messages") or []
    # _log_tool_calls(messages)
    if not messages:
        return ""
    last = messages[-1]
    if isinstance(last, AIMessage):
        return _aimessage_text(last)
    return str(getattr(last, "content", last))
