"""Shared session state for Maya voice agent jobs."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Optional

from agent.observability.logger import CallLogger


@dataclass
class MayaSessionData:
    call_id: str
    call_logger: CallLogger
    verified: bool = False
    simulate_tool_failure: bool = False
    simulate_stt_failure: bool = False
    simulate_tts_failure: bool = False
    simulate_llm_failure: bool = False
    silence_count: int = 0
    last_activity: float = field(default_factory=time.monotonic)
    silence_task: Optional[asyncio.Task] = None
