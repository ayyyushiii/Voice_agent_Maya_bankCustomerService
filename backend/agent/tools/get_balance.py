"""Account balance retrieval tool."""

from __future__ import annotations

import time

from livekit.agents import RunContext, function_tool

from agent.session_data import MayaSessionData
from services import banking_tools


@function_tool
async def get_balance(context: RunContext[MayaSessionData]) -> str:
    """Get account balance for verified customer."""
    data = context.userdata
    call_logger = data.call_logger
    call_id = data.call_id

    await call_logger.emit("tool_called", {"tool": "get_balance", "args": {}})
    start = time.perf_counter()

    result = banking_tools.get_balance(
        call_id,
        simulate_failure=data.simulate_tool_failure,
    )
    duration_ms = round((time.perf_counter() - start) * 1000, 1)
    call_logger.latency.record_tool(duration_ms)

    if result.get("success"):
        await call_logger.emit("tool_result", {"tool": "get_balance", "result": result, "durationMs": duration_ms})
        await call_logger.emit_latency()
        return f"Your account balance is {result['balance']} {result['currency']}."
    await call_logger.emit("tool_failure", {"tool": "get_balance", "error": result.get("error")})
    await call_logger.emit("tool_result", {"tool": "get_balance", "result": result, "durationMs": duration_ms})
    await call_logger.emit_latency()
    return result.get("error", "Unable to retrieve balance.")
