"""TTS factory — ElevenLabs primary with OpenAI fallback."""

from __future__ import annotations

import os

from livekit.agents.tts import FallbackAdapter, TTS
from livekit.plugins import elevenlabs, openai


def build_tts() -> TTS:
    voice_id = os.getenv("ELEVENLABS_VOICE_ID", "EXAVITQu4vr4xnSDxMaL")
    eleven_key = os.getenv("ELEVEN_API_KEY") or os.getenv("ELEVENLABS_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    providers: list[TTS] = [
        elevenlabs.TTS(
            voice_id=voice_id,
            api_key=eleven_key,
            model="eleven_turbo_v2_5",
            auto_mode=True,
            inactivity_timeout=300,
        ),
    ]

    if openai_key:
        providers.append(
            openai.TTS(
                model="gpt-4o-mini-tts",
                voice="alloy",
                api_key=openai_key,
            )
        )

    if len(providers) == 1:
        return providers[0]

    return FallbackAdapter(tts=providers, max_retry_per_tts=2)
