"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useCallStore } from "@/store/useCallStore";
import { formatMs } from "@/lib/utils";

const STAGES = [
  { key: "stt", label: "STT", color: "bg-cyan-500" },
  { key: "llm", label: "LLM", color: "bg-purple-500" },
  { key: "tool", label: "Tool", color: "bg-amber-500" },
  { key: "tts", label: "TTS", color: "bg-pink-500" },
  { key: "e2e", label: "E2E", color: "bg-indigo-500" },
];

export function LatencyWaterfall() {
  const latency = useCallStore((s) => s.latency);

  const maxMs = Math.max(
    ...STAGES.map((s) => latency[s.key]?.last ?? 0),
    1
  );

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm">Latency Waterfall</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {STAGES.map(({ key, label, color }) => {
          const val = latency[key]?.last ?? 0;
          const pct = Math.min(100, (val / maxMs) * 100);
          return (
            <div key={key}>
              <div className="flex justify-between text-xs mb-1">
                <span>{label}</span>
                <span className="font-mono">{formatMs(val)}</span>
              </div>
              <div className="h-3 bg-muted rounded-full overflow-hidden">
                <div
                  className={`h-full ${color} rounded-full transition-all duration-500`}
                  style={{ width: `${pct}%` }}
                />
              </div>
            </div>
          );
        })}

        <div className="pt-2 border-t text-xs text-muted-foreground">
          <p>End-to-end = user speech → agent audio playback</p>
        </div>
      </CardContent>
    </Card>
  );
}
