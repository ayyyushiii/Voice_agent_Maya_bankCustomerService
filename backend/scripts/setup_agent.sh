#!/usr/bin/env bash
# Maya agent — one-time setup and health check
set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/backend"

echo "==> Creating venv (if needed)..."
python3 -m venv venv 2>/dev/null || true
source venv/bin/activate

echo "==> Installing dependencies..."
pip install -q -r requirements.txt

echo "==> Loading environment..."
python - <<'PY'
import ssl_certs, env_setup, os, httpx
ssl_certs.configure_ssl_certs()
env_setup.load_project_env()

checks = []

def test(name, fn):
    try:
        fn()
        checks.append((name, True, "OK"))
    except Exception as e:
        checks.append((name, False, str(e)[:120]))

def openai_chat():
    r = httpx.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}", "Content-Type": "application/json"},
        json={"model": "gpt-4o", "messages": [{"role": "user", "content": "hi"}], "max_tokens": 5},
        timeout=20,
    )
    r.raise_for_status()

def deepgram():
    r = httpx.get(
        "https://api.deepgram.com/v1/projects",
        headers={"Authorization": f"Token {os.environ['DEEPGRAM_API_KEY']}"},
        timeout=15,
    )
    r.raise_for_status()

def elevenlabs():
    vid = os.getenv("ELEVENLABS_VOICE_ID", "EXAVITQu4vr4xnSDxMaL")
    r = httpx.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{vid}",
        headers={"xi-api-key": os.environ["ELEVEN_API_KEY"], "Content-Type": "application/json"},
        json={"text": "test", "model_id": "eleven_turbo_v2_5"},
        timeout=15,
    )
    r.raise_for_status()

def livekit():
    assert os.getenv("LIVEKIT_URL") and os.getenv("LIVEKIT_API_KEY")

def tools():
    from agent.tools import ALL_TOOLS
    import typing
    for t in ALL_TOOLS:
        typing.get_type_hints(t)

test("LiveKit env", livekit)
test("OpenAI GPT-4o chat", openai_chat)
test("Deepgram API", deepgram)
test("ElevenLabs TTS", elevenlabs)
test("Banking tools", tools)

print("\n=== Health Check ===")
all_ok = True
for name, ok, msg in checks:
    status = "PASS" if ok else "FAIL"
    print(f"  [{status}] {name}: {msg}")
    if not ok:
        all_ok = False

if not all_ok:
    print("\nFix failing checks before starting the agent.")
    exit(1)

print("\nAll checks passed. Start services in 3 terminals:")
print("  1. uvicorn server:app --reload --port 8000")
print("  2. python -m agent.main dev")
print("  3. cd ../frontend && npm run dev")
PY
