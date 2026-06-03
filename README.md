# Maya — Realtime Banking Voice Agent

A production-style browser-based realtime banking customer support voice agent. Users join a LiveKit room from the browser; **Maya** (AI voice agent) joins the same room, listens, reasons with GPT-4o, calls banking tools, and responds with synthesized voice — with full debug observability in the UI.

## Architecture

```
Browser (Next.js)  ←→  LiveKit Cloud  ←→  Maya Agent (Python)
       ↓                                        ↓
  FastAPI Backend  ←—— WebSocket events ————→  Observability
       ↓
  Call Logs (JSON replay)
```

**Pipeline:** Speech → Deepgram STT → GPT-4o (+ tools) → ElevenLabs TTS → Audio playback

## Prerequisites

- Node.js 18+
- Python 3.11+
- Accounts: [LiveKit Cloud](https://cloud.livekit.io), [OpenAI](https://platform.openai.com), [Deepgram](https://deepgram.com), [ElevenLabs](https://elevenlabs.io)

## Environment Variables

Copy and fill in credentials:

```bash
cp backend/.env.example .env
cp frontend/.env.local.example frontend/.env.local
```

| Variable | Description |
|----------|-------------|
| `LIVEKIT_URL` | LiveKit Cloud WebSocket URL (`wss://...`) |
| `LIVEKIT_API_KEY` | LiveKit API key |
| `LIVEKIT_API_SECRET` | LiveKit API secret (server-only, never exposed to browser) |
| `OPENAI_API_KEY` | OpenAI API key for GPT-4o |
| `DEEPGRAM_API_KEY` | Deepgram STT API key |
| `ELEVENLABS_API_KEY` | ElevenLabs TTS API key |
| `ELEVENLABS_VOICE_ID` | ElevenLabs voice ID (default: Rachel) |
| `BACKEND_URL` | Backend URL (default: `http://localhost:8000`) |
| `FRONTEND_URL` | Frontend URL for CORS (default: `http://localhost:3000`) |
| `LOG_DIR` | Call log directory (default: `./backend/agent/call_logs`) |
| `NEXT_PUBLIC_BACKEND_URL` | Frontend → backend URL |

## LiveKit Setup

1. Create a project at [cloud.livekit.io](https://cloud.livekit.io)
2. Copy **URL**, **API Key**, and **API Secret** into `.env`
3. Register agent name `maya-bank-agent` (matches `agent/main.py`)

## OpenAI Setup

1. Create an API key at [platform.openai.com](https://platform.openai.com)
2. Set `OPENAI_API_KEY` in `.env`
3. Agent uses **GPT-4o** for reasoning and tool calling

## Deepgram Setup

1. Sign up at [deepgram.com](https://deepgram.com)
2. Create an API key → `DEEPGRAM_API_KEY`
3. Agent uses **nova-2-general** model for realtime STT

## ElevenLabs Setup

1. Sign up at [elevenlabs.io](https://elevenlabs.io)
2. Create API key → `ELEVENLABS_API_KEY`
3. Pick a voice ID → `ELEVENLABS_VOICE_ID`

## Quick Start

### 1. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn server:app --reload --port 8000
```

### 2. Agent (separate terminal)

```bash
cd backend
source venv/bin/activate
python -m agent.main dev
```

### 3. Frontend (separate terminal)

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000), enter your name, and click **Start Call**.

## Mock Test User

| Field | Value |
|-------|-------|
| Phone | `9999999999` |
| Birth Year | `1990` |
| Name | Rahul Sharma |
| Balance | ₹52,430 |
| Card Last 4 | 4321 |

**Verification is required** before balance or card blocking.

## Features

- **Call controls** — start/end call, mute/unmute, connection & agent status
- **Live transcript** — partial STT, final user speech, agent speaking indicator
- **Debug panel** — agent/STT/LLM/TTS state, tool calls, latency, errors
- **Event timeline** — realtime chronological events with timestamps
- **Latency waterfall** — STT, LLM, TTS, tool, end-to-end metrics
- **Interruption (barge-in)** — user can interrupt Maya mid-speech
- **Silence handling** — 10s → "Are you still there?"; second timeout → graceful end
- **Failure simulation** — debug toggles for STT/TTS/LLM/tool/LiveKit failures
- **Call replay** — `/debug/[callId]` loads persisted JSON logs

## Banking Tools

| Tool | Verification Required |
|------|----------------------|
| `verify_user` | No (uses phone + birth year) |
| `get_balance` | Yes |
| `block_card` | Yes |
| `create_complaint` | No (works unverified) |
| `escalate` | No |
| `get_branch_hours` | No |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/livekit/token` | Generate LiveKit token + dispatch agent |
| POST | `/api/bank/verify` | Verify customer identity |
| POST | `/api/bank/balance` | Get account balance |
| POST | `/api/bank/block-card` | Block debit card |
| POST | `/api/bank/complaint` | Register complaint |
| POST | `/api/bank/escalate` | Escalate to human |
| GET | `/api/bank/branch-hours` | Branch hours |
| POST | `/api/logs/events` | Ingest debug events |
| WS | `/api/logs/ws/{callId}` | Realtime event stream |
| GET | `/api/logs/calls/{callId}` | Fetch call log for replay |

## Latency Tracking

Each conversation turn tracks:

- **STT** — speech end → final transcript
- **LLM** — transcript → model response / tool decision
- **Tool** — tool invocation duration
- **TTS** — text → first audio byte
- **E2E** — user speech → agent audio playback

Metrics appear in the Debug Panel and Latency Waterfall, and are persisted in call logs.

## Interruption Handling

LiveKit Agents supports barge-in by default. When the user speaks while Maya is talking:

1. Agent speech is interrupted
2. `interruption_detected` event is logged
3. Maya adapts to the new user input

## Project Structure

See [docs/architecture.md](docs/architecture.md) for detailed architecture.

## Test Scenarios

See [docs/test_scenarios.md](docs/test_scenarios.md) for manual test cases.

## Known Issues

See [docs/known_issues.md](docs/known_issues.md).

## License

MIT — assignment / demo project.
# Voice_agent_Maya_bankCustomerService
