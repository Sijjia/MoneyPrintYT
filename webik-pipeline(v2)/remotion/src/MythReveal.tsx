import React from "react";
import {
  AbsoluteFill,
  Easing,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
  random,
} from "remotion";
import { fontFamily } from "./theme";

export type MythRevealProps = {
  mythLabel?: string;       // «МИФ» / «ЛЕГЕНДА» / «СЛУХ»
  truthLabel?: string;      // «ПРАВДА» / «НА ДЕЛЕ»
  myth: string;            // что якобы было
  truth: string;           // что на самом деле
  subject?: string;        // «Bigfoot» / «Ratman» — крупная подпись объекта
  caption?: string;         // фраза снизу
  accent?: string;
};

// Честное разоблачение игрового мифа: сверху «МИФ» (глитч, вопросы) → переворот → «ПРАВДА».
export const MythReveal: React.FC<MythRevealProps> = ({
  mythLabel = "МИФ", truthLabel = "ПРАВДА", myth, truth, subject = "", caption = "",
  accent = "#c8161d",
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames, width, height } = useVideoConfig();
  const exit = interpolate(frame, [durationInFrames - 12, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });
  const boot = interpolate(frame, [0, 10], [0, 1], { extrapolateRight: "clamp" });

  const revealAt = Math.round(durationInFrames * 0.5);
  const isTruth = frame >= revealAt;
  const glitch = frame >= revealAt - 6 && frame < revealAt + 8;
  const gx = glitch ? (random(`g${frame}`) - 0.5) * 34 : 0;
  const scanY = (frame * 7) % 100;

  const col = isTruth ? "#39d98a" : accent;
  const label = isTruth ? truthLabel : mythLabel;
  const text = isTruth ? truth : myth;
  const flick = isTruth ? 1 : 0.88 + 0.12 * Math.sin(frame * 1.9);

  return (
    <AbsoluteFill style={{ background: isTruth ? "#04120a" : "#120406", fontFamily: fontFamily("oswald"), opacity: exit, overflow: "hidden" }}>
      {/* фон: до правды — «помехи/вопросы», после — сетка */}
      <AbsoluteFill style={{ opacity: 0.12 * boot }}>
        <svg width={width} height={height}>
          {Array.from({ length: 16 }).map((_, i) => (
            <line key={i} x1="0" y1={i * (height / 16)} x2={width} y2={i * (height / 16)} stroke={col} strokeWidth="0.5" opacity="0.3" />
          ))}
        </svg>
        {!isTruth && Array.from({ length: 40 }).map((_, i) => (
          <div key={i} style={{ position: "absolute", left: `${random(`qx${i}`) * 92 + 2}%`, top: `${random(`qy${i}`) * 88 + 4}%`, color: accent, fontSize: 30 + random(`qs${i}`) * 40, opacity: 0.3 }}>?</div>
        ))}
      </AbsoluteFill>

      {/* скан-лайны */}
      <AbsoluteFill style={{ background: "repeating-linear-gradient(0deg, rgba(0,0,0,0.35) 0px, rgba(0,0,0,0.35) 1px, transparent 3px, transparent 5px)", pointerEvents: "none" }} />

      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", padding: 130, opacity: boot * flick }}>
        <div style={{ textAlign: "center", transform: `translateX(${gx}px)` }}>
          {subject && <div style={{ color: "#fff", fontSize: 96, fontWeight: 800, letterSpacing: 1, marginBottom: 10, textShadow: `0 0 30px ${col}88` }}>{subject}</div>}
          {/* штамп МИФ/ПРАВДА */}
          <div style={{ display: "inline-block", color: "#fff", background: col, fontSize: 60, fontWeight: 800, letterSpacing: 8, padding: "8px 40px", transform: "rotate(-2deg)", boxShadow: `0 0 40px ${col}`, marginBottom: 30 }}>
            {label}
          </div>
          <div style={{ color: isTruth ? "#eafff4" : "#ffdede", fontSize: 52, fontWeight: 600, lineHeight: 1.18, maxWidth: 1500, margin: "0 auto",
            opacity: interpolate(frame, [isTruth ? revealAt + 4 : 8, isTruth ? revealAt + 16 : 20], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) }}>
            {text}
          </div>
        </div>
      </AbsoluteFill>

      {caption && (
        <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: 84,
          opacity: interpolate(frame, [20, 36], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) }) * exit }}>
          <div style={{ maxWidth: 1500, textAlign: "center", color: "#f4f1ea", fontSize: 44, fontWeight: 600, textShadow: "0 4px 24px rgba(0,0,0,0.9)", lineHeight: 1.15, borderLeft: `4px solid ${col}`, borderRight: `4px solid ${col}`, padding: "6px 34px" }}>{caption}</div>
        </AbsoluteFill>
      )}

      <div style={{ position: "absolute", left: 0, right: 0, top: `${scanY}%`, height: 110, background: `linear-gradient(180deg, transparent, ${col}12, transparent)`, pointerEvents: "none" }} />
      {glitch && <div style={{ position: "absolute", left: 0, right: 0, top: `${random(`gy${frame}`) * 70 + 12}%`, height: 10 + random(`gh${frame}`) * 30, background: "#39d98a", opacity: 0.3, mixBlendMode: "screen", transform: `translateX(${gx * 2}px)` }} />}
      <AbsoluteFill style={{ boxShadow: "inset 0 0 280px rgba(0,0,0,0.9)", pointerEvents: "none" }} />
    </AbsoluteFill>
  );
};
