import React from "react";
import { AbsoluteFill, Sequence, Easing, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { PALETTE, fontFamily } from "./theme";
import { isSensitive } from "./censor";

// Цельное анимационное ВСТУПЛЕНИЕ: последовательность битов, каждый рисует то, что
// звучит в закадре. Пока proof — 2 бита (зверства + «во имя веры»). Дальше движок
// расширяется битами globe/iceberg/morph/title под тайминг сценария.

const blurIf = (w: string) => (isSensitive(w) ? "blur(7px)" : "none");

// ── строка-удар: две строки, ключевое слово красным, влёт со сдвигом+шейк ──
const Slam: React.FC<{ top: string; hot: string; f0: number; accent: string }> = ({ top, hot, f0, accent }) => {
  const frame = useCurrentFrame();
  const ap = interpolate(frame, [f0, f0 + 8], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const y = interpolate(frame, [f0, f0 + 14], [60, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.back(1.7)) });
  const shake = Math.sin((frame - f0) * 1.5) * Math.max(0, 7 - (frame - f0));
  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", transform: `translate(${shake}px, ${y}px)`, opacity: ap }}>
      <div style={{ textAlign: "center" }}>
        <div style={{ color: PALETTE.cream, fontSize: 66, fontWeight: 700, letterSpacing: 2, textTransform: "uppercase", opacity: 0.85, filter: blurIf(top) }}>{top}</div>
        <div style={{ color: accent, fontSize: 132, fontWeight: 800, letterSpacing: 2, textTransform: "uppercase", lineHeight: 1.02, textShadow: `0 0 44px ${accent}77, 0 10px 40px #000`, filter: blurIf(hot) }}>{hot}</div>
      </div>
    </AbsoluteFill>
  );
};

// ── Бит A: три зверства влетают по очереди, красная вспышка на входе ──
const AtrocitiesBeat: React.FC<{ accent: string }> = ({ accent }) => {
  const frame = useCurrentFrame();
  const items = [
    { top: "Морят голодом", hot: "детей", at: 4 },
    { top: "Режут соседей за", hot: "колдовство", at: 62 },
    { top: "Сжигают друг друга", hot: "заживо", at: 126 },
  ];
  // красная вспышка на моменты появления
  const flash = items.reduce((a, it) => a + Math.max(0, 1 - Math.abs(frame - it.at) / 6), 0);
  const cur = items.filter((it) => frame >= it.at).slice(-1)[0];
  const grain = 0.04 + 0.03 * Math.abs(Math.sin(frame / 3));
  return (
    <AbsoluteFill style={{ background: "#04060c" }}>
      <AbsoluteFill style={{ background: accent, opacity: Math.min(0.5, flash * 0.5) }} />
      <AbsoluteFill style={{ background: "radial-gradient(circle at 50% 50%, rgba(0,0,0,0) 40%, rgba(0,0,0,0.85) 100%)" }} />
      {cur && <Slam key={cur.at} top={cur.top} hot={cur.hot} f0={cur.at} accent={accent} />}
      <AbsoluteFill style={{ background: "#fff", opacity: grain * 0.5, mixBlendMode: "overlay", pointerEvents: "none" }} />
    </AbsoluteFill>
  );
};

// ── крест, который проявляется штрихом и трескается красным ──
const Cross: React.FC<{ f0: number; accent: string }> = ({ f0, accent }) => {
  const frame = useCurrentFrame();
  const draw = interpolate(frame, [f0, f0 + 34], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
  const crack = interpolate(frame, [f0 + 40, f0 + 60], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const red = interpolate(frame, [f0 + 44, f0 + 66], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const col = `rgb(${Math.round(244 + (217 - 244) * red)},${Math.round(241 + (40 - 241) * red)},${Math.round(234 + (40 - 234) * red)})`;
  const V = 210, len = 640;
  return (
    <svg width={520} height={720} viewBox="0 0 520 720" style={{ overflow: "visible" }}>
      {/* вертикаль + перекладина, рисуются штрихом */}
      <line x1="260" y1="40" x2="260" y2="680" stroke={col} strokeWidth="26" strokeLinecap="round" strokeDasharray={len} strokeDashoffset={len * (1 - draw)} style={{ filter: `drop-shadow(0 0 ${18 * red}px ${accent})` }} />
      <line x1="90" y1={V} x2="430" y2={V} stroke={col} strokeWidth="26" strokeLinecap="round" strokeDasharray={340} strokeDashoffset={340 * (1 - Math.max(0, draw * 1.4 - 0.4))} style={{ filter: `drop-shadow(0 0 ${18 * red}px ${accent})` }} />
      {/* трещина */}
      <polyline points="250,70 285,240 235,380 300,520 250,660" fill="none" stroke={accent} strokeWidth={4} strokeDasharray={900} strokeDashoffset={900 * (1 - crack)} opacity={crack} style={{ filter: `drop-shadow(0 0 8px ${accent})` }} />
    </svg>
  );
};

// ── Бит B: «И ВСЁ ЭТО ВО ИМЯ ВЕРЫ» + крест трескается ──
const FaithBeat: React.FC<{ accent: string }> = ({ accent }) => {
  const frame = useCurrentFrame();
  const smallAp = interpolate(frame, [4, 16], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const bigAp = interpolate(frame, [16, 30], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const bigY = interpolate(frame, [16, 34], [40, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
  const exit = interpolate(frame, [190, 210], [1, 0], { extrapolateLeft: "clamp" });
  return (
    <AbsoluteFill style={{ background: "#04060c", opacity: exit }}>
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", opacity: interpolate(frame, [40, 60], [0.25, 0.5], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) }}>
        <Cross f0={40} accent={accent} />
      </AbsoluteFill>
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
        <div style={{ textAlign: "center" }}>
          <div style={{ color: PALETTE.cream, fontSize: 46, fontWeight: 600, letterSpacing: 6, textTransform: "uppercase", opacity: smallAp * 0.8 }}>И всё это</div>
          <div style={{ color: PALETTE.cream, fontSize: 118, fontWeight: 800, letterSpacing: 3, textTransform: "uppercase", opacity: bigAp, transform: `translateY(${bigY}px)`, textShadow: "0 10px 40px #000" }}>
            во имя <span style={{ color: accent, textShadow: `0 0 40px ${accent}` }}>веры</span>
          </div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

export const IntroSequence: React.FC<{ accent?: string }> = ({ accent = PALETTE.red }) => {
  return (
    <AbsoluteFill style={{ background: "#04060c", fontFamily: fontFamily("oswald") }}>
      <Sequence from={0} durationInFrames={210}>
        <AtrocitiesBeat accent={accent} />
      </Sequence>
      <Sequence from={210} durationInFrames={210}>
        <FaithBeat accent={accent} />
      </Sequence>
    </AbsoluteFill>
  );
};
