"""
Maya Banking Voice Agent — FastAPI backend server.

Provides LiveKit token generation, banking tool APIs,
realtime debug event streaming, and call log persistence.
"""

from __future__ import annotations

import ssl_certs

ssl_certs.configure_ssl_certs()

import env_setup

env_setup.load_project_env()

import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes import bank_tools, livekit_token, logs

# Load .env from backend dir or project root
_backend_dir = Path(__file__).resolve().parent
load_dotenv(_backend_dir / ".env")
load_dotenv(_backend_dir.parent / ".env")


@asynccontextmanager
async def lifespan(app: FastAPI):
    log_dir = Path(os.getenv("LOG_DIR", "./agent/call_logs"))
    log_dir.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(
    title="Maya Banking Voice Agent API",
    description="Backend for LiveKit token, banking tools, and debug observability",
    version="1.0.0",
    lifespan=lifespan,
)

frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        frontend_url,
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ],
    # Allow any localhost port during local dev (e.g. when 3000 is taken)
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(livekit_token.router)
app.include_router(bank_tools.router)
app.include_router(logs.router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "maya-bank-backend"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
