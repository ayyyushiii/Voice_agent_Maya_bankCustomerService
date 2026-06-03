"""Structured debug event types for Maya voice agent."""

from __future__ import annotations

from enum import Enum
from typing import Any


class EventType(str, Enum):
    ROOM_CREATED = "room_created"
    USER_JOINED = "user_joined"
    AGENT_JOINED = "agent_joined"
    STT_PARTIAL = "stt_partial"
    STT_FINAL = "stt_final"
    LLM_STARTED = "llm_started"
    TOOL_CALLED = "tool_called"
    TOOL_RESULT = "tool_result"
    TTS_STARTED = "tts_started"
    AGENT_SPEAKING = "agent_speaking"
    INTERRUPTION_DETECTED = "interruption_detected"
    SILENCE_TIMEOUT = "silence_timeout"
    TOOL_FAILURE = "tool_failure"
    DISCONNECT = "disconnect"
    CALL_ENDED = "call_ended"
    LATENCY_UPDATE = "latency_update"
    ERROR = "error"


EVENT_TYPES = [e.value for e in EventType]


def make_event(
    call_id: str,
    event_type: str | EventType,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    from datetime import datetime, timezone

    return {
        "call_id": call_id,
        "event_type": event_type.value if isinstance(event_type, EventType) else event_type,
        "payload": payload or {},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
