import React from "react";
import { AbsoluteFill, Img, staticFile, interpolate, useCurrentFrame, useVideoConfig, Easing } from "remotion";
import { fontFamily } from "./theme";

// Финал-рефлексия: подъём из красной бездны к поверхности + монтаж-callback реальных кадров тем
// (память всплывает пузырями), лучи света у поверхности, финальный вордмарк. Зеркало интро.

type Shot = { img: string; from: number; to: number; lane: number };  // lane: 0 лев / 1 центр / 2 прав
export type OutroReflectionProps = {
  shots?: Shot[];
  accent?: string;
  brand?: string;
  riseFrom?: number;      // кадр начала подъёма (до него — глубокая бездна, «дно»)
  fps?: number;
};

const CLAMP = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const rnd = (i: number, s = 1) => {
  const x = Math.sin(i * 12.9898 + s * 78.233) * 43758.5453;
  return x - Math.floor(x);
};

export const OutroReflection: React.FC<OutroReflectionProps> = ({
  shots = [], accent = "#ff4500", brand = "REDDIT", riseFrom = 0,
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames: D, width: W, height: H } = useVideoConfig();

  const appear = interpolate(frame, [0, 24], [0, 1], CLAMP);
  const exit = interpolate(frame, [D - 20, D], [1, 0], CLAMP);
  // подъём: 0 в бездне → 1 у поверхности
  const rise = interpolate(frame, [riseFrom, D - 12], [0, 1], { ...CLAMP, easing: Easing.inOut(Easing.cubic) });
  const abyss = 1 - rise;                      // сколько ещё «красной» глубины
  const surface = interpolate(rise, [0.72, 1], [0, 1], CLAMP);   // близость к свету

  const laneX = (l: number) => W * (l === 0 ? 0.22 : l === 1 ? 0.5 : 0.78);

  return (
    <AbsoluteFill style={{ fontFamily: fontFamily("oswald"), background: "#04070c", opacity: appear * exit, overflow: "hidden" }}>
      {/* толща воды: снизу красная бездна, сверху — прохладный свет поверхности (растёт при подъёме) */}
      <AbsoluteFill style={{ background:
        `linear-gradient(180deg, rgba(10,22,34,${0.35 + surface * 0.5}) 0%, #0a1a28 ${18 + surface * 14}%, #071624 52%, #0a0f1a 74%, ${abyss > 0.4 ? "#2a0808" : "#0c0a12"} 92%, ${abyss > 0.4 ? "#5a0d0d" : "#140a10"} 100%)` }} />
      {/* красное свечение из глубины — гаснет по мере подъёма */}
      <AbsoluteFill style={{ background: `radial-gradient(120% 70% at 50% 114%, ${accent}${abyss > 0.5 ? "40" : "12"} 0%, rgba(0,0,0,0) 60%)` }} />
      {/* свет поверхности сверху — разгорается к концу */}
      <AbsoluteFill style={{ background: `radial-gradient(90% 55% at 50% -12%, rgba(190,224,242,${0.05 + surface * 0.5}) 0%, rgba(0,0,0,0) 55%)` }} />

      {/* лучи света от поверхности */}
      <AbsoluteFill style={{ opacity: (0.12 + surface * 0.5) * appear, pointerEvents: "none" }}>
        {[0, 1, 2, 3, 4].map((i) => {
          const x = W * (0.2 + i * 0.15) + Math.sin(frame / 44 + i) * 22;
          return <div key={`ray${i}`} style={{ position: "absolute", top: -80, left: x, width: 90 + i * 10, height: H * 0.9,
            transform: `rotate(${(i - 2) * 4}deg)`, transformOrigin: "top center",
            background: "linear-gradient(180deg, rgba(190,224,242,0.5), rgba(190,224,242,0))", filter: "blur(22px)" }} />;
        })}
      </AbsoluteFill>

      {/* силуэт айсберга, уходящий вверх из воды (слева), подтверждает «мы у айсберга» */}
      <svg width={W} height={H} style={{ position: "absolute", inset: 0, opacity: 0.5 * appear }}>
        <polygon
          points={`-40,${H * 1.05} ${W * 0.10},${H * (0.42 - rise * 0.5)} ${W * 0.20},${H * (0.20 - rise * 0.55)} ${W * 0.30},${H * (0.5 - rise * 0.5)} ${W * 0.24},${H * 1.05}`}
          fill="url(#ogr)" opacity={0.55} />
        <defs>
          <linearGradient id="ogr" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="#cfe6f4" stopOpacity="0.5" /><stop offset="0.6" stopColor="#3f5f76" stopOpacity="0.4" />
            <stop offset="1" stopColor="#243d50" stopOpacity="0.2" />
          </linearGradient>
        </defs>
      </svg>

      {/* пузыри/частицы — поднимаются */}
      <AbsoluteFill style={{ opacity: 0.55 * appear, pointerEvents: "none" }}>
        {Array.from({ length: 40 }).map((_, i) => {
          const x = rnd(i, 7) * 100;
          const spd = 0.5 + rnd(i, 9) * 1.1;
          const y = ((rnd(i, 8) * 100 - frame * spd / 6) % 100 + 100) % 100;
          const sz = 2 + rnd(i, 10) * 5;
          return <div key={`b${i}`} style={{ position: "absolute", left: `${x}%`, top: `${y}%`, width: sz, height: sz,
            borderRadius: "50%", background: i % 6 === 0 ? accent : "#bfe0f0", opacity: 0.14 + rnd(i, 11) * 0.22, filter: "blur(0.4px)" }} />;
        })}
      </AbsoluteFill>

      {/* МОНТАЖ — кадры-воспоминания всплывают снизу вверх, кино-рамка + Ken-Burns + фейд */}
      {shots.map((s, i) => {
        const op = interpolate(frame, [s.from, s.from + 14, s.to - 16, s.to], [0, 1, 1, 0], CLAMP);
        if (op <= 0.001) return null;
        const prog = interpolate(frame, [s.from, s.to], [0, 1], CLAMP);
        const drift = interpolate(prog, [0, 1], [70, -70]);           // медленный подъём
        const kb = 1.04 + prog * 0.12;
        const w = W * (s.lane === 1 ? 0.34 : 0.28);
        const x = laneX(s.lane) + Math.sin((frame + i * 30) / 60) * 10;
        const y = H * (s.lane === 1 ? 0.46 : s.lane === 0 ? 0.4 : 0.54) + drift;
        const rot = (s.lane === 0 ? -2.2 : s.lane === 2 ? 2.2 : 0);
        return (
          <div key={`s${i}`} style={{ position: "absolute", left: x, top: y, width: w, transform: `translate(-50%,-50%) rotate(${rot}deg)`,
            opacity: op, borderRadius: 12, overflow: "hidden", aspectRatio: "16/10",
            boxShadow: `0 24px 70px rgba(0,0,0,0.8), 0 0 0 2px ${accent}aa, 0 0 34px ${accent}44` }}>
            <Img src={staticFile(s.img)} style={{ width: "100%", height: "100%", objectFit: "cover",
              transform: `scale(${kb})`, transformOrigin: "50% 45%" }} />
            <div style={{ position: "absolute", inset: 0, background: "linear-gradient(180deg, rgba(0,0,0,0.15) 0%, transparent 30%, rgba(0,0,0,0.4) 100%)" }} />
            <div style={{ position: "absolute", inset: 0, boxShadow: "inset 0 0 40px rgba(0,0,0,0.5)" }} />
          </div>
        );
      })}

      {/* лёгкая рябь поверхности сверху при выходе к свету */}
      {surface > 0.01 && (
        <div style={{ position: "absolute", top: 0, left: 0, width: "100%", height: H * 0.16,
          background: `linear-gradient(180deg, rgba(200,230,245,${surface * 0.4}), rgba(200,230,245,0))`, opacity: surface }} />
      )}

      {/* финальный вордмарк у поверхности */}
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", opacity: surface }}>
        <div style={{ textAlign: "center", transform: `translateY(${interpolate(surface, [0, 1], [40, 0])}px)` }}>
          <div style={{ color: "#f4f1ea", fontSize: 128, fontWeight: 800, letterSpacing: 4, lineHeight: 0.9,
            textShadow: "0 6px 40px rgba(0,0,0,0.7)" }}>АЙСБЕРГ</div>
          <div style={{ color: accent, fontSize: 96, fontWeight: 800, letterSpacing: 4, textShadow: `0 0 44px ${accent}` }}>{brand}</div>
        </div>
      </AbsoluteFill>

      {/* виньетка */}
      <AbsoluteFill style={{ boxShadow: "inset 0 0 320px rgba(0,0,0,0.85)", pointerEvents: "none" }} />
    </AbsoluteFill>
  );
};
