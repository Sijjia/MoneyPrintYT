import React from "react";
import {
  AbsoluteFill,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { PALETTE, fontFamily } from "./theme";

export type CyberIntrusionProps = {
  title?: string;
  accent?: string;
};

const rnd = (i: number, s = 1) => {
  const x = Math.sin(i * 51.3 + s * 83.1) * 43758.5453;
  return x - Math.floor(x);
};
const GLYPHS = "01АБ#$%&x9F3D7A2C10⟠▮".split("");

// 3D-полёт сквозь красный «дождь кода» к взламываемому замку. Кибер-армия / Lazarus.
export const CyberIntrusion: React.FC<CyberIntrusionProps> = ({
  title = "КИБЕР-АРМИЯ",
  accent = PALETTE.red,
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  const intro = interpolate(frame, [0, 16], [0, 1], { extrapolateRight: "clamp" });
  const exit = interpolate(frame, [durationInFrames - 18, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });
  const fly = interpolate(frame, [0, durationInFrames], [0, 4400]);
  const breach = interpolate(frame, [40, durationInFrames - 40], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const glitch = Math.sin(frame * 3.3) > 0.86 ? (rnd(frame, 1) - 0.5) * 30 : 0;

  // колонки кода в 3D
  const cols = Array.from({ length: 26 }).map((_, i) => {
    const x = (rnd(i, 1) - 0.5) * 2400;
    const y = (rnd(i, 2) - 0.5) * 1000;
    const z = -400 - rnd(i, 3) * 3200;
    const len = 8 + Math.floor(rnd(i, 4) * 10);
    const speed = 3 + rnd(i, 5) * 5;
    return { x, y, z, len, speed, seed: i, key: i };
  });

  return (
    <AbsoluteFill style={{ fontFamily: "monospace", opacity: exit, background: "#040608" }}>
      <AbsoluteFill style={{ background: "radial-gradient(circle at 50% 50%, #180505 0%, #090304 60%, #040203 100%)" }} />

      {/* 3D дождь кода */}
      <AbsoluteFill style={{ perspective: 1000, opacity: intro }}>
        <div style={{ position: "absolute", left: "50%", top: "50%", transformStyle: "preserve-3d", transform: `translate(-50%,-50%) translateX(${glitch}px) translateZ(${fly}px)` }}>
          {cols.map(({ x, y, z, len, speed, seed, key }) => (
            <div key={key} style={{ position: "absolute", transform: `translate3d(${x}px, ${y}px, ${z}px)`, display: "flex", flexDirection: "column", fontSize: 34, lineHeight: 1.05, color: accent, textShadow: `0 0 8px ${accent}` }}>
              {Array.from({ length: len }).map((__, j) => {
                const g = GLYPHS[Math.floor(rnd(seed * 13 + j, Math.floor(frame / 4) + 1) * GLYPHS.length)];
                const head = (Math.floor((frame * speed) / 6) % (len + 4));
                const op = j === head ? 1 : Math.max(0.08, 1 - Math.abs(head - j) * 0.16);
                return <span key={j} style={{ opacity: op, color: j === head ? PALETTE.cream : accent }}>{g}</span>;
              })}
            </div>
          ))}
        </div>
      </AbsoluteFill>

      {/* центральный замок, который взламывают */}
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", opacity: intro }}>
        <svg width={340} height={340} viewBox="-170 -170 340 340" style={{ filter: `drop-shadow(0 0 ${20 + breach * 40}px ${accent})`, transform: `translateX(${glitch * 0.6}px)` }}>
          <circle r={120 + breach * 30} fill="none" stroke={accent} strokeWidth="3" opacity={0.5} strokeDasharray="14 8" style={{ transformOrigin: "center", transform: `rotate(${frame * 1.5}deg)` }} />
          {/* щит/замок */}
          <path d="M0 -95 L80 -60 L80 30 Q80 90 0 120 Q-80 90 -80 30 L-80 -60 Z" fill="#160404" stroke={accent} strokeWidth="4" opacity={1 - breach * 0.4} />
          <rect x="-34" y="-14" width="68" height="60" rx="8" fill="none" stroke={accent} strokeWidth="5" />
          <path d="M-20 -14 V-34 a20 20 0 0 1 40 0 V-14" fill="none" stroke={accent} strokeWidth="5" />
          {/* трещина при взломе */}
          {breach > 0.4 && <path d="M0 -95 L10 -30 L-14 10 L12 60 L-6 120" fill="none" stroke={PALETTE.cream} strokeWidth={2 + breach * 3} opacity={breach} />}
          {breach > 0.75 && <text x="0" y="8" textAnchor="middle" fill={PALETTE.cream} fontSize="40" fontWeight="800" style={{ fontFamily: "monospace" }}>ВЗЛОМ</text>}
        </svg>
      </AbsoluteFill>

      {/* глитч-полосы + скан */}
      {glitch !== 0 && <AbsoluteFill style={{ background: `repeating-linear-gradient(0deg, transparent 0 ${20 + rnd(frame, 2) * 30}px, ${accent}22 ${20 + rnd(frame, 2) * 30}px ${22 + rnd(frame, 2) * 30}px)`, mixBlendMode: "screen", pointerEvents: "none" }} />}
      <AbsoluteFill style={{ boxShadow: "inset 0 0 320px rgba(0,0,0,0.85)", pointerEvents: "none" }} />

      {/* хедер-терминал */}
      <AbsoluteFill style={{ justifyContent: "flex-start", alignItems: "flex-start", padding: 56, opacity: intro }}>
        <div style={{ color: accent, fontSize: 26, letterSpacing: 3, fontFamily: "monospace" }}>
          &gt; ACCESS_BANK... {Math.floor(breach * 100)}%  0x{(frame * 2654435761 % 0xffffff).toString(16).padStart(6, "0").toUpperCase()}
        </div>
      </AbsoluteFill>

      {title && (
        <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: 90, opacity: interpolate(frame, [16, 34], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) * exit }}>
          <div style={{ fontFamily: fontFamily("oswald"), color: PALETTE.cream, fontSize: 90, fontWeight: 800, letterSpacing: 8, textTransform: "uppercase", textShadow: `0 0 40px ${accent}, 0 6px 30px rgba(0,0,0,0.9)` }}>{title}</div>
        </AbsoluteFill>
      )}
    </AbsoluteFill>
  );
};
