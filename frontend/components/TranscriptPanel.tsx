"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useCallStore } from "@/store/useCallStore";
import { formatTimestamp } from "@/lib/utils";

export function TranscriptPanel() {
  const { partialTranscript, transcripts, isAgentSpeaking, agentState } = useCallStore();

  return (
    <Card className="h-full flex flex-col">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          Conversation
          {isAgentSpeaking && <Badge variant="success">Agent speaking</Badge>}
        </CardTitle>
      </CardHeader>
      <CardContent className="flex-1 overflow-y-auto max-h-[420px] space-y-3">
        {transcripts.length === 0 && !partialTranscript && (
          <p className="text-sm text-muted-foreground">Start a call to see the conversation...</p>
        )}

        {transcripts.map((entry) => (
          <div
            key={entry.id}
            className={`rounded-lg p-3 text-sm ${
              entry.role === "user"
                ? "bg-blue-50 dark:bg-blue-950/30 ml-4"
                : "bg-emerald-50 dark:bg-emerald-950/30 mr-4"
            }`}
          >
            <div className="flex items-center justify-between mb-1">
              <Badge variant={entry.role === "user" ? "default" : "success"}>
                {entry.role === "user" ? "You" : "Maya"}
              </Badge>
              <span className="text-xs text-muted-foreground">{formatTimestamp(entry.timestamp)}</span>
            </div>
            <p>{entry.text}</p>
          </div>
        ))}

        {partialTranscript && (
          <div className="rounded-lg p-3 text-sm bg-blue-50/50 border border-dashed border-blue-200 ml-4">
            <Badge variant="outline" className="mb-1">Partial</Badge>
            <p className="text-muted-foreground italic">{partialTranscript}</p>
          </div>
        )}

        {agentState === "speaking" && (
          <div className="rounded-lg p-3 text-sm bg-emerald-50/50 border border-dashed border-emerald-200 mr-4">
            <Badge variant="success" className="mb-1">Speaking</Badge>
            <p className="text-muted-foreground italic">Maya is responding...</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
