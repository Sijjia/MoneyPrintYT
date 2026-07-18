import React from "react";
import { AbsoluteFill, Sequence, Easing, interpolate, useCurrentFrame } from "remotion";
import { PALETTE, fontFamily } from "./theme";

// Цельное анимационное ВСТУПЛЕНИЕ: биты рисуют смысл ОБРАЗАМИ (не текстом — его в
// ролике и так много). Пока proof: зверства как визуальные метафоры + крест.

// ── силуэт человека (единый визуальный язык) ──
const Figure: React.FC<{ x: number; y: number; s?: number; fill: string; op?: number }> = ({ x, y, s = 1, fill, op = 1 }) => (
  <g transform={`translate(${x} ${y}) scale(${s})`} opacity={op}>
    <circle cx="0" cy="-46" r="16" fill={fill} />
    <path d="M-24 34 C-24 2 -12 -14 0 -14 C12 -14 24 2 24 34 Z" fill={fill} />
  </g>
);

const lerpCol = (a: number[], b: number[], t: number) =>
  `rgb(${a.map((v, i) => Math.round(v + (b[i] - v) * t)).join(",")})`;

// ── ГОЛОД: детская фигура вянет (уменьшается+сереет+оседает), пустая миска ──
const StarveScene: React.FC<{ accent: string }> = ({ accent }) => {
  const f = useCurrentFrame();
  const w = interpolate(f, [8, 62], [1, 0.62], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.inOut(Easing.cubic) });
  const sink = interpolate(f, [8, 62], [0, 70], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const fade = interpolate(f, [8, 62], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const fill = lerpCol([232, 226, 214], [70, 58, 56], fade);
  const bowlAp = interpolate(f, [12, 28], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <svg width="1920" height="1080" viewBox="0 0 1920 1080">
      {/* детская пропорция: голова крупнее (внутри Figure базовая); тут просто масштаб */}
      <Figure x={840} y={540 + sink} s={3.4 * w} fill={fill} />
      {/* пустая миска */}
      <g opacity={bowlAp} transform="translate(1130 610)">
        <path d="M-120 0 C-120 92 120 92 120 0 Z" fill="none" stroke="rgba(230,226,214,0.6)" strokeWidth="10" />
        <ellipse cx="0" cy="0" rx="120" ry="28" fill="none" stroke="rgba(230,226,214,0.6)" strokeWidth="10" />
      </g>
    </svg>
  );
};

// ── КЛИНОК: фигура, красный разрез проходит по диагонали + вспышка, фигура падает ──
const BladeScene: React.FC<{ accent: string }> = ({ accent }) => {
  const f = useCurrentFrame();
  const swipe = interpolate(f, [10, 22], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.in(Easing.cubic) });
  const flash = Math.max(0, 1 - Math.abs(f - 22) / 5);
  const fall = interpolate(f, [26, 60], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.in(Easing.cubic) });
  const rot = fall * 26, drop = fall * 120;
  const fill = lerpCol([232, 226, 214], [150, 26, 26], interpolate(f, [26, 52], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }));
  const x2 = interpolate(swipe, [0, 1], [520, 1400]);
  const y2 = interpolate(swipe, [0, 1], [780, 320]);
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{ background: accent, opacity: flash * 0.45 }} />
      <svg width="1920" height="1080" viewBox="0 0 1920 1080">
        <g transform={`rotate(${rot} 960 620) translate(0 ${drop})`}>
          <Figure x={960} y={540} s={3.6} fill={fill} />
          {/* красный след разреза по телу */}
          {f >= 22 && <line x1="820" y1="700" x2="1100" y2="480" stroke={accent} strokeWidth="8" strokeLinecap="round" opacity={Math.min(1, (f - 22) / 6)} style={{ filter: `drop-shadow(0 0 8px ${accent})` }} />}
        </g>
        {/* сам разрез-клинок */}
        {swipe < 1 && <line x1="520" y1="780" x2={x2} y2={y2} stroke={accent} strokeWidth="9" strokeLinecap="round" style={{ filter: `drop-shadow(0 0 14px ${accent})` }} />}
      </svg>
    </AbsoluteFill>
  );
};

