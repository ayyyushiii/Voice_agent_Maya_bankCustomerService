"""Call logging, event streaming, and replay API."""

from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from services.debug_flags import get_flags, set_flags

router = APIRouter(prefix="/api/logs", tags=["logs"])

LOG_DIR = Path(os.getenv("LOG_DIR", "./agent/call_logs"))
LOG_DIR.mkdir(parents=True, exist_ok=True)

# In-memory event hub: call_id -> { websockets, buffer, call_log }
_call_sessions: dict[str, dict[str, Any]] = {}


class DebugEvent(BaseModel):
    call_id: str
    event_type: str
    payload: dict[str, Any] = Field(default_factory=dict)
    timestamp: Optional[str] = None


class FailureFlagsRequest(BaseModel):
    stt_failure: Optional[bool] = None
    tts_failure: Optional[bool] = None
    llm_failure: Optional[bool] = None
    tool_failure: Optional[bool] = None
    livekit_disconnect: Optional[bool] = None


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get_session(call_id: str) -> dict[str, Any]:
    if call_id not in _call_sessions:
        _call_sessions[call_id] = {
            "websockets": set(),
            "buffer": [],
            "call_log": {
                "callId": call_id,
                "startedAt": _now_iso(),
                "endedAt": None,
                "transcripts": [],
                "events": [],
                "latency": {},
                "toolCalls": [],
                "errors": [],
                "summary": None,
            },
        }
    return _call_sessions[call_id]


def _persist_call_log(call_id: str) -> None:
    session = _call_sessions.get(call_id)
    if not session:
        return
    path = LOG_DIR / f"{call_id}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(session["call_log"], f, indent=2, default=str)


def _update_call_log_from_event(call_id: str, event: dict[str, Any]) -> None:
    session = _get_session(call_id)
    log = session["call_log"]
    log["events"].append(event)

    etype = event.get("event_type")
    payload = event.get("payload", {})

    if etype in ("stt_partial", "stt_final"):
        log["transcripts"].append(
            {
                "type": etype,
                "text": payload.get("text", ""),
                "timestamp": event.get("timestamp"),
            }
        )
    elif etype == "tool_called":
        log["toolCalls"].append(
            {
                "tool": payload.get("tool"),
                "args": payload.get("args"),
                "timestamp": event.get("timestamp"),
            }
        )
    elif etype == "tool_result":
        if log["toolCalls"]:
            log["toolCalls"][-1]["result"] = payload.get("result")
            log["toolCalls"][-1]["durationMs"] = payload.get("durationMs")
    elif etype == "tool_failure":
        log["errors"].append(
            {"type": "tool_failure", "detail": payload, "timestamp": event.get("timestamp")}
        )
    elif etype == "latency_update":
        log["latency"].update(payload)
    elif etype == "call_ended":
        log["endedAt"] = event.get("timestamp")
        log["summary"] = payload.get("summary")
        _persist_call_log(call_id)


async def _broadcast(call_id: str, event: dict[str, Any]) -> None:
    session = _get_session(call_id)
    session["buffer"].append(event)
    if len(session["buffer"]) > 500:
        session["buffer"] = session["buffer"][-500:]

    _update_call_log_from_event(call_id, event)

    dead: set[WebSocket] = set()
    for ws in session["websockets"]:
        try:
            await ws.send_json(event)
        except Exception:
            dead.add(ws)
    session["websockets"] -= dead


@router.post("/events")
async def ingest_event(event: DebugEvent):
    """Agent and services POST structured debug events here."""
    enriched = {
        "call_id": event.call_id,
        "event_type": event.event_type,
        "payload": event.payload,
        "timestamp": event.timestamp or _now_iso(),
    }
    await _broadcast(event.call_id, enriched)
    return {"ok": True}


@router.websocket("/ws/{call_id}")
async def websocket_events(websocket: WebSocket, call_id: str):
    """Frontend subscribes to realtime debug events for a call."""
    await websocket.accept()
    session = _get_session(call_id)
    session["websockets"].add(websocket)

    # Send buffered history
    for evt in session["buffer"]:
        await websocket.send_json(evt)

    try:
        while True:
            # Keep connection alive; client may send pings
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        session["websockets"].discard(websocket)


@router.get("/calls")
async def list_calls():
    files = sorted(LOG_DIR.glob("call_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    calls = []
    for f in files[:50]:
        try:
            with open(f, encoding="utf-8") as fh:
                data = json.load(fh)
            calls.append(
                {
                    "callId": data.get("callId"),
                    "startedAt": data.get("startedAt"),
                    "endedAt": data.get("endedAt"),
                    "summary": data.get("summary"),
                }
            )
        except Exception:
            continue
    return {"calls": calls}


@router.get("/calls/{call_id}")
async def get_call_log(call_id: str):
    path = LOG_DIR / f"{call_id}.json"
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    session = _call_sessions.get(call_id)
    if session:
        return session["call_log"]

    raise HTTPException(status_code=404, detail="Call log not found")


@router.post("/calls/{call_id}/end")
async def end_call(call_id: str, summary: Optional[dict[str, Any]] = None):
    await _broadcast(
        call_id,
        {
            "call_id": call_id,
            "event_type": "call_ended",
            "payload": {"summary": summary or {"status": "completed"}},
            "timestamp": _now_iso(),
        },
    )
    return {"ok": True}


@router.get("/debug/{call_id}/flags")
async def get_debug_flags(call_id: str):
    return get_flags(call_id)


@router.post("/debug/{call_id}/flags")
async def update_debug_flags(call_id: str, body: FailureFlagsRequest):
    flags = {k: v for k, v in body.model_dump().items() if v is not None}
    return set_flags(call_id, flags)
