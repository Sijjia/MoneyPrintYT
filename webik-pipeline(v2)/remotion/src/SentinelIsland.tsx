import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { fontFamily } from "./theme";
import { ease, enterUp } from "./anim";

export type SentinelIslandProps = {
  kicker?: string;
  title?: string;
  bufferText?: string;  // «5 км буферная зона»
  accent?: string;
  caption?: string;
  durationInFrames?: number;
};

// Северный Сентинел: тёмное море сверху, силуэт острова, красное кольцо 5-км буфера, стрелы летят
// в приближающуюся лодку. «Последнее неконтактное племя».
export const SentinelIsland: React.FC<SentinelIslandProps> = ({
  kicker = "NORTH SENTINEL",
  title = "THE ISLAND YOU CANNOT SET FOOT ON",
  bufferText = "exclusion zone · 5 km buffer",
  accent = "#e0483a",
  caption = "",
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const exit = interpolate(frame, [durationInFrames - 16, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });
  const appear = interpolate(frame, [0, 28], [0, 1], { extrapolateRight: "clamp", easing: ease.expoOut });
  const ringDash = -(frame * 1.4) % 40;
  // лодка приближается, потом отступает (стрелы)
  const boat = interpolate(frame % 150, [0, 70, 90, 150], [0, 1, 1, 0], { extrapolateRight: "clamp" });
  const bx = 1400 - boat * 300, by = 720 - boat * 120;

  return (
    <AbsoluteFill style={{ fontFamily: fontFamily("oswald"), opacity: exit, overflow: "hidden" }}>
      <AbsoluteFill style={{ background: "radial-gradient(ellipse at 50% 45%, #08131c 0%, #06101a 55%, #030a10 100%)" }} />
      {/* блики моря */}
      <AbsoluteFill style={{ opacity: appear * 0.5 }}>
        {Array.from({ length: 60 }).map((_, i) => {
          const x = (i * 137.5) % 1920, y = 120 + ((i * 91.7) % 900);
          return <div key={i} style={{ position: "absolute", left: x, top: y, width: 20, height: 2, background: "rgba(90,140,180,0.15)",
            transform: `translateY(${Math.sin((frame + i * 20) / 30) * 3}px)` }} />;
        })}
      </AbsoluteFill>

      <svg width={1920} height={1080} viewBox="0 0 1920 1080" style={{ position: "absolute", inset: 0, opacity: appear }}>
        {/* 5-км буфер — пульсирующее кольцо */}
        <circle cx="820" cy="560" r="440" fill="none" stroke={accent} strokeWidth="3" strokeDasharray="14 26" strokeDashoffset={ringDash} opacity="0.55" />
        <circle cx="820" cy="560" r="440" fill={accent} opacity={0.04 + 0.03 * Math.sin(frame / 20)} />
        {/* остров-силуэт */}
        <path d="M620,560 Q640,470 760,450 Q900,430 980,500 Q1050,560 990,640 Q900,720 780,700 Q650,680 620,560 Z" fill="#0d1a12" stroke="#1c3a26" strokeWidth="2" />
        {/* джунгли-штрихи */}
        {Array.from({ length: 30 }).map((_, i) => {
          const a = (i / 30) * Math.PI * 2; const rx = 820 + Math.cos(a) * (90 + (i % 4) * 20); const ry = 560 + Math.sin(a) * (70 + (i % 3) * 16);
          return <path key={i} d={`M${rx},${ry} l0,-16`} stroke="#1f4a30" strokeWidth="3" opacity="0.6" />;
        })}
        {/* лодка */}
        <g transform={`translate(${bx},${by})`} opacity={boat}>
          <path d="M-30,0 q30,16 60,0 l-8,10 q-22,8 -44,0 Z" fill="#5a4a34" />
        </g>
        {/* стрелы летят в лодку */}
        {boat > 0.4 && Array.from({ length: 7 }).map((_, i) => {
          const p = ((frame + i * 9) % 40) / 40;
          const sx = 900 + p * (bx - 900); const sy = 600 + p * (by - 600);
          return <g key={i} transform={`translate(${sx},${sy}) rotate(${Math.atan2(by - 600, bx - 900) * 57})`} opacity={0.8 * boat}>
            <line x1="-14" y1="0" x2="8" y2="0" stroke={accent} strokeWidth="2" /><path d="M8,0 l-6,-3 M8,0 l-6,3" stroke={accent} strokeWidth="2" />
          </g>;
        })}
      </svg>

      <AbsoluteFill style={{ justifyContent: "flex-start", alignItems: "flex-start", padding: "78px 90px", opacity: exit }}>
        {(() => { const k = enterUp(frame, 30, 2, 26); const t = enterUp(frame, 30, 8, 42, { stiffness: 125, damping: 18 }); return (<>
          <div style={{ color: accent, fontSize: 30, fontWeight: 700, letterSpacing: 8, opacity: k.opacity, transform: `translateY(${k.translateY}px)` }}>{kicker}</div>
          <div style={{ color: "#eaf2f6", fontSize: 68, fontWeight: 700, lineHeight: 1.02, maxWidth: 1100, textShadow: "0 6px 30px rgba(0,0,0,0.85)", marginTop: 6, opacity: t.opacity, transform: `translateY(${t.translateY}px)` }}>{title}</div>
          <div style={{ marginTop: 16, color: accent, fontSize: 24, fontWeight: 700, letterSpacing: 3, border: `2px solid ${accent}`, padding: "6px 16px", borderRadius: 4,
            opacity: interpolate(frame, [30, 44], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) }}>⛔ {bufferText}</div>
        </>); })()}
      </AbsoluteFill>

      {caption && (
        <div style={{ position: "absolute", left: 0, right: 0, bottom: 60, textAlign: "center", padding: "0 200px",
          color: "#dce8ee", fontSize: 32, fontWeight: 500, textShadow: "0 4px 22px rgba(0,0,0,0.95)", fontFamily: fontFamily("montserrat"),
          opacity: interpolate(frame, [36, 50], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) * exit }}>{caption}</div>
      )}
      <AbsoluteFill style={{ boxShadow: "inset 0 0 300px rgba(0,0,0,0.82)", pointerEvents: "none" }} />
    </AbsoluteFill>
  );
};
