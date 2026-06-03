# Known Issues

## Agent dispatch timing

If the agent worker is not running when the user starts a call, dispatch may succeed but no agent joins until the worker starts. **Always start the agent before testing calls.**

## Browser autoplay

Some browsers block agent audio until user interaction. Clicking **Start Call** satisfies this requirement.

## WebSocket reconnection

The debug WebSocket auto-reconnects on disconnect but may briefly miss events during reconnection windows.

## Simulated failures

- **LLM failure** is checked at agent startup only — toggle before starting the call.
- **STT/TTS failure** toggles are stored but full pipeline injection requires agent restart for some failure modes.
- **LiveKit disconnect** toggle is stored; manual disconnect via End Call is the reliable test path.

## Python 3.14 compatibility

LiveKit Agents SDK is tested primarily on Python 3.11–3.12. Python 3.14 may have compatibility issues with some dependencies. Use Python 3.11 or 3.12 if you encounter install errors.

## Call log persistence

Logs persist on `call_ended` event. If the agent crashes without emitting `call_ended`, in-memory events may be lost (though partial data remains in the event buffer until backend restart).

## ElevenLabs voice

Default voice ID (`21m00Tcm4TlvDq8ikWAM`) is ElevenLabs "Rachel". Ensure your ElevenLabs plan supports the chosen voice.

## CORS / WebSocket URL

Frontend derives WebSocket URL by replacing `http` with `ws` in `NEXT_PUBLIC_BACKEND_URL`. If backend is behind HTTPS, ensure WSS is configured correctly.
