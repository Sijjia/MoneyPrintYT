import React from "react";
import {
  AbsoluteFill,
  Easing,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { fontFamily } from "./theme";

export type RobloxTimelineProps = {
  events?: { year: string; label: string }[];
  title?: string;
  caption?: string;
  accent?: string;
};

const DEFAULT_EVENTS = [
  { year: "2003", label: "Прототип DynaBlocks" },
  { year: "2004", label: "Переименован в Roblox" },
  { year: "2006", label: "Публичный запуск" },
  { year: "2016", label: "Удаление Tix" },
  { year: "2017", label: "Удаление гостей" },
];

// Горизонтальный таймлайн истории Roblox: точки-годы появляются по очереди, линия «прорастает».
export const RobloxTimeline: React.FC<RobloxTimelineProps> = ({
  events = DEFAULT_EVENTS, title = "ХРОНОЛОГИЯ ROBLOX", caption = "", accent = "#00a2ff",
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames, width, height } = useVideoConfig();
  const exit = interpolate(frame, [durationInFrames - 12, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });
  const n = events.length;
  const x0 = 220, x1 = width - 220, span = x1 - x0;
  const perStep = Math.max(10, Math.floor((durationInFrames - 30) / n));
  const lineGrow = interpolate(frame, [10, 10 + perStep * n], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ background: "radial-gradient(ellipse at 50% 40%, #0a1420 0%, #060a12 60%, #04060a 100%)", fontFamily: fontFamily("oswald"), opacity: exit }}>
      <AbsoluteFill style={{ justifyContent: "flex-start", alignItems: "center", paddingTop: 90 }}>
        <div style={{ color: "#fff", fontSize: 50, fontWeight: 800, letterSpacing: 4, opacity: interpolate(frame, [4, 16], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) }}>{title}</div>
      </AbsoluteFill>

      <svg width={width} height={height} style={{ position: "absolute", inset: 0 }}>
        {/* базовая линия */}
        <line x1={x0} y1={height / 2} x2={x0 + span * lineGrow} y2={height / 2} stroke={accent} strokeWidth="5" />
        <line x1={x0} y1={height / 2} x2={x1} y2={height / 2} stroke={`${accent}22`} strokeWidth="5" />
        {events.map((e, i) => {
          const cx = x0 + (span * i) / (n - 1);
          const at = 10 + i * perStep;
          const app = interpolate(frame, [at, at + 10], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
          const up = i % 2 === 0;
          const cy = height / 2;
          const ly = up ? cy - 150 : cy + 60;
          return (
            <g key={i} opacity={app}>
              <line x1={cx} y1={cy} x2={cx} y2={up ? cy - 110 : cy + 40} stroke={accent} strokeWidth="3" />
              <circle cx={cx} cy={cy} r={14 * app} fill="#fff" stroke={accent} strokeWidth="4" />
              <text x={cx} y={ly} fill={accent} fontSize="52" fontWeight="800" textAnchor="middle" fontFamily="'Consolas', monospace">{e.year}</text>
              <text x={cx} y={ly + (up ? 44 : 44)} fill="#dfe" fontSize="26" fontWeight="500" textAnchor="middle" style={{ fontFamily: fontFamily("oswald") }}>{e.label}</text>
            </g>
          );
        })}
      </svg>

      {caption && (
        <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: 84,
          opacity: interpolate(frame, [22, 36], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) }) * exit }}>
          <div style={{ maxWidth: 1500, textAlign: "center", color: "#f4f1ea", fontSize: 44, fontWeight: 600, textShadow: "0 4px 24px rgba(0,0,0,0.9)", lineHeight: 1.15, borderLeft: `4px solid ${accent}`, borderRight: `4px solid ${accent}`, padding: "6px 34px" }}>{caption}</div>
        </AbsoluteFill>
      )}
      <AbsoluteFill style={{ boxShadow: "inset 0 0 280px rgba(0,0,0,0.85)", pointerEvents: "none" }} />
    </AbsoluteFill>
  );
};
