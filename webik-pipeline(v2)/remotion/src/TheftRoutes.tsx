import React from "react";
import {
  AbsoluteFill,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { PALETTE, fontFamily } from "./theme";

export type TheftRoutesProps = {
  title?: string;
  accent?: string;
};

// Карта маршрутов краж: КНДР-хаб → дуги к АЗИИ и АФРИКЕ, по ним бегут $.
export const TheftRoutes: React.FC<TheftRoutesProps> = ({
  title = "МАРШРУТЫ КРАЖ",
  accent = "#ff5050",
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const exit = interpolate(frame, [durationInFrames - 14, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });

  const W = 1920, H = 1080;
  const nk = { x: 1180, y: 360 };        // КНДР
  const nodes = [
    { x: 560, y: 560, label: "АЗИЯ" },
    { x: 470, y: 850, label: "АФРИКА" },
    { x: 300, y: 420, label: "ЕВРОПА" },
  ];

  const arc = (a: { x: number; y: number }, b: { x: number; y: number }) => {
    const mx = (a.x + b.x) / 2, my = (a.y + b.y) / 2 - 180;
    return { d: `M${a.x} ${a.y} Q${mx} ${my} ${b.x} ${b.y}`, mx, my };
  };
  const bez = (a: any, b: any, m: any, t: number) => ({
    x: (1 - t) * (1 - t) * a.x + 2 * (1 - t) * t * m.x + t * t * b.x,
    y: (1 - t) * (1 - t) * a.y + 2 * (1 - t) * t * m.y + t * t * b.y,
  });

  return (
    <AbsoluteFill style={{ fontFamily: fontFamily("oswald"), opacity: exit }}>
      <AbsoluteFill style={{ background: "radial-gradient(circle at 60% 35%, #16090a 0%, #0b0405 55%, #060202 100%)" }} />
      {/* сетка-глобус */}
      <svg width={W} height={H} style={{ position: "absolute", inset: 0, opacity: 0.18 }}>
        {Array.from({ length: 12 }).map((_, i) => <line key={`h${i}`} x1={0} y1={i * 90} x2={W} y2={i * 90} stroke="#5a7ca0" strokeWidth="1" />)}
        {Array.from({ length: 20 }).map((_, i) => <line key={`v${i}`} x1={i * 100} y1={0} x2={i * 100} y2={H} stroke="#5a7ca0" strokeWidth="1" />)}
      </svg>

      <svg width={W} height={H} style={{ position: "absolute", inset: 0 }}>
        {nodes.map((n, i) => {
          const { d, mx, my } = arc(nk, n);
          const m = { x: mx, y: my };
          const rev = interpolate(frame, [i * 6, i * 6 + 26], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
          return (
            <g key={i}>
              <path d={d} fill="none" stroke={`${accent}`} strokeWidth="4" strokeDasharray="14 10" strokeDashoffset={-frame * 3} opacity={0.35 + 0.5 * rev} style={{ filter: `drop-shadow(0 0 6px ${accent})` }} pathLength={1} />
              {/* бегущие $ */}
              {[0, 0.33, 0.66].map((off, k) => {
                const t = ((frame / 60 + off) % 1);
                const p = bez(nk, n, m, t);
                return <g key={k} opacity={rev}><circle cx={p.x} cy={p.y} r="16" fill="#0b0404" stroke={accent} strokeWidth="2" /><text x={p.x} y={p.y + 7} textAnchor="middle" fill={accent} fontSize="20" fontWeight="800">$</text></g>;
              })}
              {/* узел */}
              <circle cx={n.x} cy={n.y} r="14" fill={accent} style={{ filter: `drop-shadow(0 0 12px ${accent})` }} opacity={rev} />
              <text x={n.x} y={n.y + 54} textAnchor="middle" fill={PALETTE.cream} fontSize="34" fontWeight="700" opacity={rev} style={{ fontFamily: fontFamily("oswald") }}>{n.label}</text>
            </g>
          );
        })}
        {/* хаб КНДР */}
        <circle cx={nk.x} cy={nk.y} r={24 + Math.sin(frame / 6) * 4} fill={accent} style={{ filter: `drop-shadow(0 0 20px ${accent})` }} />
        <circle cx={nk.x} cy={nk.y} r={44} fill="none" stroke={accent} strokeWidth="2" opacity="0.5" />
        <text x={nk.x} y={nk.y - 44} textAnchor="middle" fill={PALETTE.cream} fontSize="40" fontWeight="800" style={{ fontFamily: fontFamily("oswald") }}>КНДР</text>
      </svg>

      <AbsoluteFill style={{ boxShadow: "inset 0 0 300px rgba(0,0,0,0.8)", pointerEvents: "none" }} />

      <AbsoluteFill style={{ justifyContent: "flex-start", alignItems: "flex-start", padding: 70, opacity: interpolate(frame, [10, 26], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) * exit }}>
        <div>
          <div style={{ color: PALETTE.cream, fontSize: 72, fontWeight: 800, letterSpacing: 4, textTransform: "uppercase", textShadow: `0 0 30px ${accent}` }}>{title}</div>
          <div style={{ color: accent, fontSize: 30, letterSpacing: 3, fontWeight: 600 }}>ВЫВОД ЧЕРЕЗ ПОДСТАВНЫЕ СЧЕТА</div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
