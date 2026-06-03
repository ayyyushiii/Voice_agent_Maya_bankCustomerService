# Architecture — Maya Banking Voice Agent

## Overview

Maya is a three-tier realtime voice AI system:

1. **Frontend** (Next.js) — user interface, LiveKit client, debug dashboard
2. **Backend** (FastAPI) — token server, banking APIs, event hub, call logs
3. **Agent** (LiveKit Agents SDK) — voice pipeline worker

All realtime audio flows through **LiveKit Cloud**. Debug metadata flows through the **FastAPI WebSocket hub**.

## Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        Browser (Next.js)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────────┐  │
│  │ CallControls │  │ Transcript   │  │ Debug / Timeline /    │  │
│  │              │  │ Panel        │  │ Latency Waterfall     │  │
│  └──────┬───────┘  └──────▲───────┘  └──────────▲────────────┘  │
│         │                 │                      │              │
│  ┌──────▼─────────────────┴──────────────────────┴──────────┐  │
│  │ Zustand Store + WebSocket (DebugSocket)                   │  │
│  └──────┬───────────────────────────────┬───────────────────┘  │
└─────────┼───────────────────────────────┼──────────────────────┘
          │ LiveKit SDK                   │ WS /api/logs/ws/{id}
          ▼                               ▼
┌─────────────────────┐         ┌─────────────────────────────┐
│   LiveKit Cloud     │◄───────►│   FastAPI Backend           │
│   (WebRTC rooms)    │         │   - Token generation        │
└─────────┬───────────┘         │   - Banking tools           │
          │                     │   - Event broadcast         │
          │                     │   - Call log persistence    │
          ▼                     └──────────────▲──────────────┘
┌─────────────────────┐                        │ HTTP POST events
│  Maya Agent Worker  │────────────────────────┘
│  - Deepgram STT     │
│  - GPT-4o LLM       │
│  - ElevenLabs TTS   │
│  - Banking tools    │
│  - Observability    │
└─────────────────────┘
```

## Voice Pipeline

```
User mic → LiveKit → Agent VAD/STT (Deepgram)
                          ↓
                    Final transcript
                          ↓
                    GPT-4o reasoning
                          ↓
              ┌───────────┴───────────┐
              │                       │
         Tool calls              Direct reply
    (verify, balance, etc.)           │
              │                       │
              └───────────┬───────────┘
                          ↓
                  ElevenLabs TTS
                          ↓
              Agent audio → LiveKit → User speakers
```

## Event Flow

1. Agent emits structured events via `CallLogger.emit()`
2. Events POST to `POST /api/logs/events`
3. Backend broadcasts to WebSocket subscribers for that `callId`
4. Events append to in-memory call log
5. On `call_ended`, log persists to `{LOG_DIR}/{callId}.json`

### Event Types

| Event | Source | Purpose |
|-------|--------|---------|
| `room_created` | Agent | Room initialized |
| `user_joined` | Agent | User participant connected |
| `agent_joined` | Agent | Maya connected |
| `stt_partial` | Agent | Interim transcription |
| `stt_final` | Agent | Final user utterance |
| `llm_started` | Agent | Model inference began |
| `tool_called` | Agent | Banking tool invoked |
| `tool_result` | Agent | Tool response received |
| `tts_started` | Agent | Speech synthesis began |
| `agent_speaking` | Agent | Audio playback active |
| `interruption_detected` | Agent | User barged in |
| `silence_timeout` | Agent | 10s+ silence detected |
| `tool_failure` | Agent | Tool returned error |
| `disconnect` | Agent | Room disconnected |
| `call_ended` | Agent/Backend | Call finalized |

## Verification Model

Verification state is stored **per call** in `services/user_db.py`:

- `verify_user(phone, birth_year)` marks the call as verified
- `get_balance` and `block_card` reject unverified calls with HTTP 403 / tool error
- State resets when call ends (in-memory; not persisted across calls)

## Agent Dispatch

When the frontend requests a token:

1. Backend creates room name `maya-bank-{callId}`
2. Backend dispatches agent `maya-bank-agent` via LiveKit Agent Dispatch API
3. Running agent worker receives job and joins the room

## Security

- LiveKit API secret **never** sent to browser
- Tokens are short-lived JWTs with room-scoped grants
- Sensitive account data only returned after verification
- Phone numbers partially masked in debug events

## Scalability Notes

Current implementation uses in-memory event hub and verification state — suitable for demo/assignment. Production would use Redis for pub/sub and session state, plus S3 for call log storage.
