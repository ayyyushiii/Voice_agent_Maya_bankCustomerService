"""Load persisted call logs for replay."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Optional


def get_log_dir() -> Path:
    return Path(os.getenv("LOG_DIR", "./agent/call_logs"))


def load_call_log(call_id: str) -> Optional[dict[str, Any]]:
    path = get_log_dir() / f"{call_id}.json"
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def list_call_logs(limit: int = 50) -> list[dict[str, Any]]:
    log_dir = get_log_dir()
    if not log_dir.exists():
        return []
    files = sorted(log_dir.glob("call_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    results = []
    for f in files[:limit]:
        try:
            with open(f, encoding="utf-8") as fh:
                data = json.load(fh)
            results.append(
                {
                    "callId": data.get("callId"),
                    "startedAt": data.get("startedAt"),
                    "endedAt": data.get("endedAt"),
                    "summary": data.get("summary"),
                }
            )
        except Exception:
            continue
    return results
