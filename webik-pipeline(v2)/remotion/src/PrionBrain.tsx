import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { fontFamily } from "./theme";

export type PrionBrainProps = {
  title?: string;
  sub?: string;
  accent?: string;
};

const rnd = (i: number, s = 1) => {
  const x = Math.sin(i * 57.13 + s * 33.7) * 43758.5453;
  return x - Math.floor(x);
};

// Мозг, который прионы (болезнь Куру) превращают в губку: тёмные дыры появляются
// и расползаются по ткани. Жутко, органично, динамично.
export const PrionBrain: React.FC<PrionBrainProps> = ({
  title = "КУРУ",
  sub = "прионы превращают мозг в губку",
  accent = "#1fa48a",
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames, width, height } = useVideoConfig();
  const intro = interpolate(frame, [0, 20], [0, 1], { extrapolateRight: "clamp" });
  const exit = interpolate(frame, [durationInFrames - 16, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });
  const titleIn = interpolate(frame, [12, 32], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  const cx = width * 0.44, cy = height * 0.5;
  const RX = 300, RY = 235;
  const NHOLES = 46;
  const holes = Array.from({ length: NHOLES }).map((_, i) => {
    const a = rnd(i, 1) * Math.PI * 2;
    const rr = Math.sqrt(rnd(i, 2)) * 0.86;
    const x = cx + Math.cos(a) * RX * rr;
    const y = cy + Math.sin(a) * RY * rr;
    const t0 = 26 + rnd(i, 3) * (durationInFrames * 0.7);
    const g = interpolate(frame, [t0, t0 + 40], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
    return { x, y, r: (4 + rnd(i, 4) * 16) * g, g };
  });

  return (
    <AbsoluteFill style={{ fontFamily: fontFamily("oswald"), opacity: exit }}>
      <AbsoluteFill style={{ background: "radial-gradient(ellipse at 44% 48%, #14181c 0%, #0b0f12 55%, #05080a 100%)" }} />
      <AbsoluteFill style={{ opacity: intro }}>
        <svg width={width} height={height} style={{ position: "absolute" }}>
          <defs>
            <radialGradient id="brainG" cx="42%" cy="38%">
              <stop offset="0" stopColor="#d78b8f" /><stop offset="0.6" stopColor="#b06a70" /><stop offset="1" stopColor="#7a444b" />
            </radialGradient>
            <clipPath id="brainClip"><ellipse cx={cx} cy={cy} rx={RX} ry={RY} /></clipPath>
          </defs>
          {/* полушария */}
          <ellipse cx={cx} cy={cy} rx={RX} ry={RY} fill="url(#brainG)" stroke="#5f363c" strokeWidth={4} />
          {/* извилины */}
          <g clipPath="url(#brainClip)" opacity={0.5}>
            {Array.from({ length: 22 }).map((_, i) => (
              <path key={i} d={`M ${cx - RX} ${cy - RY + i * (2 * RY / 22)} q ${RX * 0.4} ${18 - (i % 2) * 36}, ${RX} 0 t ${RX} 0`}
                stroke="#844d54" strokeWidth={3} fill="none" />
            ))}
            <line x1={cx} y1={cy - RY} x2={cx} y2={cy + RY} stroke="#6b3d43" strokeWidth={5} />
          </g>
          {/* губчатые дыры */}
          <g clipPath="url(#brainClip)">
            {holes.map((h, i) => h.g > 0.01 && (
              <g key={i}>
                <circle cx={h.x} cy={h.y} r={h.r} fill="#0a0507" />
                <circle cx={h.x} cy={h.y} r={h.r} fill="none" stroke={accent} strokeWidth={1.4} opacity={0.5 * h.g} />
              </g>
            ))}
          </g>
          {/* ствол */}
          <path d={`M ${cx} ${cy + RY - 10} q -14 60 -6 96`} stroke="#7a444b" strokeWidth={26} fill="none" strokeLinecap="round" />
        </svg>
      </AbsoluteFill>
      <AbsoluteFill style={{ boxShadow: "inset 0 0 300px rgba(0,0,0,0.78)", pointerEvents: "none" }} />
      <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "flex-end", padding: 90, opacity: titleIn * exit }}>
        <div style={{ textAlign: "right" }}>
          <div style={{ color: "#eafcf6", fontSize: 118, fontWeight: 800, letterSpacing: 4, textShadow: `0 0 34px ${accent}` }}>{title}</div>
          <div style={{ color: accent, fontSize: 34, fontWeight: 700, letterSpacing: 2, textTransform: "uppercase" }}>{sub}</div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
