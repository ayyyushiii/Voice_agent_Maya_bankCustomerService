import { BACKEND_URL, type DebugEvent } from "./api";

export type EventHandler = (event: DebugEvent) => void;

export class DebugSocket {
  private ws: WebSocket | null = null;
  private callId: string;
  private handler: EventHandler;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private closed = false;

  constructor(callId: string, handler: EventHandler) {
    this.callId = callId;
    this.handler = handler;
  }

  connect(): void {
    const wsUrl = BACKEND_URL.replace(/^http/, "ws");
    this.ws = new WebSocket(`${wsUrl}/api/logs/ws/${this.callId}`);

    this.ws.onopen = () => {
      this.ws?.send("ping");
    };

    this.ws.onmessage = (msg) => {
      if (msg.data === "pong") return;
      try {
        const event: DebugEvent = JSON.parse(msg.data);
        this.handler(event);
      } catch {
        // ignore malformed
      }
    };

    this.ws.onclose = () => {
      if (!this.closed) {
        this.reconnectTimer = setTimeout(() => this.connect(), 2000);
      }
    };
  }

  disconnect(): void {
    this.closed = true;
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    this.ws?.close();
    this.ws = null;
  }
}
