"""
Maya — LiveKit realtime banking voice agent.

Pipeline: speech → Deepgram STT → GPT-4o → banking tools → ElevenLabs TTS

Run: cd backend && python -m agent.main dev
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import ssl_certs

ssl_certs.configure_ssl_certs()

import env_setup

env_setup.load_project_env()

import asyncio
import json
import logging
import time
from typing import Optional

import httpx
from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    WorkerOptions,
    cli,
)
from livekit.plugins import deepgram, openai

# Ensure backend root is on path for services imports
_BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

env_setup.load_project_env()

from agent.observability.events import EventType
from agent.observability.logger import CallLogger
from agent.session_data import MayaSessionData
from agent.tools import ALL_TOOLS
from agent.tts_factory import build_tts

logger = logging.getLogger("maya.agent")

PROMPT_PATH = Path(__file__).parent / "prompts" / "maya_bank_agent.md"
SILENCE_PROMPT_SECONDS = 10.0


def load_instructions() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def extract_call_id(room_name: str) -> str:
    if room_name.startswith("maya-bank-"):
        return room_name.replace("maya-bank-", "", 1)
    return room_name


async def fetch_debug_flags(call_id: str) -> dict:
    backend = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{backend}/api/logs/debug/{call_id}/flags")
            if resp.status_code == 200:
                return resp.json()
    except Exception as exc:
        logger.warning("Could not fetch debug flags: %s", exc)
    return {}


class MayaBankAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=load_instructions(),
            tools=ALL_TOOLS,
        )

    async def on_enter(self) -> None:
        data: MayaSessionData = self.session.userdata
        await data.call_logger.emit(EventType.LLM_STARTED, {"purpose": "greeting"})
        await data.call_logger.emit(EventType.TTS_STARTED, {})
        await self.session.say(
            "Hello! I'm Maya from customer support. How can I help you today?",
            allow_interruptions=True,
        )


async def _silence_monitor(session: AgentSession, data: MayaSessionData) -> None:
    """Prompt on 10s silence; end call on second consecutive silence."""
    while True:
        await asyncio.sleep(1.0)
        elapsed = time.monotonic() - data.last_activity
        if elapsed < SILENCE_PROMPT_SECONDS:
            continue
        if session.agent_state == "speaking":
            continue

        data.silence_count += 1
        data.last_activity = time.monotonic()

        if data.silence_count == 1:
            await data.call_logger.emit(
                EventType.SILENCE_TIMEOUT,
                {"count": 1, "message": "Are you still there?"},
            )
            await session.say("Are you still there?", allow_interruptions=True)
        else:
            await data.call_logger.emit(
                EventType.SILENCE_TIMEOUT,
                {"count": 2, "message": "Ending call due to inactivity"},
            )
            await session.say(
                "I haven't heard from you, so I'll end this call. You can call back anytime. Goodbye!",
                allow_interruptions=False,
            )
            await data.call_logger.end_call(
                {"status": "ended", "reason": "silence_timeout", "silenceCount": data.silence_count}
            )
            await session.aclose()
            break


def _touch_activity(data: MayaSessionData) -> None:
    data.last_activity = time.monotonic()
    data.silence_count = 0


async def entrypoint(ctx: JobContext) -> None:
    # Job subprocess may not inherit env — reload on every call
    env_setup.load_project_env()

    await ctx.connect()

    room_name = ctx.room.name
    call_id = extract_call_id(room_name)
    call_logger = CallLogger(call_id)

    flags = await fetch_debug_flags(call_id)
    data = MayaSessionData(
        call_id=call_id,
        call_logger=call_logger,
        simulate_tool_failure=flags.get("tool_failure", False),
        simulate_stt_failure=flags.get("stt_failure", False),
        simulate_tts_failure=flags.get("tts_failure", False),
        simulate_llm_failure=flags.get("llm_failure", False),
    )

    await call_logger.emit(EventType.ROOM_CREATED, {"room": room_name})
    await call_logger.emit(EventType.AGENT_JOINED, {"agent": "Maya"})

    openai_api_key = os.getenv("OPENAI_API_KEY")
    deepgram_api_key = os.getenv("DEEPGRAM_API_KEY")

    session = AgentSession[MayaSessionData](
        stt=deepgram.STT(model="nova-2-general", api_key=deepgram_api_key),
        llm=openai.LLM(model="gpt-4o", api_key=openai_api_key),
        tts=build_tts(),
        userdata=data,
    )

    @session.on("user_input_transcribed")
    def on_transcript(ev) -> None:
        _touch_activity(data)
        call_logger.latency.start_e2e()
        text = getattr(ev, "transcript", "") or ""
        is_final = getattr(ev, "is_final", False)
        if is_final:
            call_logger.latency.end_stt()
            asyncio.create_task(
                call_logger.emit(EventType.STT_FINAL, {"text": text})
            )
        else:
            call_logger.latency.start_stt()
            asyncio.create_task(
                call_logger.emit(EventType.STT_PARTIAL, {"text": text})
            )

    @session.on("agent_state_changed")
    def on_agent_state(ev) -> None:
        state = ev.new_state if hasattr(ev, "new_state") else str(ev)
        state_str = state.value if hasattr(state, "value") else str(state)
        asyncio.create_task(
            call_logger.emit("agent_state", {"state": state_str})
        )
        if state_str == "speaking":
            call_logger.latency.start_tts()
            asyncio.create_task(call_logger.emit(EventType.AGENT_SPEAKING, {}))
        elif state_str == "listening":
            call_logger.latency.end_tts()
            call_logger.latency.end_e2e()
            asyncio.create_task(call_logger.emit_latency())

    @session.on("user_state_changed")
    def on_user_state(ev) -> None:
        state = ev.new_state if hasattr(ev, "new_state") else str(ev)
        state_str = state.value if hasattr(state, "value") else str(state)
        if state_str == "speaking":
            _touch_activity(data)

    @session.on("overlapping_speech")
    def on_interrupted(ev) -> None:
        asyncio.create_task(
            call_logger.emit(
                EventType.INTERRUPTION_DETECTED,
                {"message": "User interrupted agent speech"},
            )
        )

    @session.on("error")
    def on_session_error(ev) -> None:
        err = getattr(ev, "error", ev)
        msg = str(err)
        if "insufficient_quota" in msg.lower():
            msg = (
                "OpenAI quota exceeded. Add credits at "
                "https://platform.openai.com/account/billing"
            )
        elif "elevenlabs" in msg.lower() or "websocket connection closed" in msg.lower():
            msg = (
                "ElevenLabs TTS connection dropped. Restart the agent; "
                "fallback OpenAI TTS will be used if available."
            )
        asyncio.create_task(
            call_logger.emit(EventType.ERROR, {"component": "pipeline", "message": msg})
        )

    @ctx.room.on("participant_connected")
    def on_participant(participant) -> None:
        meta = participant.metadata or "{}"
        try:
            parsed = json.loads(meta)
        except json.JSONDecodeError:
            parsed = {}
        asyncio.create_task(
            call_logger.emit(
                EventType.USER_JOINED,
                {"identity": participant.identity, "name": participant.name, "meta": parsed},
            )
        )

    @ctx.room.on("disconnected")
    def on_disconnect() -> None:
        asyncio.create_task(call_logger.emit(EventType.DISCONNECT, {}))

    # Detect remote participants joining (user)
    for p in ctx.room.remote_participants.values():
        asyncio.create_task(
            call_logger.emit(
                EventType.USER_JOINED,
                {"identity": p.identity, "name": p.name},
            )
        )

    data.silence_task = asyncio.create_task(_silence_monitor(session, data))

    agent = MayaBankAgent()

    try:
        if data.simulate_llm_failure:
            await call_logger.emit(EventType.ERROR, {"component": "llm", "simulated": True})
            raise RuntimeError("Simulated LLM failure")

        await session.start(agent=agent, room=ctx.room)
    except Exception as exc:
        logger.exception("Agent session error")
        await call_logger.emit(EventType.ERROR, {"message": str(exc)})
        await call_logger.end_call({"status": "error", "error": str(exc)})
    finally:
        if data.silence_task and not data.silence_task.done():
            data.silence_task.cancel()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            agent_name="maya-bank-agent",
        )
    )