// ── ОГОНЬ: фигура (обугливается, но видна) охвачена растущим пламенем ──
const flamePath = "M0 0 C-16 -34 14 -52 4 -96 C24 -66 30 -40 20 -14 C18 -6 10 0 0 0 Z";
const BurnScene: React.FC<{ accent: string }> = ({ accent }) => {
  const f = useCurrentFrame();
  const rise = interpolate(f, [4, 50], [0.15, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
  const char = interpolate(f, [14, 60], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const fill = lerpCol([236, 228, 214], [150, 40, 26], char); // светлый → раскалённо-обугленный, ВИДЕН сквозь пламя
  const N = 15;
  return (
    <svg width="1920" height="1080" viewBox="0 0 1920 1080">
      {/* тёплое зарево за фигурой */}
      <ellipse cx="960" cy="500" rx={260 * rise} ry={320 * rise} fill={accent} opacity={0.16 * rise} style={{ filter: "blur(40px)" }} />
      <Figure x={960} y={500} s={3.7} fill={fill} />
      <g transform="translate(960 700)">
        {Array.from({ length: N }).map((_, i) => {
          const bx = (i - (N - 1) / 2) * 34;
          const flick = 0.7 + 0.5 * Math.sin(f / 2.4 + i * 1.7);
          const h = rise * (2.8 + 1.4 * flick) * (1 - Math.abs(bx) / 320);
          const sway = Math.sin(f / 4 + i) * 8;
          const col = i % 3 === 0 ? "#ffcc33" : (i % 3 === 1 ? "#ff6a1a" : accent);
          return <path key={i} d={flamePath} transform={`translate(${bx + sway} 0) scale(${2.2 + 0.6 * flick} ${Math.max(0.1, h)})`} fill={col} opacity={0.4 + 0.28 * flick} style={{ filter: `drop-shadow(0 0 14px ${accent}aa)` }} />;
        })}
      </g>
    </svg>
  );
};

const RedVignette = () => (
  <AbsoluteFill style={{ background: "radial-gradient(circle at 50% 52%, rgba(0,0,0,0) 38%, rgba(0,0,0,0.88) 100%)" }} />
);

// ── Бит A: три метафоры зверств по очереди (без текста) ──
const AtrocitiesBeat: React.FC<{ accent: string }> = ({ accent }) => {
  return (
    <AbsoluteFill style={{ background: "#04060c" }}>
      <Sequence from={0} durationInFrames={70}><FadeWrap><StarveScene accent={accent} /></FadeWrap></Sequence>
      <Sequence from={70} durationInFrames={62}><FadeWrap><BladeScene accent={accent} /></FadeWrap></Sequence>
      <Sequence from={132} durationInFrames={78}><FadeWrap><BurnScene accent={accent} /></FadeWrap></Sequence>
      <RedVignette />
    </AbsoluteFill>
  );
};

const FadeWrap: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const f = useCurrentFrame();
  const op = Math.min(interpolate(f, [0, 8], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }), interpolate(f, [999, 1000], [1, 1]));
  return <AbsoluteFill style={{ opacity: op }}>{children}</AbsoluteFill>;
};

// ── крест, проявляется штрихом и трескается красным ──
const Cross: React.FC<{ f0: number; accent: string }> = ({ f0, accent }) => {
  const frame = useCurrentFrame();
  const draw = interpolate(frame, [f0, f0 + 34], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
  const crack = interpolate(frame, [f0 + 40, f0 + 60], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const red = interpolate(frame, [f0 + 44, f0 + 66], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const col = `rgb(${Math.round(244 + (217 - 244) * red)},${Math.round(241 + (40 - 241) * red)},${Math.round(234 + (40 - 234) * red)})`;
  const V = 260, len = 760;
  return (
    <svg width={620} height={860} viewBox="0 0 620 860" style={{ overflow: "visible" }}>
      <line x1="310" y1="40" x2="310" y2="800" stroke={col} strokeWidth="30" strokeLinecap="round" strokeDasharray={len} strokeDashoffset={len * (1 - draw)} style={{ filter: `drop-shadow(0 0 ${20 * red}px ${accent})` }} />
      <line x1="110" y1={V} x2="510" y2={V} stroke={col} strokeWidth="30" strokeLinecap="round" strokeDasharray={400} strokeDashoffset={400 * (1 - Math.max(0, draw * 1.4 - 0.4))} style={{ filter: `drop-shadow(0 0 ${20 * red}px ${accent})` }} />
      <polyline points="298,80 340,300 285,470 355,640 300,790" fill="none" stroke={accent} strokeWidth={5} strokeDasharray={1100} strokeDashoffset={1100 * (1 - crack)} opacity={crack} style={{ filter: `drop-shadow(0 0 8px ${accent})` }} />
    </svg>
  );
};

// ── Бит B: крест трескается (символ, без текста) ──
const FaithBeat: React.FC<{ accent: string }> = ({ accent }) => {
  const frame = useCurrentFrame();
  const exit = interpolate(frame, [190, 210], [1, 0], { extrapolateLeft: "clamp" });
  return (
    <AbsoluteFill style={{ background: "#04060c", opacity: exit, justifyContent: "center", alignItems: "center" }}>
      <Cross f0={16} accent={accent} />
      <RedVignette />
    </AbsoluteFill>
  );
};

export const IntroSequence: React.FC<{ accent?: string }> = ({ accent = PALETTE.red }) => {
  return (
    <AbsoluteFill style={{ background: "#04060c", fontFamily: fontFamily("oswald") }}>
      <Sequence from={0} durationInFrames={210}><AtrocitiesBeat accent={accent} /></Sequence>
      <Sequence from={210} durationInFrames={210}><FaithBeat accent={accent} /></Sequence>
    </AbsoluteFill>
  );
};
