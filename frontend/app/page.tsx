"use client";

import Link from "next/link";
import { Headphones } from "lucide-react";
import { CallControls, DebugFailureToggles } from "@/components/CallControls";
import { TranscriptPanel } from "@/components/TranscriptPanel";
import { DebugPanel } from "@/components/DebugPanel";
import { Timeline } from "@/components/Timeline";
import { LatencyWaterfall } from "@/components/LatencyWaterfall";
import { AudioWaveform } from "@/components/AudioWaveform";
import { useCallStore } from "@/store/useCallStore";

export default function HomePage() {
  const callId = useCallStore((s) => s.callId);

  return (
    <main className="min-h-screen bg-gradient-to-b from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900">
      <header className="border-b bg-white/80 dark:bg-slate-950/80 backdrop-blur sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-full bg-primary flex items-center justify-center">
              <Headphones className="h-5 w-5 text-primary-foreground" />
            </div>
            <div>
              <h1 className="text-xl font-bold">Maya</h1>
              <p className="text-xs text-muted-foreground">Banking Voice Agent</p>
            </div>
          </div>
          {callId && (
            <Link
              href={`/debug/${callId}`}
              className="text-sm text-primary hover:underline"
            >
              View call replay →
            </Link>
          )}
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 py-6 grid grid-cols-1 lg:grid-cols-12 gap-4">
        <div className="lg:col-span-3 space-y-4">
          <CallControls />
          <AudioWaveform />
          <LatencyWaterfall />
          <DebugFailureToggles />
        </div>

        <div className="lg:col-span-5">
          <TranscriptPanel />
        </div>

        <div className="lg:col-span-4 space-y-4">
          <DebugPanel />
          <Timeline />
        </div>
      </div>
    </main>
  );
}
