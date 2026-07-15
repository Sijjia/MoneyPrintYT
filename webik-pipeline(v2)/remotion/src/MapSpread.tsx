import React from "react";
import { AbsoluteFill, Easing, Img, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { PALETTE, fontFamily } from "./theme";

// Карта-растекание: по тёмной карте расползается красное пятно из очага(ов) —
// как секта/явление распространялось. origins в % экрана; grow — радиус пятна.
export type SpreadOrigin = { x: number; y: number; grow?: number; label?: string };
export type MapSpreadProps = {
  origins?: SpreadOrigin[];
  title?: string;
  label?: string;
  accent?: string;
};

export const MapSpread: React.FC<MapSpreadProps> = ({ origins = [], title = "", label = "", accent = PALETTE.red }) => {
  const frame = useCurrentFrame();
  const { durationInFrames, width, height } = useVideoConfig();
  const exit = interpolate(frame, [durationInFrames - 20, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });

  return (
    <AbsoluteFill style={{ background: "#05070c", opacity: exit, overflow: "hidden", fontFamily: fontFamily("oswald") }}>
      <AbsoluteFill style={{ opacity: 0.55 }}>
        <Img src={staticFile("world_equi.jpg")} style={{ width: "100%", height: "100%", objectFit: "cover", filter: "grayscale(1) brightness(0.5) contrast(1.1)" }} />
      </AbsoluteFill>
      <AbsoluteFill style={{ background: "rgba(5,7,12,0.4)" }} />

      {/* растекающиеся пятна */}
      {origins.map((o, i) => {
        const d = 10 + i * 20;
        const g = interpolate(frame, [d, d + 74], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
        const R = (o.grow || 320) * g;
        const cx = (o.x / 100) * width;
        const cy = (o.y / 100) * height;
        return (
          <div key={i} style={{ position: "absolute", left: cx - R, top: cy - R, width: R * 2, height: R * 2, borderRadius: "50%", background: `radial-gradient(circle, ${accent}cc 0%, ${accent}55 42%, rgba(217,40,40,0) 70%)`, filter: "blur(7px)", mixBlendMode: "screen" }} />
        );
      })}
      {/* очаги + подписи */}
      {origins.map((o, i) => {
        const d = 10 + i * 20;
        const ap = interpolate(frame, [d, d + 10], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
        const cx = (o.x / 100) * width;
        const cy = (o.y / 100) * height;
        const pulse = 1 + 0.4 * Math.max(0, Math.sin(frame / 8 - i));
        return (
          <div key={i} style={{ position: "absolute", left: cx, top: cy, opacity: ap }}>
            <div style={{ position: "absolute", left: -7, top: -7, width: 14, height: 14, borderRadius: "50%", background: "#fff", boxShadow: `0 0 ${16 * pulse}px ${accent}` }} />
            {o.label && <div style={{ position: "absolute", left: 16, top: -16, color: PALETTE.cream, fontSize: 28, fontWeight: 700, letterSpacing: 2, textTransform: "uppercase", whiteSpace: "nowrap", textShadow: "0 2px 10px #000" }}>{o.label}</div>}
          </div>
        );
      })}

      {title && <div style={{ position: "absolute", top: 78, width: "100%", textAlign: "center", color: PALETTE.cream, fontSize: 54, fontWeight: 800, letterSpacing: 5, textTransform: "uppercase", textShadow: "0 4px 20px #000" }}>{title}</div>}
      {label && <div style={{ position: "absolute", bottom: 88, width: "100%", textAlign: "center", color: accent, fontSize: 36, fontWeight: 700, letterSpacing: 3, textTransform: "uppercase" }}>{label}</div>}
    </AbsoluteFill>
  );
};
