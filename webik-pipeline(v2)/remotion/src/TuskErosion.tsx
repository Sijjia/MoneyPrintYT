import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { fontFamily } from "./theme";

export type TuskErosionProps = {
  title?: string;
  sub?: string;
  accent?: string;
};

// Стилизованный слон (силуэт), tusk=0..1 — длина бивней.
const Elephant: React.FC<{ tusk: number; glow: string }> = ({ tusk, glow }) => (
  <g>
    {/* ноги */}
    {[-42, -14, 16, 44].map((x, i) => (
      <rect key={i} x={x} y={20} width={16} height={46} rx={6} fill="#20282b" />
    ))}
    {/* тело */}
    <ellipse cx={0} cy={6} rx={72} ry={46} fill="#2a343a" />
    {/* голова */}
    <circle cx={60} cy={-4} r={38} fill="#2f3a41" />
    {/* ухо */}
    <ellipse cx={50} cy={-8} rx={24} ry={30} fill="#26313a" />
    {/* хобот */}
    <path d="M 86 6 Q 108 26 98 56 Q 94 72 104 84" stroke="#2f3a41" strokeWidth={18} fill="none" strokeLinecap="round" />
    {/* глаз */}
    <circle cx={72} cy={-8} r={3.6} fill="#0c1013" />
    {/* бивни (длина = tusk) */}
    {tusk > 0.02 && [0, 1].map((k) => (
      <path key={k} d={`M ${82 + k * 4} 24 Q ${92 + tusk * 26} ${44 + tusk * 16} ${86 + tusk * 40} ${52 + tusk * 34}`}
        stroke="#ece5d2" strokeWidth={7 - k * 1.5} fill="none" strokeLinecap="round"
        style={{ filter: `drop-shadow(0 0 5px ${glow}55)` }} />
    ))}
  </g>
);

export const TuskErosion: React.FC<TuskErosionProps> = ({
  title = "БИВНИ ИСЧЕЗАЮТ",
  sub = "трофейная охота → обратная эволюция",
  accent = "#1fa48a",
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames, width, height, fps } = useVideoConfig();
  const intro = interpolate(frame, [0, 20], [0, 1], { extrapolateRight: "clamp" });
  const exit = interpolate(frame, [durationInFrames - 16, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });
  const titleIn = interpolate(frame, [12, 30], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  const N = 5;
  const tusks = [1.0, 0.72, 0.45, 0.2, 0.0];
  const years = ["1900", "1950", "1980", "2000", "2020"];
  const spanW = width * 0.82;
  const baseY = height * 0.52;

  return (
    <AbsoluteFill style={{ fontFamily: fontFamily("oswald"), opacity: exit }}>
      <AbsoluteFill style={{ background: "radial-gradient(ellipse at 50% 46%, #0a1f24 0%, #06110f 58%, #03080a 100%)" }} />
      <AbsoluteFill style={{ opacity: intro }}>
        <svg width={width} height={height} style={{ position: "absolute" }}>
          {/* линия земли */}
          <line x1={width * 0.06} y1={baseY + 70} x2={width * 0.94} y2={baseY + 70} stroke="#1c2a2b" strokeWidth={2} />
          {Array.from({ length: N }).map((_, i) => {
            const x = width * 0.09 + spanW * (i / (N - 1));
            const pop = spring({ frame: frame - (18 + i * 12), fps, config: { damping: 13, stiffness: 110 } });
            const last = i === N - 1;
            return (
              <g key={i} transform={`translate(${x}, ${baseY}) scale(${0.7 * Math.max(0.001, pop)})`} opacity={pop}>
                <Elephant tusk={tusks[i]} glow={accent} />
                <text x={0} y={110} fill={last ? accent : "#9fb8b4"} fontSize={26} fontWeight={800} textAnchor="middle"
                  style={{ fontFamily: fontFamily("oswald") }}>{years[i]}</text>
                {last && (
                  <text x={0} y={140} fill={accent} fontSize={22} fontWeight={700} textAnchor="middle"
                    style={{ fontFamily: fontFamily("oswald") }}>БЕЗ БИВНЕЙ</text>
                )}
              </g>
            );
          })}
          {/* стрелка вниз по размеру бивней */}
          <path d={`M ${width * 0.12} ${height * 0.24} L ${width * 0.86} ${height * 0.32}`} stroke={accent} strokeWidth={2}
            strokeDasharray="10 8" opacity={interpolate(frame, [40, 70], [0, 0.6], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })} />
        </svg>
      </AbsoluteFill>
      <AbsoluteFill style={{ boxShadow: "inset 0 0 280px rgba(0,0,0,0.7)", pointerEvents: "none" }} />
      <AbsoluteFill style={{ justifyContent: "flex-start", alignItems: "flex-start", padding: 74, opacity: titleIn * exit }}>
        <div>
          <div style={{ color: "#eafcf6", fontSize: 78, fontWeight: 800, letterSpacing: 2, textShadow: `0 0 30px ${accent}` }}>{title}</div>
          <div style={{ color: accent, fontSize: 32, fontWeight: 700, letterSpacing: 2, textTransform: "uppercase" }}>{sub}</div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
