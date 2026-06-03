"""Load .env and normalize API key names for LiveKit plugins."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

_BACKEND_ROOT = Path(__file__).resolve().parent


def load_project_env() -> None:
    """Load env files and map assignment names to plugin-expected names."""
    # override=True ensures .env wins over stale shell/worker env vars
    load_dotenv(_BACKEND_ROOT / ".env", override=True)
    load_dotenv(_BACKEND_ROOT.parent / ".env", override=True)

    # LiveKit ElevenLabs plugin expects ELEVEN_API_KEY, not ELEVENLABS_API_KEY
    if not os.getenv("ELEVEN_API_KEY") and os.getenv("ELEVENLABS_API_KEY"):
        os.environ["ELEVEN_API_KEY"] = os.environ["ELEVENLABS_API_KEY"]
