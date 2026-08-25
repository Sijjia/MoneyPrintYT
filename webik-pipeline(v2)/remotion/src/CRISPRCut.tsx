import React from "react";
import { AbsoluteFill, Easing, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { fontFamily } from "./theme";

export type CRISPRCutProps = {
  title?: string;
  sub?: string;
  accent?: string;
};

// Cas9 находит участок ДНК, разрезает его — яркая вспышка в точке разреза,
// затем «редактирует» основание (смена цвета). Молекулярно, чисто.
export const CRISPRCut: React.FC<CRISPRCutProps> = ({
  title = "CRISPR",
  sub = "редактирование гена",
  accent = "#1fa48a",
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames, width, height } = useVideoConfig();
  const intro = interpolate(frame, [0, 20], [0, 1], { extrapolateRight: "clamp" });
  const exit = interpolate(frame, [durationInFrames - 16, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });
  const titleIn = interpolate(frame, [16, 36], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  const midY = height * 0.5;
  const rungs = 40;
  const cutIdx = 20;
  const xAt = (i: number) => width * 0.08 + i * ((width * 0.84) / (rungs - 1));
  const cutX = xAt(cutIdx);

  const approach = interpolate(frame, [16, 54], [0, 1], { easing: Easing.out(Easing.cubic), extrapolateRight: "clamp" });
  const casY = interpolate(approach, [0, 1], [-140, midY - 96]);
  const cutT = interpolate(frame, [58, 70], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const flash = interpolate(frame, [58, 64, 78], [0, 1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const gap = 26 * cutT;                              // расхождение концов
  const edited = interpolate(frame, [84, durationInFrames - 30], [0, 1], { extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ fontFamily: fontFamily("oswald"), opacity: exit }}>
      <AbsoluteFill style={{ background: "radial-gradient(ellipse at 50% 50%, #0a1f24 0%, #06120f 55%, #03080a 100%)" }} />
      <AbsoluteFill style={{ opacity: intro }}>
        <svg width={width} height={height} style={{ position: "absolute" }}>
          {Array.from({ length: rungs }).map((_, i) => {
            const past = i >= cutIdx;
            const shift = past ? gap : -gap;
            const x = xAt(i) + (i === cutIdx ? 0 : shift * 0.15);
            const ph = i * 0.5 + frame * 0.04;
            const yA = midY + Math.sin(ph) * 34;
            const yB = midY - Math.sin(ph) * 34;
            const isEdit = i === cutIdx + 3;
            const col = isEdit ? (edited > 0.5 ? "#e0a020" : accent) : "#2f4d49";
            return (
              <g key={i}>
                <line x1={x} y1={yA} x2={x} y2={yB} stroke={col} strokeWidth={isEdit ? 6 : 3}
                  style={isEdit ? { filter: `drop-shadow(0 0 10px ${col})` } : undefined}
                  opacity={0.5 + (isEdit ? 0.5 : 0.35)} />
                <circle cx={x} cy={yA} r={isEdit ? 7 : 4} fill={isEdit ? "#fff" : "#4b6f6a"} />
                <circle cx={x} cy={yB} r={isEdit ? 7 : 4} fill={isEdit ? "#fff" : "#4b6f6a"} />
              </g>
            );
          })}
          {/* вспышка разреза */}
          <circle cx={cutX} cy={midY} r={10 + flash * 44} fill={accent} opacity={flash * 0.7}
            style={{ filter: `drop-shadow(0 0 26px ${accent})` }} />
          <line x1={cutX} y1={midY - 60} x2={cutX} y2={midY + 60} stroke="#eafcf6" strokeWidth={2} opacity={flash} />

          {/* Cas9 — белковый блоб с направляющей РНК */}
          <g transform={`translate(${cutX}, ${casY})`} opacity={approach}
             style={{ filter: `drop-shadow(0 0 20px ${accent})` }}>
            <path d="M -70 0 Q -70 -60 0 -60 Q 70 -60 70 0 Q 60 60 0 66 Q -60 60 -70 0 Z"
              fill="#0e2f2b" stroke={accent} strokeWidth={3} />
            {/* направляющая РНК — свисающая волнистая нить (не «улыбка») */}
            <path d="M -6 44 q -12 12 2 24 q 12 10 -2 24 q -10 10 3 22" stroke="#7fe9d4" strokeWidth={2.6} fill="none" opacity={0.85} />
            <text x="0" y="6" fill="#7fe9d4" fontSize="26" fontWeight={800} textAnchor="middle"
              style={{ fontFamily: fontFamily("oswald") }}>Cas9</text>
          </g>
        </svg>
      </AbsoluteFill>
      <AbsoluteFill style={{ boxShadow: "inset 0 0 300px rgba(0,0,0,0.8)", pointerEvents: "none" }} />
      <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "flex-start", padding: 84, opacity: titleIn * exit }}>
        <div>
          <div style={{ color: "#eafcf6", fontSize: 104, fontWeight: 800, letterSpacing: 4, textShadow: `0 0 34px ${accent}` }}>{title}</div>
          <div style={{ color: accent, fontSize: 38, fontWeight: 700, letterSpacing: 3, textTransform: "uppercase" }}>{sub}</div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
