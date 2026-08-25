import React from "react";
import {
  AbsoluteFill,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { PALETTE, fontFamily } from "./theme";

export type NightSatelliteProps = {
  title?: string;
  accent?: string;
};

// deterministic pseudo-random
const rnd = (i: number, s = 1) => {
  const x = Math.sin(i * 127.1 + s * 311.7) * 43758.5453;
  return x - Math.floor(x);
};

// Спутниковый вид ночью: тёмная КНДР между огнями Юга и Китая, камера медленно едет.
export const NightSatellite: React.FC<NightSatelliteProps> = ({
  title = "СТРАНА-ПРИЗРАК",
  accent = PALETTE.red,
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  const zoom = interpolate(frame, [0, durationInFrames], [1.25, 1.02], { extrapolateRight: "clamp" });
  const drift = interpolate(frame, [0, durationInFrames], [-30, 30]);
  const rot = interpolate(frame, [0, durationInFrames], [-3, 2]);
  const intro = interpolate(frame, [0, 20], [0, 1], { extrapolateRight: "clamp" });
  const exit = interpolate(frame, [durationInFrames - 22, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });

  // звёзды
  const stars = Array.from({ length: 140 }).map((_, i) => ({
    x: rnd(i, 1) * 100, y: rnd(i, 2) * 100, r: rnd(i, 3) * 1.6 + 0.4,
    tw: 0.4 + 0.6 * ((Math.sin(frame / 12 + i) + 1) / 2), key: i,
  }));
  // огни городов: юг (низ) ярко, север (центр) почти пусто, Китай (лево) немного
  const southLights = Array.from({ length: 90 }).map((_, i) => ({ x: 44 + rnd(i, 5) * 26, y: 66 + rnd(i, 6) * 20, key: i }));
  const chinaLights = Array.from({ length: 40 }).map((_, i) => ({ x: 8 + rnd(i, 7) * 20, y: 30 + rnd(i, 8) * 45, key: i }));
  const nkFew = Array.from({ length: 4 }).map((_, i) => ({ x: 46 + rnd(i, 9) * 14, y: 40 + rnd(i, 10) * 14, key: i })); // Пхеньян — редкие огни

  return (
    <AbsoluteFill style={{ fontFamily: fontFamily("oswald"), opacity: exit, background: "#01030a" }}>
      {/* звёзды */}
      <AbsoluteFill style={{ opacity: intro }}>
        {stars.map((s) => (
          <div key={s.key} style={{ position: "absolute", left: `${s.x}%`, top: `${s.y}%`, width: s.r * 2, height: s.r * 2, borderRadius: "50%", background: "#cfe0ff", opacity: s.tw * 0.8 }} />
        ))}
      </AbsoluteFill>

      {/* Земля: тёмный диск с атмосферным лимбом, камера едет */}
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", opacity: intro }}>
        <div style={{ position: "relative", width: 1500, height: 1500, transform: `translateX(${drift}px) scale(${zoom}) rotate(${rot}deg)` }}>
          {/* лимб-атмосфера */}
          <div style={{ position: "absolute", inset: 0, borderRadius: "50%", background: "radial-gradient(circle at 50% 50%, #0a1622 60%, #0d2436 74%, transparent 78%)", boxShadow: "inset 0 0 200px rgba(60,120,180,0.25)" }} />
          {/* суша (полуостров, стилизованно) */}
          <svg viewBox="0 0 100 100" style={{ position: "absolute", inset: 0, width: "100%", height: "100%" }}>
            <defs>
              <radialGradient id="southGlow" cx="55%" cy="78%" r="30%">
                <stop offset="0%" stopColor="#ffd98a" stopOpacity="0.85" />
                <stop offset="100%" stopColor="#ffd98a" stopOpacity="0" />
              </radialGradient>
              <radialGradient id="chinaGlow" cx="15%" cy="45%" r="28%">
                <stop offset="0%" stopColor="#ffe0a0" stopOpacity="0.5" />
                <stop offset="100%" stopColor="#ffe0a0" stopOpacity="0" />
              </radialGradient>
            </defs>
            {/* массив суши */}
            <path d="M40 30 Q52 26 56 36 Q60 48 54 58 Q58 66 52 74 Q46 82 44 72 Q40 62 42 52 Q36 42 40 30 Z" fill="#0b0f0c" stroke="#182018" strokeWidth="0.4" />
            <rect width="100" height="100" fill="url(#southGlow)" />
            <rect width="100" height="100" fill="url(#chinaGlow)" />
            {/* линия ДМЗ */}
            <line x1="41" y1="52" x2="57" y2="49" stroke={accent} strokeWidth="0.4" strokeDasharray="1 1" opacity="0.8" />
          </svg>
          {/* огни */}
          {southLights.map((l) => (
            <div key={`s${l.key}`} style={{ position: "absolute", left: `${l.x}%`, top: `${l.y}%`, width: 3, height: 3, borderRadius: "50%", background: "#ffe6a0", boxShadow: "0 0 6px #ffcf6e" }} />
          ))}
          {chinaLights.map((l) => (
            <div key={`c${l.key}`} style={{ position: "absolute", left: `${l.x}%`, top: `${l.y}%`, width: 2.4, height: 2.4, borderRadius: "50%", background: "#ffe6a0", boxShadow: "0 0 5px #ffcf6e", opacity: 0.8 }} />
          ))}
          {nkFew.map((l) => (
            <div key={`n${l.key}`} style={{ position: "absolute", left: `${l.x}%`, top: `${l.y}%`, width: 2.6, height: 2.6, borderRadius: "50%", background: accent, boxShadow: `0 0 8px ${accent}` }} />
          ))}
        </div>
      </AbsoluteFill>

      {/* виньетка */}
      <AbsoluteFill style={{ boxShadow: "inset 0 0 340px rgba(0,0,0,0.8)", pointerEvents: "none" }} />

      {/* подпись: КНДР — тёмное пятно */}
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", opacity: interpolate(frame, [24, 44], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) }}>
        <div style={{ position: "absolute", left: "50.5%", top: "45%", color: accent, fontSize: 34, letterSpacing: 4, fontWeight: 700, textShadow: `0 0 20px ${accent}` }}>КНДР</div>
      </AbsoluteFill>

      {title && (
        <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: 90, opacity: interpolate(frame, [20, 40], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) * exit }}>
          <div style={{ color: PALETTE.cream, fontSize: 88, fontWeight: 800, letterSpacing: 8, textTransform: "uppercase", textShadow: `0 0 40px ${accent}, 0 6px 30px rgba(0,0,0,0.9)` }}>{title}</div>
        </AbsoluteFill>
      )}
    </AbsoluteFill>
  );
};
