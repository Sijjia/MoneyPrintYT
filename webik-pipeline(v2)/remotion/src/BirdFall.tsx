import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { fontFamily } from "./theme";
import { ease, enterUp } from "./anim";

export type BirdFallProps = {
  kicker?: string;
  title?: string;
  strip?: string;       // «strip 1.5 km × 200 m»
  accent?: string;
  caption?: string;
  durationInFrames?: number;
};

const rnd = (i: number, s = 1) => { const x = Math.sin(i * 29.3 + s * 5.7) * 43758.5; return x - Math.floor(x); };

// Джатинга: безлунная ночь, узкая полоса земли у деревни, огни внизу дезориентируют птиц —
// силуэты-«галочки» спиралью падают вниз к огням. Туман.
export const BirdFall: React.FC<BirdFallProps> = ({
  kicker = "JATINGA",
  title = "THE VILLAGE WHERE BIRDS FALL FROM THE SKY",
  strip = "strip 1.5 km × 200 m",
  accent = "#7fa8d8",
  caption = "",
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const exit = interpolate(frame, [durationInFrames - 16, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });
  const appear = interpolate(frame, [0, 28], [0, 1], { extrapolateRight: "clamp", easing: ease.expoOut });

  return (
    <AbsoluteFill style={{ fontFamily: fontFamily("oswald"), opacity: exit, overflow: "hidden" }}>
      <AbsoluteFill style={{ background: "linear-gradient(180deg,#070b14 0%,#0a1120 42%,#0e1a2c 72%,#1a2436 100%)" }} />
      {/* деревенские огни внизу (полоса) */}
      <AbsoluteFill style={{ opacity: appear }}>
        {Array.from({ length: 40 }).map((_, i) => {
          const x = 360 + (i / 40) * 1200 + rnd(i, 2) * 20;
          const fl = 0.5 + 0.5 * Math.sin((frame + i * 8) / 9);
          return <div key={i} style={{ position: "absolute", left: x, top: 900 + rnd(i, 3) * 60, width: 6, height: 6, borderRadius: "50%",
            background: "#ffd98a", boxShadow: `0 0 ${8 + fl * 10}px #ffb44a`, opacity: 0.5 + fl * 0.4 }} />;
        })}
        {/* обозначение узкой полосы */}
        <div style={{ position: "absolute", left: 360, right: 360, bottom: 120, height: 2, background: `${accent}66`, opacity: appear }} />
        <div style={{ position: "absolute", left: 360, bottom: 128, color: accent, fontSize: 22, letterSpacing: 2, opacity: appear * 0.8 }}>{strip}</div>
      </AbsoluteFill>

      {/* туман */}
      <AbsoluteFill style={{ background: "radial-gradient(ellipse at 50% 85%, rgba(120,150,190,0.14), transparent 55%)", pointerEvents: "none" }} />

      {/* падающие птицы — спираль вниз к огням */}
      <svg width={1920} height={1080} viewBox="0 0 1920 1080" style={{ position: "absolute", inset: 0, opacity: appear }}>
        {Array.from({ length: 34 }).map((_, i) => {
          const life = ((frame * (2.4 + rnd(i, 5) * 1.6) + rnd(i, 1) * 600) % 620);
          const p = life / 620;
          const startX = 400 + rnd(i, 2) * 1120;
          const x = startX + Math.sin(p * 10 + i) * (60 * (1 - p));   // спираль сужается
          const y = 120 + p * 780;
          const rot = Math.sin(frame / 4 + i) * 40 + p * 120;
          const o = interpolate(p, [0, 0.1, 0.85, 1], [0, 0.9, 0.9, 0]);
          const wing = Math.abs(Math.sin((frame + i * 6) / 3)) * 10 + 4;
          return (
            <g key={i} transform={`translate(${x},${y}) rotate(${rot})`} opacity={o}>
              <path d={`M-14,0 Q0,${-wing} 0,0 Q0,${-wing} 14,0`} fill="none" stroke="#0a0d12" strokeWidth="3.5" />
              <path d={`M-14,0 Q0,${-wing} 0,0 Q0,${-wing} 14,0`} fill="none" stroke={accent} strokeWidth="1.4" opacity="0.5" />
            </g>
          );
        })}
      </svg>

      <AbsoluteFill style={{ justifyContent: "flex-start", alignItems: "flex-start", padding: "78px 90px", opacity: exit }}>
        {(() => { const k = enterUp(frame, 30, 2, 26); const t = enterUp(frame, 30, 8, 42, { stiffness: 125, damping: 18 }); return (<>
          <div style={{ color: accent, fontSize: 30, fontWeight: 700, letterSpacing: 10, opacity: k.opacity, transform: `translateY(${k.translateY}px)` }}>{kicker}</div>
          <div style={{ color: "#e8f0fb", fontSize: 66, fontWeight: 700, lineHeight: 1.02, maxWidth: 1150, textShadow: "0 6px 30px rgba(0,0,0,0.85)", marginTop: 6, opacity: t.opacity, transform: `translateY(${t.translateY}px)` }}>{title}</div>
        </>); })()}
      </AbsoluteFill>

      {caption && (
        <div style={{ position: "absolute", left: 0, right: 0, bottom: 62, textAlign: "center", padding: "0 200px",
          color: "#dbe6f3", fontSize: 32, fontWeight: 500, textShadow: "0 4px 22px rgba(0,0,0,0.95)", fontFamily: fontFamily("montserrat"),
          opacity: interpolate(frame, [34, 48], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) * exit }}>{caption}</div>
      )}
      <AbsoluteFill style={{ boxShadow: "inset 0 0 300px rgba(0,0,0,0.82)", pointerEvents: "none" }} />
    </AbsoluteFill>
  );
};
