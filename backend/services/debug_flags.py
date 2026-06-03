"""Debug failure simulation toggles per call."""

from __future__ import annotations

from typing import Any

_failure_flags: dict[str, dict[str, bool]] = {}


def get_flags(call_id: str) -> dict[str, bool]:
    return _failure_flags.get(
        call_id,
        {
            "stt_failure": False,
            "tts_failure": False,
            "llm_failure": False,
            "tool_failure": False,
            "livekit_disconnect": False,
        },
    )


def set_flags(call_id: str, flags: dict[str, bool]) -> dict[str, bool]:
    current = get_flags(call_id)
    current.update({k: v for k, v in flags.items() if k in current})
    _failure_flags[call_id] = current
    return current


def should_fail(call_id: str, component: str) -> bool:
    return get_flags(call_id).get(component, False)


def clear_flags(call_id: str) -> None:
    _failure_flags.pop(call_id, None)
