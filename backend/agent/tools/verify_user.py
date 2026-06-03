"""User identity verification tool."""

from __future__ import annotations

import time

from livekit.agents import RunContext, function_tool

from agent.session_data import MayaSessionData
from services import banking_tools


@function_tool
async def verify_user(
    context: RunContext[MayaSessionData],
    phone: str,
    birth_year: str,
) -> str:
    """Verify customer identity using registered phone number and birth year."""
    data = context.userdata
    call_logger = data.call_logger
    call_id = data.call_id

    await call_logger.emit("tool_called", {"tool": "verify_user", "args": {"phone": phone[-4:] + "****"}})
    start = time.perf_counter()

    result = banking_tools.verify_user(
        call_id,
        phone,
        birth_year,
        simulate_failure=data.simulate_tool_failure,
    )
    duration_ms = round((time.perf_counter() - start) * 1000, 1)
    call_logger.latency.record_tool(duration_ms)

    if result.get("success"):
        data.verified = True
        await call_logger.emit("tool_result", {"tool": "verify_user", "result": result, "durationMs": duration_ms})
    else:
        await call_logger.emit("tool_failure", {"tool": "verify_user", "error": result.get("error")})
        await call_logger.emit("tool_result", {"tool": "verify_user", "result": result, "durationMs": duration_ms})

    await call_logger.emit_latency()
    if result.get("success"):
        return result["message"]
    return f"Verification failed: {result.get('error', 'Unknown error')}"
