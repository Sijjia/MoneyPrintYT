import React from "react";
import { AbsoluteFill, Easing, Img, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { PALETTE, fontFamily } from "./theme";

// Архивное фото с разметкой: медленный наезд (Ken Burns) + обводки/выноски к деталям
// («вот здесь…»). Расследовательский стиль, пара к «Досье». photo — файл в public/.
export type Annot = { x: number; y: number; r?: number; label?: string };
export type PhotoAnnotateProps = {
  photo?: string | null;
  title?: string;
  annotations?: Annot[];
  accent?: string;
};

export const PhotoAnnotate: React.FC<PhotoAnnotateProps> = ({
  photo = null,
  title = "",
  annotations = [],
  accent = PALETTE.red,
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames, width, height } = useVideoConfig();
  const s = interpolate(frame, [0, durationInFrames], [1.06, 1.24]);
  const tx = interpolate(frame, [0, durationInFrames], [0, -44]);
  const exit = interpolate(frame, [durationInFrames - 20, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });

  return (
    <AbsoluteFill style={{ background: "#05070c", opacity: exit, overflow: "hidden", fontFamily: fontFamily("oswald") }}>
      <AbsoluteFill style={{ transform: `scale(${s}) translateX(${tx}px)` }}>
        {photo ? (
          <Img src={photo.startsWith("data:") ? photo : staticFile(photo)} style={{ width: "100%", height: "100%", objectFit: "cover", filter: "grayscale(0.75) contrast(1.12) brightness(0.8)" }} />
        ) : (
          <AbsoluteFill style={{ background: "repeating-linear-gradient(45deg,#0b111e,#0b111e 22px,#0e1524 22px,#0e1524 44px)" }} />
        )}
      </AbsoluteFill>
      <AbsoluteFill style={{ background: "radial-gradient(circle at 50% 44%, rgba(0,0,0,0) 26%, rgba(0,0,0,0.72) 100%)" }} />
      <AbsoluteFill style={{ background: `linear-gradient(180deg, rgba(217,40,40,0.06), rgba(120,10,10,0.16))`, mixBlendMode: "multiply" }} />

      <svg width={width} height={height} style={{ position: "absolute", inset: 0 }}>
        {annotations.map((a, i) => {
          const d = 22 + i * 34;
          const p = interpolate(frame, [d, d + 24], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
          const cx = (a.x / 100) * width;
          const cy = (a.y / 100) * height;
          const r = a.r || 70;
          const circ = 2 * Math.PI * r;
          return (
            <g key={i} opacity={p}>
              <circle cx={cx} cy={cy} r={r} fill="none" stroke={accent} strokeWidth={4} strokeDasharray={circ} strokeDashoffset={circ * (1 - p)} transform={`rotate(-90 ${cx} ${cy})`} style={{ filter: `drop-shadow(0 0 8px ${accent}aa)` }} />
              <line x1={cx + r * 0.7} y1={cy - r * 0.7} x2={cx + r * 0.7 + 130} y2={cy - r * 0.7 - 64} stroke={accent} strokeWidth={3} />
            </g>
          );
        })}
      </svg>
      {annotations.map((a, i) => {
        const d = 22 + i * 34;
        const p = interpolate(frame, [d + 12, d + 28], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
        const cx = (a.x / 100) * width;
        const cy = (a.y / 100) * height;
        const r = a.r || 70;
        return a.label ? (
          <div key={i} style={{ position: "absolute", left: cx + r * 0.7 + 130, top: cy - r * 0.7 - 96, opacity: p, color: PALETTE.cream, fontSize: 34, fontWeight: 700, letterSpacing: 2, textTransform: "uppercase", textShadow: "0 2px 12px #000", maxWidth: 420 }}>{a.label}</div>
        ) : null;
      })}

      {title && (
        <div style={{ position: "absolute", bottom: 88, left: 100, color: PALETTE.cream, fontSize: 54, fontWeight: 800, letterSpacing: 3, textTransform: "uppercase", textShadow: "0 4px 20px #000", opacity: interpolate(frame, [6, 22], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) }}>{title}</div>
      )}
    </AbsoluteFill>
  );
};
