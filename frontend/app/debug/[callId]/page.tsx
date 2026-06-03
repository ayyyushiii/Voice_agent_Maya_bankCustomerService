"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft, Loader2 } from "lucide-react";
import { fetchCallLog, type CallLog } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { formatTimestamp, formatMs } from "@/lib/utils";

const EVENT_COLORS: Record<string, string> = {
  stt_final: "bg-cyan-600",
  tool_called: "bg-amber-500",
  tool_result: "bg-amber-600",
  call_ended: "bg-gray-600",
  interruption_detected: "bg-orange-500",
  silence_timeout: "bg-yellow-500",
};

export default function DebugReplayPage() {
  const params = useParams();
  const callId = params.callId as string;
  const [log, setLog] = useState<CallLog | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchCallLog(callId)
      .then(setLog)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [callId]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (error || !log) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-4">
        <p className="text-destructive">{error || "Call not found"}</p>
        <Link href="/" className="text-primary hover:underline flex items-center gap-1">
          <ArrowLeft className="h-4 w-4" /> Back to call
        </Link>
      </div>
    );
  }

  return (
    <main className="min-h-screen bg-slate-50 dark:bg-slate-950">
      <header className="border-b bg-white dark:bg-slate-900 px-4 py-4">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <div>
            <Link href="/" className="text-sm text-primary hover:underline flex items-center gap-1 mb-2">
              <ArrowLeft className="h-4 w-4" /> Back
            </Link>
            <h1 className="text-2xl font-bold">Call Replay</h1>
            <p className="font-mono text-sm text-muted-foreground">{log.callId}</p>
          </div>
          <div className="text-right text-sm">
            <p>Started: {formatTimestamp(log.startedAt)}</p>
            {log.endedAt && <p>Ended: {formatTimestamp(log.endedAt)}</p>}
          </div>
        </div>
      </header>

      <div className="max-w-5xl mx-auto px-4 py-6 space-y-6">
        {log.summary && (
          <Card>
            <CardHeader><CardTitle>Summary</CardTitle></CardHeader>
            <CardContent>
              <pre className="text-sm">{JSON.stringify(log.summary, null, 2)}</pre>
            </CardContent>
          </Card>
        )}

        <Card>
          <CardHeader><CardTitle>Transcript</CardTitle></CardHeader>
          <CardContent className="space-y-2">
            {log.transcripts.length === 0 ? (
              <p className="text-muted-foreground text-sm">No transcripts recorded</p>
            ) : (
              log.transcripts.map((t, i) => (
                <div key={i} className="text-sm border-l-2 border-primary pl-3 py-1">
                  <Badge variant="outline" className="mb-1">{t.type}</Badge>
                  <p>{t.text}</p>
                  <time className="text-xs text-muted-foreground">{formatTimestamp(t.timestamp)}</time>
                </div>
              ))
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Event Timeline</CardTitle></CardHeader>
          <CardContent>
            <ol className="space-y-2">
              {log.events.map((evt, i) => (
                <li key={i} className="flex items-start gap-2 text-sm">
                  <span className={`mt-1 h-2 w-2 rounded-full shrink-0 ${EVENT_COLORS[evt.event_type] || "bg-gray-400"}`} />
                  <div>
                    <span className="font-mono text-xs">{formatTimestamp(evt.timestamp)}</span>
                    <Badge variant="outline" className="ml-2 text-[10px]">{evt.event_type}</Badge>
                    {Object.keys(evt.payload).length > 0 && (
                      <pre className="text-[10px] text-muted-foreground mt-1">{JSON.stringify(evt.payload, null, 2)}</pre>
                    )}
                  </div>
                </li>
              ))}
            </ol>
          </CardContent>
        </Card>

        <div className="grid md:grid-cols-2 gap-4">
          <Card>
            <CardHeader><CardTitle>Latency</CardTitle></CardHeader>
            <CardContent>
              {Object.entries(log.latency).map(([key, val]) => (
                <div key={key} className="flex justify-between text-sm py-1">
                  <span className="uppercase">{key}</span>
                  <span className="font-mono">{formatMs(val.last)} / {formatMs(val.avg)}</span>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle>Tool Calls</CardTitle></CardHeader>
            <CardContent className="space-y-3">
              {log.toolCalls.length === 0 ? (
                <p className="text-sm text-muted-foreground">No tools called</p>
              ) : (
                log.toolCalls.map((tc, i) => (
                  <div key={i} className="text-sm border rounded p-2">
                    <Badge>{tc.tool}</Badge>
                    {tc.durationMs != null && (
                      <span className="ml-2 text-xs font-mono">{formatMs(tc.durationMs)}</span>
                    )}
                    {tc.result != null && (
                      <pre className="text-[10px] mt-1 overflow-x-auto">{JSON.stringify(tc.result, null, 2)}</pre>
                    )}
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        </div>

        {log.errors.length > 0 && (
          <Card>
            <CardHeader><CardTitle className="text-destructive">Errors</CardTitle></CardHeader>
            <CardContent>
              {log.errors.map((e, i) => (
                <pre key={i} className="text-sm text-destructive bg-destructive/10 p-2 rounded mb-2">
                  {JSON.stringify(e, null, 2)}
                </pre>
              ))}
            </CardContent>
          </Card>
        )}
      </div>
    </main>
  );
}
