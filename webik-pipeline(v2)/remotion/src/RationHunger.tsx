import React from "react";
import {
  AbsoluteFill,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { PALETTE, fontFamily } from "./theme";

export type RationHungerProps = {
  title?: string;
  accent?: string;
};

const Bowl: React.FC<{ fill: number; col: string }> = ({ fill, col }) => (
  <svg width={200} height={130} viewBox="0 0 200 130">
    {/* содержимое (доля fill 0..1) */}
    <clipPath id="b"><path d="M18 40 Q100 150 182 40 Z" /></clipPath>
    <rect x="18" y={40 + (1 - fill) * 70} width="164" height={fill * 70} fill={col} clipPath="url(#b)" opacity="0.9" />
    {/* чаша */}
    <path d="M10 40 Q100 156 190 40" fill="none" stroke="#c9c2b4" strokeWidth="7" />
    <ellipse cx="100" cy="40" rx="90" ry="16" fill="none" stroke="#c9c2b4" strokeWidth="7" />
  </svg>
);

// Иерархия голода: ряд мисок в глубину — полная у элиты, пустая у «враждебных».
export const RationHunger: React.FC<RationHungerProps> = ({
  title = "ИЕРАРХИЯ ГОЛОДА",
  accent = PALETTE.red,
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const gold = PALETTE.gold;

  const intro = interpolate(frame, [0, 18], [0, 1], { extrapolateRight: "clamp" });
  const exit = interpolate(frame, [durationInFrames - 18, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });
  const dolly = interpolate(frame, [0, durationInFrames], [-200, 2400]);
  const sway = Math.sin(frame / 46) * 2;

  const N = 9;
  const bowls = Array.from({ length: N }).map((_, i) => {
    const fill = Math.max(0.04, 1 - i / (N - 1)); // спереди полная → в глубине пустая
    const col = i < 2 ? gold : i < 4 ? "#b98a2e" : accent;
    return { z: -200 - i * 460, x: (i % 2 === 0 ? -1 : 1) * 40, fill, col, i, key: i };
  });

  return (
    <AbsoluteFill style={{ fontFamily: fontFamily("oswald"), opacity: exit }}>
      <AbsoluteFill style={{ background: "radial-gradient(circle at 50% 46%, #1e0a08 0%, #0e0505 55%, #050202 100%)" }} />

      {/* падающие «зёрна» */}
      <AbsoluteFill style={{ opacity: 0.5 * intro, pointerEvents: "none" }}>
        {Array.from({ length: 30 }).map((_, i) => {
          const x = (Math.sin(i * 12.9) * 0.5 + 0.5) * 100;
          const y = ((frame * (2 + (i % 3)) + i * 40) % 120);
          return <div key={i} style={{ position: "absolute", left: `${x}%`, top: `${y}%`, width: 4, height: 8, borderRadius: 2, background: "#e9dcae", opacity: 0.6 }} />;
        })}
      </AbsoluteFill>

      <AbsoluteFill style={{ perspective: 1100, opacity: intro }}>
        <div style={{ position: "absolute", left: "50%", top: "54%", transformStyle: "preserve-3d", transform: `translate(-50%,-50%) rotateY(${sway}deg) rotateX(14deg) translateZ(${dolly}px)` }}>
          {bowls.map(({ z, x, fill, col, i, key }) => (
            <div key={key} style={{ position: "absolute", transform: `translate3d(${x}px, 0px, ${z}px)`, marginLeft: -100, marginTop: -65, filter: `drop-shadow(0 0 24px ${col}66)` }}>
              <Bowl fill={fill} col={col} />
              <div style={{ textAlign: "center", marginTop: 6, color: col, fontSize: 30, fontWeight: 700 }}>{i === 0 ? "700 г" : i === N - 1 ? "90 г" : ""}</div>
            </div>
          ))}
        </div>
      </AbsoluteFill>

      <AbsoluteFill style={{ boxShadow: "inset 0 0 320px rgba(0,0,0,0.88)", pointerEvents: "none" }} />

      {/* подписи класса */}
      <AbsoluteFill style={{ opacity: intro, pointerEvents: "none" }}>
        <div style={{ position: "absolute", left: "16%", top: "30%", color: gold, fontSize: 32, letterSpacing: 3, fontWeight: 700 }}>ЭЛИТА · 700 г</div>
        <div style={{ position: "absolute", right: "16%", bottom: "30%", color: accent, fontSize: 32, letterSpacing: 3, fontWeight: 700 }}>«ВРАЖДЕБНЫЕ» · 90 г</div>
      </AbsoluteFill>

      {title && (
        <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: 86, opacity: interpolate(frame, [18, 36], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) * exit }}>
          <div style={{ color: PALETTE.cream, fontSize: 84, fontWeight: 800, letterSpacing: 6, textTransform: "uppercase", textShadow: `0 0 40px ${accent}, 0 6px 30px rgba(0,0,0,0.9)` }}>{title}</div>
          <div style={{ marginTop: 8, color: accent, fontSize: 30, letterSpacing: 4, fontWeight: 600 }}>КАРТОЧКА РЕШАЕТ, КТО ВЫЖИВЕТ</div>
        </AbsoluteFill>
      )}
    </AbsoluteFill>
  );
};
