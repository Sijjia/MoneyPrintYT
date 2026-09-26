import { AbsoluteFill, Img, staticFile, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import React from "react";

/** GTA V НЛО: 3 светящиеся тарелки над пиками при 100% → надписи (Segregate=Easter Egg)
 *  → затонувшая тарелка на дне океана → подтверждено Rockstar. Капибара слева. */
export type UFOSeg = { from: number; to: number; kind: "ufos" | "sunken" | "confirmed" };
type Txt = { t: string; s: string };
type Props = { mouth?: number[]; segments?: UFOSeg[]; accent?: string; L?: Record<string, Txt>; segTxt?: string };
const RU_UFO: Record<string, Txt> = {
  ufos: { t: "ТРИ НЛО ПРИ 100%", s: "Чилиад · Сэнди-Шорс · Форт-Занкудо" },
  sunken: { t: "ЗАТОНУВШАЯ ТАРЕЛКА", s: "на дне океана · нужно глубоководное снаряжение" },
  confirmed: { t: "ПОДТВЕРЖДЕНО ROCKSTAR", s: "связь с фреской Чилиад — до сих пор загадка" },
};
const RU_SEG = "= анаграмма «EASTER EGG»";

const Saucer: React.FC<{ x: number; y: number; s: number; glow: number; accent: string; beam?: boolean }> =
({ x, y, s, glow, accent, beam }) => (
  <g transform={`translate(${x},${y}) scale(${s})`}>
    {beam && <polygon points="-70,20 70,20 200,300 -200,300" fill={accent} opacity={0.10 + glow * 0.12} />}
    <ellipse cx={0} cy={20} rx={40} ry={22} fill="#0c1622" stroke={accent} strokeWidth={2} opacity={0.9} />
    <ellipse cx={0} cy={0} rx={100} ry={34} fill="#16283a" stroke={accent} strokeWidth={2.5} />
    <ellipse cx={0} cy={6} rx={100} ry={20} fill="#0b1420" />
    {[-60, -30, 0, 30, 60].map((lx, i) => (
      <circle key={i} cx={lx} cy={8} r={6} fill={accent} opacity={0.5 + 0.5 * Math.abs(Math.sin(glow * 6 + i))} />
    ))}
    <ellipse cx={0} cy={0} rx={112} ry={40} fill="none" stroke={accent} strokeWidth={1} opacity={0.25 + glow * 0.3} />
  </g>
);

const Peak: React.FC<{ x: number; w: number; h: number }> = ({ x, w, h }) => (
  <polygon points={`${x - w},1080 ${x},${1080 - h} ${x + w},1080`} fill="#0a0f18" stroke="#1b2740" strokeWidth={1.5} />
);

export const UFOScene: React.FC<Props> = ({ mouth = [], segments = [], accent = "#5ef0c8", L = RU_UFO, segTxt = RU_SEG }) => {
  const frame = useCurrentFrame();
  const { width, height, fps } = useVideoConfig();
  const seg = segments.find((s) => frame >= s.from && frame < s.to) || segments[segments.length - 1];
  const kind = seg?.kind || "ufos";
  const prog = seg ? (frame - seg.from) / Math.max(1, seg.to - seg.from) : 0;
  const glow = (Math.sin(frame / 18) + 1) / 2;
  const hover = Math.sin(frame / 40) * 10;

  const mh = height * 0.78, mw = mh * (1370 / 3068), cx = width * 0.18;
  const inn = spring({ frame, fps, config: { damping: 15, stiffness: 90 } });
  const ex = interpolate(inn, [0, 1], [-140, 0]);
  const mopen = interpolate(mouth[frame] ?? 0, [0, 1], [0, 1]);
  const bob = Math.sin(frame / 50) * 4;

  const underwater = kind === "sunken" ? interpolate(prog, [0, 0.25], [0, 1], { extrapolateRight: "clamp" }) : (kind === "confirmed" ? 0 : 0);

  return (
    <AbsoluteFill style={{ background: kind === "sunken"
      ? "linear-gradient(180deg,#062038 0%,#041526 60%,#020b14 100%)"
      : "linear-gradient(180deg,#0b0a1e 0%,#0a1226 55%,#060812 100%)" }}>
      <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} style={{ position: "absolute" }}>
        {/* звёзды */}
        {kind !== "sunken" && Array.from({ length: 60 }).map((_, i) => {
          const sx = (i * 137) % width, sy = (i * 89) % (height * 0.6);
          return <circle key={i} cx={sx} cy={sy} r={1.2} fill="#cdd6ff" opacity={0.3 + 0.5 * Math.abs(Math.sin(frame / 30 + i))} />;
        })}

        {kind === "ufos" && (<g>
          {/* пики */}
          <Peak x={width * 0.5} w={220} h={height * 0.5} />
          <Peak x={width * 0.78} w={150} h={height * 0.35} />
          <Peak x={width * 0.34} w={130} h={height * 0.28} />
          {/* 3 тарелки */}
          <Saucer x={width * 0.5} y={height * 0.30 + hover} s={0.9} glow={glow} accent={accent} beam />
          <Saucer x={width * 0.78} y={height * 0.42 - hover} s={0.6} glow={glow} accent={accent} />
          <Saucer x={width * 0.34} y={height * 0.36 + hover * 0.6} s={0.55} glow={glow} accent={accent} />
          {/* человечки смотрят вверх */}
          {Array.from({ length: 4 }).map((_, i) => (
            <g key={i} transform={`translate(${width * (0.42 + i * 0.1)},${height - 40})`}>
              <circle cx={0} cy={-30} r={9} fill="#1a2740" /><rect x={-9} y={-18} width={18} height={28} rx={7} fill="#1a2740" />
              <line x1={-7} y1={-12} x2={-16} y2={-24} stroke="#1a2740" strokeWidth={5} strokeLinecap="round" />
              <line x1={7} y1={-12} x2={16} y2={-24} stroke="#1a2740" strokeWidth={5} strokeLinecap="round" />
            </g>
          ))}
          {/* надпись на тарелке */}
          {prog > 0.45 && (
            <g transform={`translate(${width * 0.5},${height * 0.30 + hover - 60})`} opacity={interpolate(prog, [0.45, 0.6], [0, 1], { extrapolateRight: "clamp" })}>
              <text x={0} y={0} fontSize={22} textAnchor="middle" fill={accent} fontWeight={800} letterSpacing={3}>SEGREGATE</text>
              <text x={0} y={26} fontSize={18} textAnchor="middle" fill="#fff">{segTxt}</text>
            </g>
          )}
        </g>)}

        {kind === "sunken" && (<g opacity={underwater}>
          {/* дно океана + затонувшая тарелка */}
          <rect x={0} y={height * 0.78} width={width} height={height * 0.22} fill="#04101c" />
          <g transform={`translate(${width * 0.58},${height * 0.72}) rotate(-12)`}>
            <Saucer x={0} y={0} s={1.1} glow={glow * 0.5} accent={accent} />
          </g>
          {/* дайвер с фонарём */}
          <g transform={`translate(${width * 0.32 + Math.sin(frame / 30) * 20},${height * 0.5 + Math.cos(frame / 25) * 14})`}>
            <polygon points="18,0 240,-60 240,60" fill={accent} opacity={0.14} />
            <circle cx={0} cy={0} r={13} fill="#1c2a3a" stroke={accent} strokeWidth={2} />
            <rect x={-10} y={12} width={20} height={30} rx={8} fill="#1c2a3a" />
            <line x1={8} y1={20} x2={22} y2={6} stroke="#1c2a3a" strokeWidth={5} strokeLinecap="round" />
          </g>
          {/* пузыри */}
          {Array.from({ length: 14 }).map((_, i) => {
            const by = height - ((frame * 2 + i * 80) % height);
            return <circle key={i} cx={(i * 151) % width} cy={by} r={2 + (i % 3)} fill="#8fd8ff" opacity={0.25} />;
          })}
        </g>)}
      </svg>

      {/* капибара */}
      <div style={{ position: "absolute", left: cx - mw * 0.4, top: height - mh * 0.25, width: mw * 0.8, height: mh * 0.18,
        background: "radial-gradient(ellipse, rgba(0,0,0,.55), transparent 70%)", filter: "blur(6px)" }} />
      <div style={{ position: "absolute", left: cx - mw / 2 + ex, top: height - mh + bob - height * 0.02, width: mw, height: mh }}>
        <Img src={staticFile("mascot/closed.png")} style={{ width: "100%", position: "absolute", top: 0, left: 0 }} />
        <Img src={staticFile("mascot/open.png")} style={{ width: "100%", position: "absolute", top: 0, left: 0, opacity: mopen }} />
      </div>

      {/* заголовки по фазам */}
      <div style={{ position: "absolute", top: height * 0.09, left: 0, width: "100%", textAlign: "center" }}>
        {kind === "ufos" && <><div style={{ fontSize: 50, fontWeight: 900, color: "#eef3ff", textShadow: "0 3px 20px #000" }}>{L.ufos.t}</div>
          <div style={{ fontSize: 24, color: accent, letterSpacing: 2 }}>{L.ufos.s}</div></>}
        {kind === "sunken" && <><div style={{ fontSize: 50, fontWeight: 900, color: "#dff2ff", textShadow: "0 3px 20px #000" }}>{L.sunken.t}</div>
          <div style={{ fontSize: 24, color: accent, letterSpacing: 2 }}>{L.sunken.s}</div></>}
        {kind === "confirmed" && (() => {
          const pop = interpolate(prog, [0, 0.15], [1.5, 1], { extrapolateRight: "clamp" });
          return <div style={{ transform: `scale(${pop})`, display: "inline-block", border: `5px solid ${accent}`, borderRadius: 12, padding: "12px 30px", background: "rgba(6,20,30,.6)" }}>
            <div style={{ fontSize: 46, fontWeight: 900, color: accent }}>{L.confirmed.t}</div>
            <div style={{ fontSize: 22, color: "#cfe0ff" }}>{L.confirmed.s}</div></div>;
        })()}
      </div>
      {kind === "sunken" && <div style={{ position: "absolute", inset: 0, background: "radial-gradient(120% 100% at 50% 40%, rgba(20,80,120,.12), rgba(2,10,20,.5))", pointerEvents: "none" }} />}
      <div style={{ position: "absolute", inset: 0, boxShadow: "inset 0 0 240px rgba(0,0,0,.8)", pointerEvents: "none" }} />
    </AbsoluteFill>
  );
};

export default UFOScene;
