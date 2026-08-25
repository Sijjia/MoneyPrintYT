import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { fontFamily } from "./theme";

export type RatioViz17Props = {
  title?: string;
  ratio?: string;
  women?: number;
  accent?: string;
};

// 17 женских фигур + 1 мужская (светится) — визуал неолитического «мужского горлышка».
export const RatioViz17: React.FC<RatioViz17Props> = ({
  title = "17 ЖЕНЩИН НА 1 МУЖЧИНУ",
  ratio = "17 : 1",
  women = 17,
  accent = "#1fa48a",
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames, width, height, fps } = useVideoConfig();
  const intro = interpolate(frame, [0, 18], [0, 1], { extrapolateRight: "clamp" });
  const exit = interpolate(frame, [durationInFrames - 16, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });

  const total = women + 1;
  const cols = 6;
  const rows = Math.ceil(total / cols);
  const cw = width * 0.62 / cols;
  const gx = (width * 0.62) / cols;
  const startX = width * 0.06;
  const startY = height * 0.26;
  const malePulse = 1 + Math.sin(frame / 8) * 0.06;

  const figs = Array.from({ length: total }).map((_, i) => {
    const male = i === 3; // мужская — заметная позиция
    const c = i % cols, r = Math.floor(i / cols);
    return { x: startX + c * gx + gx / 2, y: startY + r * (height * 0.5 / rows), male };
  });

  return (
    <AbsoluteFill style={{ fontFamily: fontFamily("oswald"), opacity: exit }}>
      <AbsoluteFill style={{ background: "radial-gradient(ellipse at 40% 45%, #0a1f24 0%, #06110f 60%, #03080a 100%)" }} />
      <AbsoluteFill style={{ justifyContent: "flex-start", alignItems: "flex-start", padding: 70, opacity: intro }}>
        <div style={{ color: "#eafcf6", fontSize: 60, fontWeight: 800, letterSpacing: 2, textShadow: `0 0 30px ${accent}`, maxWidth: width * 0.6 }}>{title}</div>
      </AbsoluteFill>
      <AbsoluteFill style={{ opacity: intro }}>
        <svg width={width} height={height} style={{ position: "absolute" }}>
          {figs.map((f, i) => {
            const pop = spring({ frame: frame - (16 + i * 3), fps, config: { damping: 13, stiffness: 130 } });
            const col = f.male ? accent : "#4d6b67";
            const sc = (f.male ? 1.5 * malePulse : 1) * Math.max(0.001, pop);
            return (
              <g key={i} transform={`translate(${f.x},${f.y}) scale(${sc})`} opacity={pop}
                 style={{ filter: f.male ? `drop-shadow(0 0 14px ${accent})` : "none" }}>
                <circle cx="0" cy="-16" r="9" fill={f.male ? "#eafcf6" : "#6f8f8a"} />
                {f.male
                  ? <path d="M -9 -6 Q 0 -10 9 -6 L 7 22 L -7 22 Z" fill={col} />
                  : <path d="M -9 -6 Q 0 -9 9 -6 L 12 24 L -12 24 Z" fill={col} />}
              </g>
            );
          })}
        </svg>
      </AbsoluteFill>
      <AbsoluteFill style={{ boxShadow: "inset 0 0 260px rgba(0,0,0,0.7)", pointerEvents: "none" }} />
      {/* большое соотношение справа */}
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "flex-end", padding: 90, opacity: intro * exit }}>
        <div style={{ textAlign: "right" }}>
          <div style={{ color: accent, fontSize: 160, fontWeight: 800, lineHeight: 0.9, textShadow: `0 0 40px ${accent}` }}>{ratio}</div>
          <div style={{ color: "#cfe8e2", fontSize: 30, fontWeight: 700, letterSpacing: 3, textTransform: "uppercase" }}>вымирали мужские роды</div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
