import { create } from "zustand";
import type { Room } from "livekit-client";
import type { ConnectionStatus } from "@/lib/livekit";
import type { DebugEvent, FailureFlags } from "@/lib/api";

export interface TranscriptEntry {
  id: string;
  role: "user" | "agent";
  text: string;
  isPartial: boolean;
  timestamp: string;
}

export interface CallState {
  participantName: string;
  callId: string | null;
  roomName: string | null;
  livekitUrl: string | null;
  token: string | null;
  room: Room | null;
  connectionStatus: ConnectionStatus;
  agentStatus: string;
  isMuted: boolean;
  isAgentSpeaking: boolean;
  isLoading: boolean;
  error: string | null;

  // Transcripts
  partialTranscript: string;
  transcripts: TranscriptEntry[];
  currentAgentResponse: string;

  // Debug
  events: DebugEvent[];
  agentState: string;
  sttState: string;
  llmState: string;
  ttsState: string;
  currentTool: string | null;
  lastToolResult: unknown;
  latency: Record<string, { last: number; avg: number }>;
  debugErrors: string[];
  failureFlags: FailureFlags;

  setParticipantName: (name: string) => void;
  setCallSession: (data: {
    callId: string;
    roomName: string;
    livekitUrl: string;
    token: string;
  }) => void;
  setRoom: (room: Room | null) => void;
  setConnectionStatus: (status: ConnectionStatus) => void;
  setAgentStatus: (status: string) => void;
  setMuted: (muted: boolean) => void;
  setAgentSpeaking: (speaking: boolean) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  addEvent: (event: DebugEvent) => void;
  setFailureFlags: (flags: Partial<FailureFlags>) => void;
  resetCall: () => void;
}

const defaultFlags: FailureFlags = {
  stt_failure: false,
  tts_failure: false,
  llm_failure: false,
  tool_failure: false,
  livekit_disconnect: false,
};

export const useCallStore = create<CallState>((set, get) => ({
  participantName: "",
  callId: null,
  roomName: null,
  livekitUrl: null,
  token: null,
  room: null,
  connectionStatus: "idle",
  agentStatus: "offline",
  isMuted: false,
  isAgentSpeaking: false,
  isLoading: false,
  error: null,

  partialTranscript: "",
  transcripts: [],
  currentAgentResponse: "",

  events: [],
  agentState: "idle",
  sttState: "idle",
  llmState: "idle",
  ttsState: "idle",
  currentTool: null,
  lastToolResult: null,
  latency: {},
  debugErrors: [],
  failureFlags: { ...defaultFlags },

  setParticipantName: (name) => set({ participantName: name }),

  setCallSession: (data) =>
    set({
      callId: data.callId,
      roomName: data.roomName,
      livekitUrl: data.livekitUrl,
      token: data.token,
    }),

  setRoom: (room) => set({ room }),
  setConnectionStatus: (status) => set({ connectionStatus: status }),
  setAgentStatus: (status) => set({ agentStatus: status }),
  setMuted: (muted) => set({ isMuted: muted }),
  setAgentSpeaking: (speaking) => set({ isAgentSpeaking: speaking }),
  setLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error }),

  setFailureFlags: (flags) =>
    set((s) => ({ failureFlags: { ...s.failureFlags, ...flags } })),

  addEvent: (event) => {
    const state = get();
    const updates: Partial<CallState> = {
      events: [...state.events, event].slice(-200),
    };

    switch (event.event_type) {
      case "stt_partial":
        updates.partialTranscript = String(event.payload.text || "");
        updates.sttState = "listening";
        break;
      case "stt_final": {
        const text = String(event.payload.text || "");
        updates.partialTranscript = "";
        updates.sttState = "idle";
        updates.transcripts = [
          ...state.transcripts,
          {
            id: `user-${event.timestamp}`,
            role: "user",
            text,
            isPartial: false,
            timestamp: event.timestamp,
          },
        ];
        break;
      }
      case "llm_started":
        updates.llmState = "thinking";
        break;
      case "tts_started":
        updates.ttsState = "generating";
        break;
      case "agent_speaking":
        updates.ttsState = "speaking";
        updates.agentState = "speaking";
        break;
      case "agent_state":
        updates.agentState = String(event.payload.state || "unknown");
        if (event.payload.state === "listening") {
          updates.llmState = "idle";
          updates.ttsState = "idle";
        }
        break;
      case "tool_called":
        updates.currentTool = String(event.payload.tool || "");
        updates.llmState = "tool_call";
        break;
      case "tool_result":
        updates.lastToolResult = event.payload.result;
        updates.currentTool = String(event.payload.tool || state.currentTool);
        updates.llmState = "idle";
        break;
      case "tool_failure":
        updates.debugErrors = [
          ...state.debugErrors,
          String(event.payload.error || "Tool failure"),
        ].slice(-20);
        break;
      case "latency_update":
        updates.latency = event.payload as Record<string, { last: number; avg: number }>;
        break;
      case "interruption_detected":
        updates.agentState = "interrupted";
        break;
      case "agent_joined":
        updates.agentStatus = "online";
        break;
      case "error":
        updates.debugErrors = [
          ...state.debugErrors,
          String(event.payload.message || event.payload.component || "Error"),
        ].slice(-20);
        break;
      case "call_ended":
        updates.agentStatus = "ended";
        updates.connectionStatus = "disconnected";
        break;
      default:
        break;
    }

    set(updates);
  },

  resetCall: () =>
    set({
      callId: null,
      roomName: null,
      livekitUrl: null,
      token: null,
      room: null,
      connectionStatus: "idle",
      agentStatus: "offline",
      isMuted: false,
      isAgentSpeaking: false,
      isLoading: false,
      error: null,
      partialTranscript: "",
      transcripts: [],
      currentAgentResponse: "",
      events: [],
      agentState: "idle",
      sttState: "idle",
      llmState: "idle",
      ttsState: "idle",
      currentTool: null,
      lastToolResult: null,
      latency: {},
      debugErrors: [],
      failureFlags: { ...defaultFlags },
    }),
}));
