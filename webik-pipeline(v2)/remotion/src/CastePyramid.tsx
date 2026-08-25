import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { PALETTE, fontFamily } from "./theme";

export type CastePyramidProps = {
  title?: string;
  accent?: string;
};

const Person: React.FC<{ s: number; col: string; glow?: number }> = ({ s, col, glow = 0 }) => (
  <svg width={s} height={s * 1.3} viewBox="0 0 100 130" style={{ filter: glow ? `drop-shadow(0 0 ${glow}px ${col})` : undefined }}>
    <ellipse cx="50" cy="34" rx="23" ry="27" fill={col} />
    <path d="M10 130 Q50 64 90 130 Z" fill={col} />
  </svg>
);

const Star: React.FC<{ size: number; col: string; glow?: number }> = ({ size, col, glow = 0 }) => (
  <svg width={size} height={size} viewBox="-50 -50 100 100" style={{ filter: glow ? `drop-shadow(0 0 ${glow}px ${col})` : undefined }}>
    <polygon points={Array.from({ length: 5 }).map((_, i) => { const a = (-90 + i * 72) * Math.PI / 180; const ao = (-90 + i * 72 + 36) * Math.PI / 180; return `${Math.cos(a) * 48},${Math.sin(a) * 48} ${Math.cos(ao) * 20},${Math.sin(ao) * 20}`; }).join(" ")} fill={col} />
  </svg>
);

// Иерархия сонбун одним кадром: звезда+элита сверху → «колеблющиеся» → толпа «враждебных» внизу.
export const CastePyramid: React.FC<CastePyramidProps> = ({
  title = "СОНБУН",
  accent = PALETTE.red,
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames, fps } = useVideoConfig();
  const gold = PALETTE.gold;
  const amber = "#cf9a3e";

  const exit = interpolate(frame, [durationInFrames - 20, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });
  const zoom = interpolate(frame, [0, durationInFrames], [1.0, 1.07]);
  const starPulse = 1 + 0.06 * Math.sin(frame / 9);
  const appTop = spring({ frame, fps, config: { damping: 16 }, durationInFrames: 20 });
  const appMid = spring({ frame: frame - 8, fps, config: { damping: 16 }, durationInFrames: 20 });
  const appBot = spring({ frame: frame - 16, fps, config: { damping: 16 }, durationInFrames: 24 });

  const bottom = Array.from({ length: 44 });

  return (
    <AbsoluteFill style={{ fontFamily: fontFamily("oswald"), opacity: exit }}>
      <AbsoluteFill style={{ background: "linear-gradient(180deg, #0e0a12 0%, #1a0809 52%, #300808 100%)" }} />
      <AbsoluteFill style={{ background: `radial-gradient(ellipse at 50% 10%, ${gold}26, transparent 42%)` }} />
      {/* большой треугольник-иерархия */}
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", transform: `scale(${zoom})` }}>
        <svg width={1500} height={900} viewBox="0 0 1500 900" style={{ position: "absolute", top: 90 }}>
          <polygon points="750,20 1360,860 140,860" fill="none" stroke={`${accent}55`} strokeWidth="2" />
          <line x1="360" y1="590" x2="1140" y2="590" stroke={`${amber}44`} strokeWidth="2" />
          <line x1="560" y1="320" x2="940" y2="320" stroke={`${gold}55`} strokeWidth="2" />
        </svg>
      </AbsoluteFill>

      <AbsoluteFill style={{ transform: `scale(${zoom})` }}>
        {/* ВЕРШИНА — элита */}
        <div style={{ position: "absolute", left: "50%", top: "9%", transform: `translateX(-50%) translateY(${(1 - appTop) * -40}px)`, opacity: appTop, display: "flex", flexDirection: "column", alignItems: "center" }}>
          <div style={{ transform: `scale(${starPulse})` }}><Star size={110} col={gold} glow={34} /></div>
          <div style={{ marginTop: 2 }}><Person s={120} col={gold} glow={22} /></div>
          <div style={{ color: gold, fontSize: 34, fontWeight: 800, letterSpacing: 3 }}>ЭЛИТА · немногие</div>
        </div>

        {/* СЕРЕДИНА — колеблющиеся */}
        <div style={{ position: "absolute", left: "50%", top: "40%", transform: `translateX(-50%) translateY(${(1 - appMid) * 30}px)`, opacity: appMid, display: "flex", flexDirection: "column", alignItems: "center", gap: 6 }}>
          <div style={{ display: "flex", gap: 26 }}>{Array.from({ length: 7 }).map((_, i) => <Person key={i} s={92} col={amber} glow={8} />)}</div>
          <div style={{ color: amber, fontSize: 30, fontWeight: 700, letterSpacing: 3 }}>КОЛЕБЛЮЩИЙСЯ КЛАСС</div>
        </div>

        {/* НИЗ — толпа «враждебных» */}
        <div style={{ position: "absolute", left: "50%", top: "64%", transform: `translateX(-50%) translateY(${(1 - appBot) * 40}px)`, opacity: appBot, display: "flex", flexDirection: "column", alignItems: "center" }}>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(22, 1fr)", gap: 6, width: 1500, justifyItems: "center" }}>
            {bottom.map((_, i) => <Person key={i} s={62} col="#4a1010" />)}
          </div>
          <div style={{ marginTop: 6, color: accent, fontSize: 36, fontWeight: 800, letterSpacing: 3, textShadow: `0 0 20px ${accent}` }}>«ВРАЖДЕБНЫЙ КЛАСС» · большинство</div>
        </div>
      </AbsoluteFill>

      <AbsoluteFill style={{ background: "radial-gradient(ellipse at 50% 100%, rgba(217,40,40,0.35), transparent 55%)", pointerEvents: "none" }} />
      <AbsoluteFill style={{ boxShadow: "inset 0 0 300px rgba(0,0,0,0.8)", pointerEvents: "none" }} />

      {title && (
        <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: 40, opacity: interpolate(frame, [18, 36], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) * exit }}>
          <div style={{ color: PALETTE.cream, fontSize: 72, fontWeight: 800, letterSpacing: 6, textTransform: "uppercase", textShadow: `0 0 40px ${accent}, 0 6px 30px rgba(0,0,0,0.9)` }}>{title}</div>
          <div style={{ marginTop: 6, color: accent, fontSize: 28, letterSpacing: 4, fontWeight: 600 }}>51 РАЗРЯД · СУДЬБА ОТ РОЖДЕНИЯ</div>
        </AbsoluteFill>
      )}
    </AbsoluteFill>
  );
};
