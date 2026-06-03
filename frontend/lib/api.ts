const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

export interface TokenResponse {
  token: string;
  room_name: string;
  livekit_url: string;
  call_id: string;
  participant_identity: string;
}

export interface CallLog {
  callId: string;
  startedAt: string;
  endedAt?: string;
  transcripts: Array<{ type: string; text: string; timestamp: string }>;
  events: DebugEvent[];
  latency: Record<string, { last: number; avg: number }>;
  toolCalls: Array<{
    tool: string;
    args?: Record<string, unknown>;
    result?: unknown;
    durationMs?: number;
    timestamp?: string;
  }>;
  errors: Array<{ type: string; detail: unknown; timestamp: string }>;
  summary?: Record<string, unknown>;
}

export interface DebugEvent {
  call_id: string;
  event_type: string;
  payload: Record<string, unknown>;
  timestamp: string;
}

export interface FailureFlags {
  stt_failure: boolean;
  tts_failure: boolean;
  llm_failure: boolean;
  tool_failure: boolean;
  livekit_disconnect: boolean;
}

export async function requestLiveKitToken(participantName: string): Promise<TokenResponse> {
  const res = await fetch(`${BACKEND_URL}/api/livekit/token`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ participant_name: participantName }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to get LiveKit token");
  }
  return res.json();
}

export async function fetchCallLog(callId: string): Promise<CallLog> {
  const res = await fetch(`${BACKEND_URL}/api/logs/calls/${callId}`);
  if (!res.ok) throw new Error("Call log not found");
  return res.json();
}

export async function fetchCallList(): Promise<Array<{ callId: string; startedAt: string; endedAt?: string; summary?: unknown }>> {
  const res = await fetch(`${BACKEND_URL}/api/logs/calls`);
  if (!res.ok) return [];
  const data = await res.json();
  return data.calls || [];
}

export async function updateDebugFlags(callId: string, flags: Partial<FailureFlags>): Promise<FailureFlags> {
  const res = await fetch(`${BACKEND_URL}/api/logs/debug/${callId}/flags`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(flags),
  });
  if (!res.ok) throw new Error("Failed to update debug flags");
  return res.json();
}

export async function endCall(callId: string): Promise<void> {
  await fetch(`${BACKEND_URL}/api/logs/calls/${callId}/end`, { method: "POST" });
}

export { BACKEND_URL };
