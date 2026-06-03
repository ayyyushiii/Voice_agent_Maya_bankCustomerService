"""Debit/credit card blocking tool."""

from __future__ import annotations

import time

from livekit.agents import RunContext, function_tool

from agent.session_data import MayaSessionData
from services import banking_tools


@function_tool
async def block_card(context: RunContext[MayaSessionData]) -> str:
    """Block the customer's debit card immediately."""
    data = context.userdata
    call_logger = data.call_logger
    call_id = data.call_id

    await call_logger.emit("tool_called", {"tool": "block_card", "args": {}})
    start = time.perf_counter()

    result = banking_tools.block_card(
        call_id,
        simulate_failure=data.simulate_tool_failure,
    )
    duration_ms = round((time.perf_counter() - start) * 1000, 1)
    call_logger.latency.record_tool(duration_ms)

    if result.get("success"):
        await call_logger.emit("tool_result", {"tool": "block_card", "result": result, "durationMs": duration_ms})
        await call_logger.emit_latency()
        return result["message"]
    await call_logger.emit("tool_failure", {"tool": "block_card", "error": result.get("error")})
    await call_logger.emit("tool_result", {"tool": "block_card", "result": result, "durationMs": duration_ms})
    await call_logger.emit_latency()
    return result.get("error", "Unable to block card.")
