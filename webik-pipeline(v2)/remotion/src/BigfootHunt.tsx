import { AbsoluteFill, Img, staticFile, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import React from "react";

/** Bigfoot San Andreas: тёмный лес, охотники с фонарями ищут снежного человека,
 *  силуэт мелькает в тумане → «мифа не было» (развенчание) → пасхалка GTA V (человек в костюме).
 *  Капибара слева (липсинк), лес справа. Фазы: hunt / debunk / gtaV. */
export type BFSeg = { from: number; to: number; kind: "hunt" | "debunk" | "gtaV" };
type Txt = { t: string; s: string };
type Props = { mouth?: number[]; segments?: BFSeg[]; accent?: string; L?: Record<string, Txt> };
const RU_BF: Record<string, Txt> = {
  hunt: { t: "ЛЕГЕНДА, КОТОРУЮ ИСКАЛИ ГОДАМИ", s: "San Andreas · 2004" },
  debunk: { t: "БИГФУТА НЕ БЫЛО", s: "все скрины — фотошоп и моды" },
  gtaV: { t: "НАГРАДА В GTA V", s: "…и тот оказался человеком в костюме" },
};

const rnd = (i: number, s = 1) => { const x = Math.sin(i * 12.9898 + s * 78.233) * 43758.5453; return x - Math.floor(x); };

const Tree: React.FC<{ x: number; h: number; shade: number }> = ({ x, h, shade }) => (
  <g transform={`translate(${x},0)`}>
    <rect x={-8} y={1080 - h * 0.28} width={16} height={h * 0.28} fill={`rgb(${shade},${shade + 6},${shade})`} />
    <polygon points={`0,${1080 - h} ${-h * 0.28},${1080 - h * 0.30} ${h * 0.28},${1080 - h * 0.30}`} fill={`rgb(${shade - 4},${shade + 4},${shade - 4})`} />
    <polygon points={`0,${1080 - h * 0.75} ${-h * 0.24},${1080 - h * 0.5} ${h * 0.24},${1080 - h * 0.5}`} fill={`rgb(${shade - 2},${shade + 6},${shade - 2})`} />
  </g>
);

/** охотник с конусом фонаря, конус сканирует */
const Hunter: React.FC<{ x: number; y: number; phase: number; accent: string }> = ({ x, y, phase, accent }) => {
  const f = useCurrentFrame();
  const sweep = Math.sin((f + phase) / 22) * 18;
  const t = Math.sin((f + phase) / 6) * 10;
  return (
    <g transform={`translate(${x},${y})`}>
      {/* конус фонаря */}
      <g transform={`rotate(${sweep - 20})`}>
        <polygon points="10,-38 260,-150 260,60" fill="url(#beam)" opacity={0.5} />
      </g>
      {/* фигура */}
      <line x1={-6} y1={16} x2={-6 + t * 0.3} y2={44} stroke="#0c120c" strokeWidth={7} strokeLinecap="round" />
      <line x1={6} y1={16} x2={6 - t * 0.3} y2={44} stroke="#0c120c" strokeWidth={7} strokeLinecap="round" />
      <rect x={-11} y={-16} width={22} height={34} rx={9} fill="#0c120c" />
      <circle cx={0} cy={-30} r={11} fill="#0c120c" />
      <circle cx={0} cy={-46} r={5} fill={accent} opacity={0.9} />{/* налобный фонарь */}
    </g>
  );
};

export const BigfootHunt: React.FC<Props> = ({ mouth = [], segments = [], accent = "#8be04e", L = RU_BF }) => {
  const frame = useCurrentFrame();
  const { width, height, fps } = useVideoConfig();
  const seg = segments.find((s) => frame >= s.from && frame < s.to) || segments[segments.length - 1];
  const kind = seg?.kind || "hunt";
  const prog = seg ? (frame - seg.from) / Math.max(1, seg.to - seg.from) : 0;

  // капибара
  const mh = height * 0.8, mw = mh * (1370 / 3068), cx = width * 0.19;
  const inn = spring({ frame, fps, config: { damping: 15, stiffness: 90 } });
  const ex = interpolate(inn, [0, 1], [-140, 0]);
  const mopen = interpolate(mouth[frame] ?? 0, [0, 1], [0, 1]);
  const bob = Math.sin(frame / 50) * 4;

  // силуэт бигфута: мелькает в hunt, растворяется в debunk, СОЛИДНЫЙ в gtaV
  const flick = kind === "hunt" ? 0.5 + 0.4 * Math.abs(Math.sin(frame / 42))
    : kind === "debunk" ? interpolate(prog, [0, 0.6], [0.7, 0], { extrapolateRight: "clamp" })
    : 0.98;
  const bfX = kind === "gtaV" ? width * 0.62 : width * (0.5 + Math.sin(frame / 90) * 0.12);
  const zipper = kind === "gtaV" ? interpolate(prog, [0.45, 0.95], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) : 0;

  return (
    <AbsoluteFill style={{ background: "linear-gradient(180deg,#0a140c 0%,#06100a 55%,#040806 100%)" }}>
      <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} style={{ position: "absolute" }}>
        <defs>
          <radialGradient id="beam" cx="0%" cy="50%" r="100%">
            <stop offset="0%" stopColor={accent} stopOpacity={0.7} />
            <stop offset="100%" stopColor={accent} stopOpacity={0} />
          </radialGradient>
          <radialGradient id="moon" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#cfe6d0" stopOpacity={0.9} />
            <stop offset="100%" stopColor="#cfe6d0" stopOpacity={0} />
          </radialGradient>
        </defs>
        {/* луна */}
        <circle cx={width * 0.8} cy={height * 0.2} r={150} fill="url(#moon)" />
        <circle cx={width * 0.8} cy={height * 0.2} r={60} fill="#e8f2e6" opacity={0.85} />
        {/* дальние деревья */}
        {Array.from({ length: 12 }).map((_, i) => (
          <Tree key={"f" + i} x={width * (0.32 + i * 0.06) + rnd(i) * 30} h={height * (0.45 + rnd(i, 2) * 0.25)} shade={18 + Math.floor(rnd(i, 3) * 8)} />
        ))}
        {/* ближние деревья (передний план, темнее) */}
        {Array.from({ length: 5 }).map((_, i) => (
          <Tree key={"n" + i} x={width * (0.30 + i * 0.15)} h={height * (0.8 + rnd(i, 5) * 0.3)} shade={8 + Math.floor(rnd(i, 6) * 5)} />
        ))}
        {/* силуэт бигфута — ПЕРЕД деревьями, светлее + зелёный рим, чтобы читался */}
        <g transform={`translate(${bfX},${height - 470}) scale(1.55)`} opacity={flick}>
          <g fill="#171f24" stroke={accent} strokeWidth={1.6} strokeOpacity={0.55}>
            <ellipse cx={0} cy={70} rx={58} ry={98} />
            <circle cx={0} cy={-25} r={42} />
            <rect x={-72} y={-5} width={32} height={112} rx={15} />
            <rect x={40} y={-5} width={32} height={112} rx={15} />
          </g>
          {/* мех-контур блик */}
          <ellipse cx={0} cy={70} rx={58} ry={98} fill="none" stroke="#cfe6d0" strokeWidth={1} strokeOpacity={0.25} />
          <circle cx={-15} cy={-30} r={6} fill="#c8ff7a" />
          <circle cx={15} cy={-30} r={6} fill="#c8ff7a" />
          {/* «человек в костюме»: молния раскрывает фигуру внутри */}
          {zipper > 0 && (<g>
            <line x1={0} y1={-60} x2={0} y2={150 * zipper - 60} stroke="#ffd23f" strokeWidth={4} />
            <rect x={-18} y={-44} width={36} height={132 * zipper} fill="#2c4a72" opacity={0.95} />
            <circle cx={0} cy={-32} r={14 * (zipper > 0.5 ? 1 : 0)} fill="#e8c9a0" />
          </g>)}
        </g>
        {/* охотники */}
        {kind !== "gtaV" && Array.from({ length: 3 }).map((_, i) => (
          <Hunter key={i} x={width * (0.42 + i * 0.15)} y={height - 60} phase={i * 40} accent={accent} />
        ))}
        {/* туман */}
        {Array.from({ length: 3 }).map((_, i) => {
          const fx = ((frame * (0.4 + i * 0.2) + i * 700) % (width + 600)) - 300;
          return <ellipse key={i} cx={fx} cy={height - 120 - i * 90} rx={420} ry={90} fill="#9fb8a0" opacity={0.06} />;
        })}
      </svg>

      {/* тень + капибара */}
      <div style={{ position: "absolute", left: cx - mw * 0.4, top: height - mh * 0.25, width: mw * 0.8, height: mh * 0.18,
        background: "radial-gradient(ellipse, rgba(0,0,0,.6), transparent 70%)", filter: "blur(6px)" }} />
      <div style={{ position: "absolute", left: cx - mw / 2 + ex, top: height - mh + bob - height * 0.02, width: mw, height: mh }}>
        <Img src={staticFile("mascot/closed.png")} style={{ width: "100%", position: "absolute", top: 0, left: 0 }} />
        <Img src={staticFile("mascot/open.png")} style={{ width: "100%", position: "absolute", top: 0, left: 0, opacity: mopen }} />
      </div>

      {/* текстовые плашки по фазам */}
      <div style={{ position: "absolute", top: height * 0.12, left: 0, width: "100%", textAlign: "center" }}>
        {kind === "hunt" && <Caption title={L.hunt.t} sub={L.hunt.s} accent={accent} />}
        {kind === "debunk" && <Stamp text={L.debunk.t} sub={L.debunk.s} accent="#e0433a" prog={prog} />}
        {kind === "gtaV" && <Caption title={L.gtaV.t} sub={L.gtaV.s} accent={accent} />}
      </div>
      <div style={{ position: "absolute", inset: 0, boxShadow: "inset 0 0 260px rgba(0,0,0,.85)", pointerEvents: "none" }} />
    </AbsoluteFill>
  );
};

