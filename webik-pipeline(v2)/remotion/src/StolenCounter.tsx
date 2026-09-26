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

export type StolenCounterProps = {
  value: number;            // целевое число
  prefix?: string;          // «$» / «»
  suffix?: string;          // « аккаунтов» / «»
  label: string;            // ЧТО это (УКРАДЕНО / УГНАНО / ШТРАФ)
  sub?: string;             // источник/пояснение мелким
  caption?: string;         // фраза снизу
  accent?: string;
};

const MONO = "'Consolas', 'Courier New', monospace";

// Резко в начале, замедление под конец (ease-out) — «ахуенный момент» на цифрах.
export const StolenCounter: React.FC<StolenCounterProps> = ({
  value, prefix = "", suffix = "", label, sub = "", caption = "", accent = "#e2231a",
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames, width, height } = useVideoConfig();
  const exit = interpolate(frame, [durationInFrames - 12, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });
  const boot = interpolate(frame, [0, 10], [0, 1], { extrapolateRight: "clamp" });

  const dur = Math.min(durationInFrames - 20, 46);
  const t = interpolate(frame, [8, 8 + dur], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
  const shown = Math.round(value * t);
  const done = t >= 0.999;
  const shownStr = prefix + shown.toLocaleString("ru-RU") + suffix;
  const punch = done ? 1 + 0.04 * Math.max(0, Math.sin((frame - (8 + dur)) * 0.5)) : 1;

  const flicker = 0.94 + 0.06 * Math.sin(frame * 1.6);
  const scanY = (frame * 7) % 100;

  return (
    <AbsoluteFill style={{ background: "radial-gradient(ellipse at 50% 42%, #17090a 0%, #0a0506 60%, #050303 100%)", fontFamily: MONO, opacity: exit }}>
      {/* «денежный дождь» из символов на фоне */}
      <AbsoluteFill style={{ opacity: 0.10 * boot }}>
        {Array.from({ length: Math.floor(width / 70) }, (_, c) => {
          const rows = Math.floor(height / 40) + 2;
          const off = (frame * (0.5 + random(`s${c}`) * 1.2) + random(`o${c}`) * rows) % rows;
          return (
            <div key={c} style={{ position: "absolute", left: c * 70 + 16, top: 0, color: accent, fontSize: 26, lineHeight: "40px" }}>
              {Array.from({ length: rows }, (_, r) => {
                const op = Math.max(0, 1 - Math.abs(r - off) / 4);
                return <div key={r} style={{ opacity: op }}>{["$", "₽", "R$", "#", prefix || "$"][Math.floor(random(`d${c}${r}`) * 5)]}</div>;
              })}
            </div>
          );
        })}
      </AbsoluteFill>

      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", opacity: boot * flicker }}>
        <div style={{ textAlign: "center" }}>
          <div style={{ color: accent, fontSize: 40, letterSpacing: 8, fontWeight: 700, textTransform: "uppercase", fontFamily: fontFamily("oswald") }}>
            {label}
          </div>
          <div style={{ color: "#fff", fontSize: 210, fontWeight: 800, lineHeight: 0.95, letterSpacing: -4, marginTop: 8,
            textShadow: `0 0 50px ${accent}aa`, transform: `scale(${punch})`, fontVariantNumeric: "tabular-nums" }}>
            {shownStr}
            <span style={{ color: accent, opacity: done ? 0 : 1 }}>_</span>
          </div>
          {sub && <div style={{ marginTop: 14, color: accent, fontSize: 30, letterSpacing: 3, opacity: 0.85, fontFamily: fontFamily("oswald") }}>{sub}</div>}
        </div>
      </AbsoluteFill>

      {caption && (
        <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: 90,
          opacity: interpolate(frame, [14, 30], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) }) * exit }}>
          <div style={{ maxWidth: 1500, textAlign: "center", color: "#f4f1ea", fontFamily: fontFamily("oswald"), fontSize: 48, fontWeight: 600, textShadow: "0 4px 24px rgba(0,0,0,0.9)", lineHeight: 1.15, borderLeft: `4px solid ${accent}`, borderRight: `4px solid ${accent}`, padding: "6px 34px" }}>
            {caption}
          </div>
        </AbsoluteFill>
      )}

      <AbsoluteFill style={{ background: "repeating-linear-gradient(0deg, rgba(0,0,0,0.28) 0px, rgba(0,0,0,0.28) 1px, transparent 3px, transparent 5px)", pointerEvents: "none" }} />
      <div style={{ position: "absolute", left: 0, right: 0, top: `${scanY}%`, height: 120, background: `linear-gradient(180deg, transparent, ${accent}10, transparent)`, pointerEvents: "none" }} />
      <AbsoluteFill style={{ boxShadow: "inset 0 0 300px rgba(0,0,0,0.9)", pointerEvents: "none" }} />
    </AbsoluteFill>
  );
};
