"""Branch hours lookup — no verification required."""

from __future__ import annotations

import time

from livekit.agents import RunContext, function_tool

from agent.session_data import MayaSessionData
from services import banking_tools


@function_tool
async def get_branch_hours(context: RunContext[MayaSessionData]) -> str:
    """Get branch operating hours."""
    data = context.userdata
    call_logger = data.call_logger

    await call_logger.emit("tool_called", {"tool": "get_branch_hours", "args": {}})
    start = time.perf_counter()

    result = banking_tools.get_branch_hours()
    duration_ms = round((time.perf_counter() - start) * 1000, 1)
    call_logger.latency.record_tool(duration_ms)

    await call_logger.emit(
        "tool_result", {"tool": "get_branch_hours", "result": result, "durationMs": duration_ms}
    )
    await call_logger.emit_latency()
    return f"Our branches are open {result['branchHours']}."
