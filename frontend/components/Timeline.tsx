"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useCallStore } from "@/store/useCallStore";
import { formatTimestamp } from "@/lib/utils";

const EVENT_COLORS: Record<string, string> = {
  room_created: "bg-slate-500",
  user_joined: "bg-blue-500",
  agent_joined: "bg-emerald-500",
  stt_partial: "bg-cyan-400",
  stt_final: "bg-cyan-600",
  llm_started: "bg-purple-500",
  tool_called: "bg-amber-500",
  tool_result: "bg-amber-600",
  tts_started: "bg-pink-500",
  agent_speaking: "bg-pink-600",
  interruption_detected: "bg-orange-500",
  silence_timeout: "bg-yellow-500",
  tool_failure: "bg-red-500",
  disconnect: "bg-red-600",
  call_ended: "bg-gray-600",
  latency_update: "bg-indigo-400",
  error: "bg-red-700",
};

export function Timeline() {
  const events = useCallStore((s) => s.events);

  return (
    <Card className="h-full flex flex-col">
      <CardHeader>
        <CardTitle>Event Timeline</CardTitle>
      </CardHeader>
      <CardContent className="flex-1 overflow-y-auto max-h-[420px]">
        {events.length === 0 ? (
          <p className="text-sm text-muted-foreground">Events will appear here in realtime...</p>
        ) : (
          <ol className="relative border-l border-muted ml-2 space-y-3">
            {events.map((evt, i) => (
              <li key={`${evt.timestamp}-${i}`} className="ml-4">
                <span
                  className={`absolute -left-1.5 flex h-3 w-3 rounded-full ${EVENT_COLORS[evt.event_type] || "bg-gray-400"}`}
                />
                <div className="flex flex-wrap items-center gap-2">
                  <Badge variant="outline" className="font-mono text-[10px]">
                    {evt.event_type}
                  </Badge>
                  <time className="text-[10px] text-muted-foreground font-mono">
                    {formatTimestamp(evt.timestamp)}
                  </time>
                </div>
                {Object.keys(evt.payload).length > 0 && (
                  <pre className="text-[10px] text-muted-foreground mt-1 overflow-x-auto">
                    {JSON.stringify(evt.payload).slice(0, 120)}
                    {JSON.stringify(evt.payload).length > 120 ? "…" : ""}
                  </pre>
                )}
              </li>
            ))}
          </ol>
        )}
      </CardContent>
    </Card>
  );
}
