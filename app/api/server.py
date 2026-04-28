from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.chat import router as chat_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Lang-Agent API",
        version="0.1.0",
        description="HTTP API for Lang-Agent chat frontend.",
    )

    allow_origins_raw = os.getenv("API_ALLOW_ORIGINS", "http://localhost:5173")
    allow_origins = [item.strip() for item in allow_origins_raw.split(",") if item.strip()]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(chat_router)
    return app


app = create_app()
