import React from "react";
import {
  AbsoluteFill,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { PALETTE, fontFamily } from "./theme";

export type PrisonCampProps = {
  title?: string;
  accent?: string;
};

// Ночной лагерь: уходящая колючая проволока, вышки, лучи прожекторов, туман.
export const PrisonCamp: React.FC<PrisonCampProps> = ({
  title = "ЛАГЕРЯ",
  accent = PALETTE.red,
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  const dolly = interpolate(frame, [0, durationInFrames], [0, 3600], { extrapolateRight: "clamp" });
  const sway = Math.sin(frame / 44) * 2.4;
  const intro = interpolate(frame, [0, 18], [0, 1], { extrapolateRight: "clamp" });
  const exit = interpolate(frame, [durationInFrames - 20, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });

  // столбы забора в глубину (обе стороны)
  const posts = Array.from({ length: 12 }).flatMap((_, i) =>
    [-1, 1].map((side) => ({ z: -400 - i * 460, side, i, key: `${i}-${side}` }))
  );
  // ряды колючей проволоки (горизонтальные линии на разной высоте, в глубину)
  const wires = [-180, -80, 20, 120];

  return (
    <AbsoluteFill style={{ fontFamily: fontFamily("oswald"), opacity: exit }}>
      {/* холодное небо-градиент + луна-зарево */}
      <AbsoluteFill style={{ background: "linear-gradient(180deg, #0a1016 0%, #0c0708 55%, #050202 100%)" }} />
      <AbsoluteFill style={{ background: "radial-gradient(circle at 50% 22%, rgba(180,60,60,0.28), transparent 45%)" }} />

      {/* вышки-прожекторы по краям + лучи */}
      {[-1, 1].map((side) => {
        const beamRot = side * (26 + Math.sin(frame / 40 + (side > 0 ? 1 : 0)) * 16);
        return (
          <AbsoluteFill key={side} style={{ opacity: intro }}>
            {/* луч */}
            <div style={{ position: "absolute", top: "18%", left: side < 0 ? "12%" : undefined, right: side > 0 ? "12%" : undefined, width: 520, height: "120%", transformOrigin: "top center", transform: `rotate(${beamRot}deg)`, background: `linear-gradient(180deg, ${accent}bb, ${accent}22 40%, transparent 75%)`, filter: "blur(16px)", mixBlendMode: "screen" }} />
            {/* вышка (силуэт) */}
            <svg style={{ position: "absolute", top: "12%", left: side < 0 ? "6%" : undefined, right: side > 0 ? "6%" : undefined }} width={160} height={420} viewBox="0 0 160 420">
              <polygon points="30,420 55,120 105,120 130,420" fill="#000" opacity="0.9" />
              <rect x="35" y="70" width="90" height="60" fill="#0a0505" stroke="#000" strokeWidth="4" />
              <polygon points="30,70 80,30 130,70" fill="#000" />
              <circle cx="80" cy="100" r="10" fill={accent} style={{ filter: `drop-shadow(0 0 14px ${accent})` }} />
              <line x1="40" y1="220" x2="120" y2="220" stroke="#000" strokeWidth="6" />
              <line x1="45" y1="320" x2="115" y2="320" stroke="#000" strokeWidth="6" />
            </svg>
          </AbsoluteFill>
        );
      })}

      {/* 3D-забор */}
      <AbsoluteFill style={{ perspective: 1000, opacity: intro }}>
        <div
          style={{
            position: "absolute",
            left: "50%",
            top: "60%",
            transformStyle: "preserve-3d",
            transform: `translate(-50%,-50%) rotateY(${sway}deg) translateZ(${dolly}px)`,
          }}
        >
          {posts.map(({ z, side, key }) => (
            <div key={key} style={{ position: "absolute", transform: `translate3d(${side * 470}px, -40px, ${z}px)`, width: 16, height: 440, marginLeft: -8, marginTop: -220, background: "linear-gradient(180deg,#1a1414,#000)", boxShadow: "0 0 8px rgba(0,0,0,0.8)" }} />
          ))}
          {/* колючая проволока — тонкие светящиеся линии в глубину */}
          {wires.map((wy, wi) =>
            [-1, 1].map((side) => (
              <div key={`${wi}-${side}`} style={{ position: "absolute", transform: `translate3d(${side * 470}px, ${wy}px, -3200px)`, width: 16, height: 3, marginLeft: -8, background: `${accent}`, boxShadow: `0 0 10px ${accent}`, transformOrigin: "left center", scale: "360 1", opacity: 0.5 }} />
            ))
          )}
        </div>
      </AbsoluteFill>

      {/* туман по земле + виньетка */}
      <AbsoluteFill style={{ background: "radial-gradient(ellipse at 50% 92%, rgba(90,50,50,0.5), transparent 55%)", pointerEvents: "none" }} />
      <AbsoluteFill style={{ boxShadow: "inset 0 0 340px rgba(0,0,0,0.9)", pointerEvents: "none" }} />

      {title && (
        <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: 90, opacity: interpolate(frame, [18, 36], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) * exit }}>
          <div style={{ color: PALETTE.cream, fontSize: 90, fontWeight: 800, letterSpacing: 8, textTransform: "uppercase", textShadow: `0 0 40px ${accent}, 0 6px 30px rgba(0,0,0,0.9)` }}>{title}</div>
        </AbsoluteFill>
      )}
    </AbsoluteFill>
  );
};
