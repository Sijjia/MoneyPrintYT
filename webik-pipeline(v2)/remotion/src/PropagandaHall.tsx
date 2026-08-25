import React from "react";
import {
  AbsoluteFill,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { PALETTE, fontFamily } from "./theme";

export type PropagandaHallProps = {
  title?: string;
  accent?: string;
};

const Star: React.FC<{ size: number; color: string; stroke?: string; sw?: number; glow?: number }> = ({
  size, color, stroke, sw = 0, glow = 0,
}) => (
  <svg width={size} height={size} viewBox="-50 -50 100 100" style={{ filter: glow ? `drop-shadow(0 0 ${glow}px ${color})` : undefined }}>
    <polygon
      points={Array.from({ length: 5 })
        .map((_, i) => {
          const a = (-90 + i * 72) * (Math.PI / 180);
          const ao = (-90 + i * 72 + 36) * (Math.PI / 180);
          return `${Math.cos(a) * 48},${Math.sin(a) * 48} ${Math.cos(ao) * 20},${Math.sin(ao) * 20}`;
        })
        .join(" ")}
      fill={color}
      stroke={stroke}
      strokeWidth={sw}
    />
  </svg>
);

// Кино-проезд камеры сквозь «зал вождя»: знамёна, звёзды, портреты в тумане.
export const PropagandaHall: React.FC<PropagandaHallProps> = ({
  title = "КУЛЬТ ЛИЧНОСТИ",
  accent = PALETTE.red,
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const gold = PALETTE.gold;

  // камера едет вперёд (мир приближается) + лёгкое покачивание
  const dolly = interpolate(frame, [0, durationInFrames], [0, 4200], { extrapolateRight: "clamp" });
  const sway = Math.sin(frame / 34) * 3.2;
  const swayY = Math.cos(frame / 41) * 1.6;
  const intro = interpolate(frame, [0, 18], [0, 1], { extrapolateRight: "clamp" });
  const exit = interpolate(frame, [durationInFrames - 20, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });

  // ряды знамён по сторонам (z в глубину)
  const N = 9;
  const banners = Array.from({ length: N }).flatMap((_, i) => {
    const z = -600 - i * 520;
    return [-1, 1].map((side) => ({ z, side, key: `${i}-${side}` }));
  });
  // портреты по центру-верху вдалеке
  const portraits = Array.from({ length: 5 }).map((_, i) => ({ z: -1400 - i * 620, key: i }));

  return (
    <AbsoluteFill style={{ fontFamily: fontFamily("oswald"), opacity: exit }}>
      {/* глубинный фон: тёмно-красный градиент + большая звезда-солнце в конце */}
      <AbsoluteFill style={{ background: "radial-gradient(circle at 50% 42%, #3a0a0a 0%, #160404 45%, #070202 100%)" }} />
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", opacity: intro }}>
        <div style={{ position: "absolute", top: "30%", filter: `drop-shadow(0 0 120px ${accent})`, opacity: 0.9 }}>
          <Star size={interpolate(frame, [0, durationInFrames], [280, 620])} color={accent} glow={80} />
        </div>
      </AbsoluteFill>

      {/* 3D-зал */}
      <AbsoluteFill style={{ perspective: 1100, opacity: intro }}>
        <div
          style={{
            position: "absolute",
            left: "50%",
            top: "52%",
            transformStyle: "preserve-3d",
            transform: `translate(-50%,-50%) rotateY(${sway}deg) rotateX(${swayY}deg) translateZ(${dolly}px)`,
          }}
        >
          {/* знамёна по бокам */}
          {banners.map(({ z, side, key }) => (
            <div
              key={key}
              style={{
                position: "absolute",
                transform: `translate3d(${side * 560}px, -70px, ${z}px)`,
                width: 260,
                height: 560,
                marginLeft: -130,
                marginTop: -280,
                background: `linear-gradient(180deg, ${accent} 0%, #8e1414 100%)`,
                boxShadow: `0 0 60px ${accent}aa, inset 0 0 40px rgba(0,0,0,0.4)`,
                borderTop: `6px solid ${gold}`,
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                paddingTop: 40,
              }}
            >
              <Star size={110} color={gold} glow={10} />
              <div style={{ marginTop: 20, width: 150, height: 8, background: gold, opacity: 0.8 }} />
              <div style={{ marginTop: 16, width: 120, height: 6, background: "#ffffffaa" }} />
              <div style={{ marginTop: 12, width: 120, height: 6, background: "#ffffff66" }} />
            </div>
          ))}
          {/* портреты по центру */}
          {portraits.map(({ z, key }) => (
            <div
              key={key}
              style={{
                position: "absolute",
                transform: `translate3d(0px, -240px, ${z}px)`,
                width: 300,
                height: 380,
                marginLeft: -150,
                marginTop: -190,
                background: "linear-gradient(180deg, #201312, #0d0707)",
                border: `10px solid ${gold}`,
                boxShadow: `0 0 50px rgba(0,0,0,0.7)`,
                display: "flex",
                alignItems: "flex-end",
                justifyContent: "center",
              }}
            >
              {/* силуэт головы */}
              <svg width={300} height={330} viewBox="0 0 300 330">
                <ellipse cx="150" cy="130" rx="78" ry="92" fill="#000" opacity="0.75" />
                <path d="M40 330 Q150 190 260 330 Z" fill="#000" opacity="0.75" />
              </svg>
            </div>
          ))}
          {/* пол — уходящая красная дорожка */}
          <div
            style={{
              position: "absolute",
              transform: "rotateX(90deg) translateZ(340px) translateY(-2600px)",
              width: 520,
              height: 6000,
              marginLeft: -260,
              background: `linear-gradient(180deg, ${accent}00, ${accent}66)`,
            }}
          />
        </div>
      </AbsoluteFill>

      {/* прожекторы */}
      <AbsoluteFill style={{ mixBlendMode: "screen", opacity: 0.5 * intro }}>
        <div style={{ position: "absolute", left: "20%", top: "-20%", width: 400, height: "140%", background: `linear-gradient(180deg, ${accent}66, transparent)`, transform: `rotate(${18 + Math.sin(frame / 50) * 8}deg)`, filter: "blur(20px)" }} />
        <div style={{ position: "absolute", right: "20%", top: "-20%", width: 400, height: "140%", background: `linear-gradient(180deg, ${gold}44, transparent)`, transform: `rotate(${-18 + Math.cos(frame / 46) * 8}deg)`, filter: "blur(20px)" }} />
      </AbsoluteFill>

      {/* туман */}
      <AbsoluteFill style={{ background: "radial-gradient(circle at 50% 80%, rgba(120,20,20,0.35), transparent 60%)", pointerEvents: "none" }} />
      <AbsoluteFill style={{ background: "linear-gradient(180deg, rgba(7,2,2,0.6) 0%, transparent 25%, transparent 70%, rgba(7,2,2,0.85) 100%)" }} />

      {/* заголовок снизу */}
      {title && (
        <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: 90, opacity: interpolate(frame, [16, 34], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) * exit }}>
          <div style={{ display: "flex", alignItems: "center", gap: 22 }}>
            <Star size={54} color={accent} glow={16} />
            <div style={{ color: PALETTE.cream, fontSize: 92, fontWeight: 800, letterSpacing: 6, textTransform: "uppercase", textShadow: `0 0 40px ${accent}, 0 6px 30px rgba(0,0,0,0.8)` }}>{title}</div>
            <Star size={54} color={accent} glow={16} />
          </div>
        </AbsoluteFill>
      )}
    </AbsoluteFill>
  );
};
