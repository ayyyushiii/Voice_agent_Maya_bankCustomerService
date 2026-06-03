"""Latency tracking for STT, LLM, TTS, tools, and end-to-end."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class LatencyTracker:
    """Tracks pipeline latencies in milliseconds."""

    stt_ms: list[float] = field(default_factory=list)
    llm_ms: list[float] = field(default_factory=list)
    tts_ms: list[float] = field(default_factory=list)
    tool_ms: list[float] = field(default_factory=list)
    e2e_ms: list[float] = field(default_factory=list)

    _stt_start: Optional[float] = None
    _llm_start: Optional[float] = None
    _tts_start: Optional[float] = None
    _e2e_start: Optional[float] = None

    def start_stt(self) -> None:
        self._stt_start = time.perf_counter()

    def end_stt(self) -> float:
        if self._stt_start is None:
            return 0.0
        ms = (time.perf_counter() - self._stt_start) * 1000
        self.stt_ms.append(ms)
        self._stt_start = None
        return ms

    def start_llm(self) -> None:
        self._llm_start = time.perf_counter()

    def end_llm(self) -> float:
        if self._llm_start is None:
            return 0.0
        ms = (time.perf_counter() - self._llm_start) * 1000
        self.llm_ms.append(ms)
        self._llm_start = None
        return ms

    def start_tts(self) -> None:
        self._tts_start = time.perf_counter()

    def end_tts(self) -> float:
        if self._tts_start is None:
            return 0.0
        ms = (time.perf_counter() - self._tts_start) * 1000
        self.tts_ms.append(ms)
        self._tts_start = None
        return ms

    def record_tool(self, ms: float) -> None:
        self.tool_ms.append(ms)

    def start_e2e(self) -> None:
        self._e2e_start = time.perf_counter()

    def end_e2e(self) -> float:
        if self._e2e_start is None:
            return 0.0
        ms = (time.perf_counter() - self._e2e_start) * 1000
        self.e2e_ms.append(ms)
        self._e2e_start = None
        return ms

    @staticmethod
    def _avg(values: list[float]) -> float:
        return round(sum(values) / len(values), 1) if values else 0.0

    @staticmethod
    def _last(values: list[float]) -> float:
        return round(values[-1], 1) if values else 0.0

    def snapshot(self) -> dict[str, Any]:
        return {
            "stt": {"last": self._last(self.stt_ms), "avg": self._avg(self.stt_ms)},
            "llm": {"last": self._last(self.llm_ms), "avg": self._avg(self.llm_ms)},
            "tts": {"last": self._last(self.tts_ms), "avg": self._avg(self.tts_ms)},
            "tool": {"last": self._last(self.tool_ms), "avg": self._avg(self.tool_ms)},
            "e2e": {"last": self._last(self.e2e_ms), "avg": self._avg(self.e2e_ms)},
        }
