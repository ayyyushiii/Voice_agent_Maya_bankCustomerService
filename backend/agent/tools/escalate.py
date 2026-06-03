"""Human agent escalation tool."""

from __future__ import annotations

import time

from livekit.agents import RunContext, function_tool

from agent.session_data import MayaSessionData
from services import banking_tools


@function_tool
async def escalate(context: RunContext[MayaSessionData], reason: str) -> str:
    """Escalate the call to a human banking agent."""
    data = context.userdata
    call_logger = data.call_logger
    call_id = data.call_id

    await call_logger.emit("tool_called", {"tool": "escalate", "args": {"reason": reason}})
    start = time.perf_counter()

    result = banking_tools.escalate(
        call_id,
        reason,
        simulate_failure=data.simulate_tool_failure,
    )
    duration_ms = round((time.perf_counter() - start) * 1000, 1)
    call_logger.latency.record_tool(duration_ms)

    if result.get("success"):
        await call_logger.emit("tool_result", {"tool": "escalate", "result": result, "durationMs": duration_ms})
        await call_logger.emit_latency()
        return result["message"]
    await call_logger.emit("tool_failure", {"tool": "escalate", "error": result.get("error")})
    await call_logger.emit("tool_result", {"tool": "escalate", "result": result, "durationMs": duration_ms})
    await call_logger.emit_latency()
    return result.get("error", "Unable to escalate.")
