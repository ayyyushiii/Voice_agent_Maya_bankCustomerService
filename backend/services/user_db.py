"""Shared mock user database access."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "mockUsers.json"

# Per-call verification state: call_id -> userId
_verified_sessions: dict[str, str] = {}


def load_users() -> list[dict[str, Any]]:
    with open(DATA_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return data.get("users", [])


def find_user(user_id: str | None = None, phone: str | None = None) -> dict[str, Any] | None:
    users = load_users()
    for user in users:
        if user_id and user.get("userId") == user_id:
            return user
        if phone and user.get("registeredPhone") == phone:
            return user
    return None


def save_users(users: list[dict[str, Any]]) -> None:
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump({"users": users}, f, indent=2)


def mark_verified(call_id: str, user_id: str) -> None:
    _verified_sessions[call_id] = user_id


def is_verified(call_id: str) -> bool:
    return call_id in _verified_sessions


def get_verified_user_id(call_id: str) -> str | None:
    return _verified_sessions.get(call_id)


def clear_verification(call_id: str) -> None:
    _verified_sessions.pop(call_id, None)
