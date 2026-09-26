import { AbsoluteFill, Img, staticFile, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import React from "react";

/** Arion Kurtaj: взлом Rockstar с Fire Stick из отеля → слив GTA VI → приговор + Uber.
 *  Кибер-вайб: дождь кода, терминал, отель, вылетающие «утёкшие клипы». Капибара слева. */
export type KSeg = { from: number; to: number; kind: "breach" | "leak" | "verdict" };
type Txt = { t: string; s: string };
type Props = { mouth?: number[]; segments?: KSeg[]; accent?: string; L?: Record<string, Txt>; fireLabel?: string; leakLabel?: string; leakSub?: string };
const RU_K: Record<string, Txt> = {
  breach: { t: "ВЗЛОМ С FIRE STICK", s: "18 лет · Lapsus$ · под залогом, из номера отеля" },
  verdict: { t: "ПРИГОВОР: БЕССРОЧНО В КЛИНИКЕ", s: "признан невменяемым · декабрь 2023 · + взлом Uber" },
};
const RU_FIRE = "Fire Stick + телефон отеля →";
const RU_LEAKL = "КЛИПОВ GTA VI СЛИТО"; const RU_LEAKS = "крупнейшая утечка в истории игр";
const CH = "01<>{}[]#$@%&/\\ABCDEF0110KURTAJ";

export const KurtajHack: React.FC<Props> = ({ mouth = [], segments = [], accent = "#37e0a0", L = RU_K, fireLabel = RU_FIRE, leakLabel = RU_LEAKL, leakSub = RU_LEAKS }) => {
  const frame = useCurrentFrame();
  const { width, height, fps } = useVideoConfig();
  const seg = segments.find((s) => frame >= s.from && frame < s.to) || segments[segments.length - 1];
  const kind = seg?.kind || "breach";
  const prog = seg ? (frame - seg.from) / Math.max(1, seg.to - seg.from) : 0;

  const mh = height * 0.78, mw = mh * (1370 / 3068), cx = width * 0.17;
  const inn = spring({ frame, fps, config: { damping: 15, stiffness: 90 } });
  const ex = interpolate(inn, [0, 1], [-140, 0]);
  const mopen = interpolate(mouth[frame] ?? 0, [0, 1], [0, 1]);
  const bob = Math.sin(frame / 50) * 4;

  const cols = Math.ceil(width / 26);
  const leaked = kind === "leak" ? Math.floor(interpolate(prog, [0, 0.85], [0, 92], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }))
    : kind === "verdict" ? 92 : Math.floor(prog * 20);

  return (
    <AbsoluteFill style={{ background: "radial-gradient(120% 90% at 62% 30%, #06140f 0%, #05100c 55%, #020806 100%)" }}>
      <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} style={{ position: "absolute" }}>
        {/* дождь кода */}
        {Array.from({ length: cols }).map((_, c) => {
          const speed = 3 + (c % 5); const yhead = ((frame * speed + c * 53) % (height + 300)) - 150;
          return Array.from({ length: 8 }).map((_, k) => {
            const y = yhead - k * 30; const op = interpolate(k, [0, 7], [0.55, 0]);
            const ch = CH[(c * 7 + k + frame) % CH.length];
            return <text key={c + "_" + k} x={c * 26 + 4} y={y} fontSize={18} fill={accent} opacity={op} fontFamily="monospace">{ch}</text>;
          });
        })}

        {/* отель: кровать + ТВ + Fire Stick (в breach) */}
        {kind === "breach" && (<g opacity={0.9}>
          <rect x={width * 0.60} y={height * 0.55} width={width * 0.30} height={height * 0.12} rx={10} fill="#12211a" stroke={accent} strokeWidth={1.5} />
          <rect x={width * 0.60} y={height * 0.5} width={width * 0.10} height={height * 0.06} rx={8} fill="#1a2b22" />
          {/* ТВ на стене */}
          <rect x={width * 0.66} y={height * 0.22} width={width * 0.20} height={height * 0.20} rx={8} fill="#0a1410" stroke={accent} strokeWidth={2} />
          <text x={width * 0.76} y={height * 0.30} fontSize={26} textAnchor="middle" fill={accent} fontWeight={800}>ROCKSTAR</text>
          <text x={width * 0.76} y={height * 0.35} fontSize={20} textAnchor="middle" fill="#fff">SERVERS · ACCESS</text>
          <text x={width * 0.76} y={height * 0.395} fontSize={22} textAnchor="middle" fill={accent} fontWeight={900}
            opacity={0.4 + 0.6 * Math.abs(Math.sin(frame / 10))}>GRANTED</text>
          {/* Fire Stick + телефон */}
          <rect x={width * 0.855} y={height * 0.31} width={30} height={12} rx={3} fill="#e0433a" />
          <text x={width * 0.70} y={height * 0.62} fontSize={16} fill={accent}>{fireLabel}</text>
        </g>)}

        {/* вылетающие утёкшие клипы (leak) */}
        {kind !== "breach" && Array.from({ length: 10 }).map((_, i) => {
          const t = ((frame * 1.4 + i * 30) % 130) / 130;
          const sx = width * 0.5, sy = height * 0.55;
          const ang = (i / 10) * Math.PI * 2;
          const x = sx + Math.cos(ang) * t * width * 0.5;
          const y = sy + Math.sin(ang) * t * height * 0.45;
          return <g key={i} opacity={interpolate(t, [0, 0.1, 0.85, 1], [0, 1, 1, 0])} transform={`translate(${x},${y}) rotate(${t * 60})`}>
            <rect x={-28} y={-18} width={56} height={36} rx={4} fill="#0c1a14" stroke={accent} strokeWidth={1.5} />
            <text x={0} y={5} fontSize={13} textAnchor="middle" fill={accent} fontWeight={800}>GTA VI</text>
          </g>;
        })}
      </svg>

      {/* капибара */}
      <div style={{ position: "absolute", left: cx - mw * 0.4, top: height - mh * 0.25, width: mw * 0.8, height: mh * 0.18,
        background: "radial-gradient(ellipse, rgba(0,0,0,.55), transparent 70%)", filter: "blur(6px)" }} />
      <div style={{ position: "absolute", left: cx - mw / 2 + ex, top: height - mh + bob - height * 0.02, width: mw, height: mh }}>
        <Img src={staticFile("mascot/closed.png")} style={{ width: "100%", position: "absolute", top: 0, left: 0 }} />
        <Img src={staticFile("mascot/open.png")} style={{ width: "100%", position: "absolute", top: 0, left: 0, opacity: mopen }} />
      </div>

      {/* заголовки + счётчик слива */}
      <div style={{ position: "absolute", top: height * 0.08, left: 0, width: "100%", textAlign: "center" }}>
        {kind === "breach" && <><div style={{ fontSize: 48, fontWeight: 900, color: "#e9fff5", textShadow: "0 3px 20px #000" }}>{L.breach.t}</div>
          <div style={{ fontSize: 24, color: accent }}>{L.breach.s}</div></>}
        {kind === "leak" && <><div style={{ fontSize: 96, fontWeight: 900, color: "#fff", fontVariantNumeric: "tabular-nums", textShadow: `0 0 40px ${accent}` }}>{leaked}</div>
          <div style={{ fontSize: 30, fontWeight: 800, color: accent, letterSpacing: 3 }}>{leakLabel}</div>
          <div style={{ fontSize: 22, color: "#bfe" }}>{leakSub}</div></>}
        {kind === "verdict" && (() => { const pop = interpolate(prog, [0, 0.15], [1.5, 1], { extrapolateRight: "clamp" });
          return <div style={{ transform: `scale(${pop})`, display: "inline-block", border: `5px solid #e0433a`, borderRadius: 12, padding: "12px 30px", background: "rgba(30,8,8,.6)" }}>
            <div style={{ fontSize: 44, fontWeight: 900, color: "#ff6a60" }}>{L.verdict.t}</div>
            <div style={{ fontSize: 22, color: "#ffd0cc" }}>{L.verdict.s}</div></div>;
        })()}
      </div>
      <div style={{ position: "absolute", inset: 0, boxShadow: "inset 0 0 240px rgba(0,0,0,.85)", pointerEvents: "none" }} />
    </AbsoluteFill>
  );
};

export default KurtajHack;
