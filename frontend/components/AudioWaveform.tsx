"use client";

import { useEffect, useRef } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useCallStore } from "@/store/useCallStore";

export function AudioWaveform() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animRef = useRef<number>(0);
  const { room, isAgentSpeaking, connectionStatus } = useCallStore();

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const w = canvas.width;
    const h = canvas.height;
    let phase = 0;

    const draw = () => {
      ctx.clearRect(0, 0, w, h);
      ctx.fillStyle = "#0f172a";
      ctx.fillRect(0, 0, w, h);

      const active = connectionStatus === "connected";
      const amplitude = isAgentSpeaking ? 40 : active ? 15 : 5;
      const bars = 32;
      const barW = w / bars - 2;

      for (let i = 0; i < bars; i++) {
        const barH =
          amplitude *
          (0.3 + 0.7 * Math.abs(Math.sin(phase + i * 0.4))) *
          (active ? 1 : 0.3);
        const x = i * (barW + 2);
        const y = (h - barH) / 2;

        const gradient = ctx.createLinearGradient(0, y, 0, y + barH);
        if (isAgentSpeaking) {
          gradient.addColorStop(0, "#10b981");
          gradient.addColorStop(1, "#059669");
        } else if (active) {
          gradient.addColorStop(0, "#3b82f6");
          gradient.addColorStop(1, "#1d4ed8");
        } else {
          gradient.addColorStop(0, "#64748b");
          gradient.addColorStop(1, "#475569");
        }

        ctx.fillStyle = gradient;
        ctx.beginPath();
        ctx.roundRect(x, y, barW, barH, 2);
        ctx.fill();
      }

      phase += isAgentSpeaking ? 0.15 : 0.05;
      animRef.current = requestAnimationFrame(draw);
    };

    draw();
    return () => cancelAnimationFrame(animRef.current);
  }, [room, isAgentSpeaking, connectionStatus]);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm">Audio Activity</CardTitle>
      </CardHeader>
      <CardContent>
        <canvas ref={canvasRef} width={320} height={80} className="w-full rounded-md" />
      </CardContent>
    </Card>
  );
}
