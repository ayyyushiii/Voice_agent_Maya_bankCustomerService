"""Call logger — emits events to backend and persists call logs."""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, Optional

import httpx

from agent.observability.events import EventType, make_event
from agent.observability.latency import LatencyTracker

logger = logging.getLogger("maya.logger")


class CallLogger:
    """Publishes structured events to the FastAPI backend for UI streaming."""

    def __init__(self, call_id: str):
        self.call_id = call_id
        self.backend_url = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")
        self.latency = LatencyTracker()
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=10.0)
        return self._client

    async def emit(self, event_type: str | EventType, payload: dict[str, Any] | None = None) -> None:
        event = make_event(self.call_id, event_type, payload)
        try:
            client = await self._get_client()
            resp = await client.post(f"{self.backend_url}/api/logs/events", json=event)
            resp.raise_for_status()
        except Exception as exc:
            logger.warning("Failed to emit event %s: %s", event_type, exc)

    async def emit_latency(self) -> None:
        await self.emit(EventType.LATENCY_UPDATE, self.latency.snapshot())

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def end_call(self, summary: dict[str, Any]) -> None:
        await self.emit_latency()
        await self.emit(EventType.CALL_ENDED, {"summary": summary})
        try:
            client = await self._get_client()
            await client.post(
                f"{self.backend_url}/api/logs/calls/{self.call_id}/end",
                json=summary,
            )
        except Exception as exc:
            logger.warning("Failed to finalize call: %s", exc)
        await self.close()
