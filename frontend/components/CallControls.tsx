"use client";

import { useRef, useCallback, useEffect } from "react";
import { Phone, PhoneOff, Mic, MicOff, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useCallStore } from "@/store/useCallStore";
import { requestLiveKitToken, updateDebugFlags, endCall } from "@/lib/api";
import { connectToRoom, disconnectRoom, toggleMute } from "@/lib/livekit";
import { DebugSocket } from "@/lib/socket";
import { RoomEvent } from "livekit-client";

const statusVariant = {
  idle: "secondary" as const,
  connecting: "warning" as const,
  connected: "success" as const,
  disconnected: "outline" as const,
  error: "destructive" as const,
};

export function CallControls() {
  const socketRef = useRef<DebugSocket | null>(null);

  const {
    participantName,
    callId,
    roomName,
    room,
    connectionStatus,
    agentStatus,
    isMuted,
    isLoading,
    error,
    setParticipantName,
    setCallSession,
    setRoom,
    setConnectionStatus,
    setAgentStatus,
    setMuted,
    setAgentSpeaking,
    setLoading,
    setError,
    addEvent,
    resetCall,
  } = useCallStore();

  const startCall = useCallback(async () => {
    if (!participantName.trim()) {
      setError("Please enter your name");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const tokenData = await requestLiveKitToken(participantName.trim());
      setCallSession({
        callId: tokenData.call_id,
        roomName: tokenData.room_name,
        livekitUrl: tokenData.livekit_url,
        token: tokenData.token,
      });

      setAgentStatus("waiting");

      socketRef.current = new DebugSocket(tokenData.call_id, addEvent);
      socketRef.current.connect();

      const lkRoom = await connectToRoom({
        url: tokenData.livekit_url,
        token: tokenData.token,
        onConnectionChange: setConnectionStatus,
        onAgentSpeaking: setAgentSpeaking,
        onAgentJoined: () => setAgentStatus("online"),
        onError: setError,
      });

      setRoom(lkRoom);

      // Mark online if agent already in room (don't overwrite with "waiting")
      if (lkRoom.remoteParticipants.size > 0) {
        setAgentStatus("online");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start call");
      setConnectionStatus("error");
    } finally {
      setLoading(false);
    }
  }, [
    participantName,
    setParticipantName,
    setCallSession,
    setRoom,
    setConnectionStatus,
    setAgentStatus,
    setAgentSpeaking,
    setLoading,
    setError,
    addEvent,
  ]);

  // Detect agent joining after user is already connected
  useEffect(() => {
    if (!room || connectionStatus !== "connected") return;

    const markOnline = () => {
      if (room.remoteParticipants.size > 0) {
        setAgentStatus("online");
      }
    };

    markOnline();
    room.on(RoomEvent.ParticipantConnected, markOnline);
    room.on(RoomEvent.TrackSubscribed, markOnline);

    return () => {
      room.off(RoomEvent.ParticipantConnected, markOnline);
      room.off(RoomEvent.TrackSubscribed, markOnline);
    };
  }, [room, connectionStatus, setAgentStatus]);

  const handleEndCall = useCallback(async () => {
    socketRef.current?.disconnect();
    socketRef.current = null;
    await disconnectRoom(room);
    if (callId) await endCall(callId).catch(() => {});
    resetCall();
  }, [room, callId, resetCall]);

  const handleToggleMute = useCallback(async () => {
    const next = !isMuted;
    await toggleMute(room, next);
    setMuted(next);
  }, [room, isMuted, setMuted]);

  const inCall = connectionStatus === "connected" || connectionStatus === "connecting";

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>Call Controls</span>
          <Badge variant={statusVariant[connectionStatus]}>{connectionStatus}</Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Input
            placeholder="Your name"
            value={participantName}
            onChange={(e) => setParticipantName(e.target.value)}
            disabled={inCall}
          />
        </div>

        <div className="flex flex-wrap gap-2">
          {!inCall ? (
            <Button onClick={startCall} disabled={isLoading} className="gap-2">
              {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Phone className="h-4 w-4" />}
              Start Call
            </Button>
          ) : (
            <>
              <Button variant="outline" onClick={handleToggleMute} className="gap-2">
                {isMuted ? <MicOff className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
                {isMuted ? "Unmute" : "Mute"}
              </Button>
              <Button variant="destructive" onClick={handleEndCall} className="gap-2">
                <PhoneOff className="h-4 w-4" />
                End Call
              </Button>
            </>
          )}
        </div>

        <div className="grid grid-cols-2 gap-3 text-sm">
          <div>
            <span className="text-muted-foreground">Room</span>
            <p className="font-mono truncate">{roomName || "—"}</p>
          </div>
          <div>
            <span className="text-muted-foreground">Agent</span>
            <div className="mt-1">
              <Badge variant={agentStatus === "online" ? "success" : "secondary"}>{agentStatus}</Badge>
            </div>
          </div>
          <div>
            <span className="text-muted-foreground">Call ID</span>
            <p className="font-mono text-xs truncate">{callId || "—"}</p>
          </div>
        </div>

        {error && <p className="text-sm text-destructive">{error}</p>}
      </CardContent>
    </Card>
  );
}

export function DebugFailureToggles() {
  const { callId, failureFlags, setFailureFlags } = useCallStore();

  const toggle = async (key: keyof typeof failureFlags, value: boolean) => {
    setFailureFlags({ [key]: value });
    if (callId) {
      await updateDebugFlags(callId, { [key]: value }).catch(() => {});
    }
  };

  const flags = [
    { key: "stt_failure" as const, label: "STT Failure" },
    { key: "tts_failure" as const, label: "TTS Failure" },
    { key: "llm_failure" as const, label: "LLM Failure" },
    { key: "tool_failure" as const, label: "Tool Failure" },
    { key: "livekit_disconnect" as const, label: "LiveKit Disconnect" },
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm">Failure Simulation</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {flags.map(({ key, label }) => (
          <div key={key} className="flex items-center justify-between">
            <span className="text-sm">{label}</span>
            <button
              type="button"
              onClick={() => toggle(key, !failureFlags[key])}
              disabled={!callId}
              className={`h-6 w-11 rounded-full transition-colors ${failureFlags[key] ? "bg-destructive" : "bg-muted"} disabled:opacity-50`}
            >
              <span
                className={`block h-5 w-5 rounded-full bg-white shadow transition-transform ${failureFlags[key] ? "translate-x-5" : "translate-x-0.5"}`}
              />
            </button>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