const Caption: React.FC<{ title: string; sub: string; accent: string }> = ({ title, sub, accent }) => (
  <div>
    <div style={{ fontSize: 52, fontWeight: 900, color: "#eef3ea", letterSpacing: 1, textShadow: "0 3px 20px #000" }}>{title}</div>
    <div style={{ marginTop: 8, fontSize: 26, color: accent, letterSpacing: 2 }}>{sub}</div>
  </div>
);
const Stamp: React.FC<{ text: string; sub: string; accent: string; prog: number }> = ({ text, sub, accent, prog }) => {
  const pop = interpolate(prog, [0, 0.12], [1.6, 1], { extrapolateRight: "clamp" });
  const rot = interpolate(prog, [0, 0.12], [-14, -8], { extrapolateRight: "clamp" });
  return (
    <div style={{ transform: `scale(${pop}) rotate(${rot}deg)`, display: "inline-block", border: `6px solid ${accent}`,
      padding: "10px 34px", borderRadius: 10, background: "rgba(20,6,6,.6)" }}>
      <div style={{ fontSize: 60, fontWeight: 900, color: accent, letterSpacing: 2 }}>{text}</div>
      <div style={{ fontSize: 24, color: "#e8b4b0", letterSpacing: 1 }}>{sub}</div>
    </div>
  );
};

export default BigfootHunt;
