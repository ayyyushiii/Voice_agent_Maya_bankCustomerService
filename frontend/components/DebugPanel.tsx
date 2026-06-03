"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useCallStore } from "@/store/useCallStore";
import { formatMs } from "@/lib/utils";

function StateBadge({ label, state }: { label: string; state: string }) {
  const variant =
    state === "idle" ? "secondary" : state.includes("fail") ? "destructive" : "default";
  return (
    <div className="flex items-center justify-between py-1">
      <span className="text-sm text-muted-foreground">{label}</span>
      <Badge variant={variant}>{state}</Badge>
    </div>
  );
}

export function DebugPanel() {
  const {
    agentState,
    sttState,
    llmState,
    ttsState,
    currentTool,
    lastToolResult,
    latency,
    debugErrors,
    isAgentSpeaking,
  } = useCallStore();

  return (
    <Card>
      <CardHeader>
        <CardTitle>Debug Panel</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-1">
          <StateBadge label="Agent" state={agentState} />
          <StateBadge label="STT" state={sttState} />
          <StateBadge label="LLM" state={llmState} />
          <StateBadge label="TTS" state={ttsState} />
          <StateBadge label="Speaking" state={isAgentSpeaking ? "yes" : "no"} />
        </div>

        {currentTool && (
          <div>
            <p className="text-xs text-muted-foreground mb-1">Current Tool</p>
            <Badge>{currentTool}</Badge>
          </div>
        )}

        {lastToolResult != null && (
          <div>
            <p className="text-xs text-muted-foreground mb-1">Tool Result</p>
            <pre className="text-xs bg-muted p-2 rounded overflow-x-auto max-h-32">
              {JSON.stringify(lastToolResult, null, 2)}
            </pre>
          </div>
        )}

        <div>
          <p className="text-xs text-muted-foreground mb-2">Latency (last / avg)</p>
          <div className="grid grid-cols-2 gap-2 text-xs font-mono">
            {Object.entries(latency).map(([key, val]) => (
              <div key={key} className="bg-muted rounded p-2">
                <span className="uppercase text-muted-foreground">{key}</span>
                <p>{formatMs(val?.last ?? 0)} / {formatMs(val?.avg ?? 0)}</p>
              </div>
            ))}
            {Object.keys(latency).length === 0 && (
              <p className="text-muted-foreground col-span-2">No latency data yet</p>
            )}
          </div>
        </div>

        {debugErrors.length > 0 && (
          <div>
            <p className="text-xs text-destructive mb-1">Errors</p>
            <ul className="text-xs space-y-1">
              {debugErrors.map((e, i) => (
                <li key={i} className="text-destructive bg-destructive/10 p-1 rounded">{e}</li>
              ))}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
