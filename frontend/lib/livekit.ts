import {
  Room,
  RoomEvent,
  Track,
  ConnectionState,
  RemoteParticipant,
} from "livekit-client";

export type ConnectionStatus = "idle" | "connecting" | "connected" | "disconnected" | "error";

export interface LiveKitConnectOptions {
  url: string;
  token: string;
  onConnectionChange?: (status: ConnectionStatus) => void;
  onAgentSpeaking?: (speaking: boolean) => void;
  onAgentJoined?: () => void;
  onError?: (error: Error) => void;
}

function attachAgentAudio(track: Track, participant: RemoteParticipant) {
  if (track.kind !== Track.Kind.Audio) return;
  const el = track.attach();
  el.id = `agent-audio-${participant.identity}`;
  document.body.appendChild(el);
}

export async function connectToRoom(
  options: LiveKitConnectOptions
): Promise<Room> {
  const room = new Room({
    adaptiveStream: true,
    dynacast: true,
  });

  room.on(RoomEvent.ConnectionStateChanged, (state: ConnectionState) => {
    const map: Record<ConnectionState, ConnectionStatus> = {
      [ConnectionState.Disconnected]: "disconnected",
      [ConnectionState.Connecting]: "connecting",
      [ConnectionState.Connected]: "connected",
      [ConnectionState.Reconnecting]: "connecting",
      [ConnectionState.SignalReconnecting]: "connecting",
    };
    options.onConnectionChange?.(map[state] ?? "idle");
  });

  room.on(RoomEvent.TrackSubscribed, (track, _publication, participant) => {
    if (participant.identity !== room.localParticipant.identity) {
      attachAgentAudio(track, participant);
      options.onAgentJoined?.();
    }
  });

  room.on(RoomEvent.ParticipantConnected, (participant) => {
    if (participant.identity !== room.localParticipant.identity) {
      options.onAgentJoined?.();
    }
  });

  room.on(RoomEvent.ActiveSpeakersChanged, (speakers) => {
    const agentSpeaking = speakers.some(
      (s) => s.identity !== room.localParticipant.identity
    );
    options.onAgentSpeaking?.(agentSpeaking);
  });

  try {
    options.onConnectionChange?.("connecting");
    await room.connect(options.url, options.token);
    await room.localParticipant.setMicrophoneEnabled(true);
    options.onConnectionChange?.("connected");

    // Agent may already be in the room
    for (const participant of room.remoteParticipants.values()) {
      options.onAgentJoined?.();
      participant.trackPublications.forEach((pub) => {
        if (pub.track) attachAgentAudio(pub.track, participant);
      });
    }

    return room;
  } catch (err) {
    options.onConnectionChange?.("error");
    options.onError?.(err instanceof Error ? err : new Error(String(err)));
    throw err;
  }
}

export async function disconnectRoom(room: Room | null): Promise<void> {
  if (!room) return;
  room.removeAllListeners();
  await room.disconnect();
  document.querySelectorAll('[id^="agent-audio-"]').forEach((el) => el.remove());
}

export async function toggleMute(room: Room | null, muted: boolean): Promise<void> {
  if (!room) return;
  await room.localParticipant.setMicrophoneEnabled(!muted);
}

export function getAgentParticipant(room: Room | null): RemoteParticipant | undefined {
  if (!room) return undefined;
  return Array.from(room.remoteParticipants.values()).find(
    (p) => p.identity.includes("agent") || p.name?.toLowerCase().includes("maya")
  );
}
