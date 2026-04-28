from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.api.schemas.chat import ChatRequest, ChatResponse
from app.api.services.chat_service import ask_agent

router = APIRouter(prefix="/api", tags=["chat"])


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest) -> ChatResponse:
    try:
        answer = ask_agent(
            user_id=payload.user_id,
            thread_id=payload.thread_id,
            message=payload.message,
        )
    except Exception as ex:
        raise HTTPException(status_code=500, detail=f"chat failed: {ex}") from ex

    return ChatResponse(
        answer=answer,
        thread_id=payload.thread_id,
        user_id=payload.user_id,
    )
