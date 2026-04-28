from __future__ import annotations

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    user_id: str = Field(default="demo-user", min_length=1, max_length=128)
    thread_id: str = Field(default="web-default", min_length=1, max_length=128)
    message: str = Field(min_length=1, max_length=4000)


class ChatResponse(BaseModel):
    answer: str
    thread_id: str
    user_id: str
