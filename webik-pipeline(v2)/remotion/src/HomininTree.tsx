import React from "react";
import { AbsoluteFill, Easing, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { fontFamily } from "./theme";

export type HomininTreeProps = {
  title?: string;
  accent?: string;
  species?: { name: string; cranium: number }[];
};

const DEF = [
  { name: "ДЕНИСОВЕЦ", cranium: 1.05 },
  { name: "НЕАНДЕРТАЛЕЦ", cranium: 1.15 },
  { name: "ХОББИТ ФЛОРЕСА", cranium: 0.55 },
  { name: "HOMO SAPIENS", cranium: 1.0 },
];

// Стилизованный череп гоминида (SVG): свод, надбровье, глазницы, челюсть. Костяной.
const Skull: React.FC<{ s: number; glow: string; bright: number }> = ({ s, glow, bright }) => (
  <g style={{ filter: `drop-shadow(0 0 ${8 * bright}px ${glow})` }}>
    <ellipse cx="0" cy="0" rx={34 * s} ry={30 * s} fill="#ece5d2" opacity={0.9} />
    <path d={`M ${-30 * s} ${6 * s} Q 0 ${44 * s} ${30 * s} ${6 * s} L ${22 * s} ${26 * s} Q 0 ${40 * s} ${-22 * s} ${26 * s} Z`} fill="#ded6bf" />
    <path d={`M ${-26 * s} ${-4 * s} Q 0 ${-14 * s} ${26 * s} ${-4 * s}`} stroke="#b9ad8f" strokeWidth={4 * s} fill="none" />
    <ellipse cx={-13 * s} cy={4 * s} rx={7 * s} ry={9 * s} fill="#14100a" />
    <ellipse cx={13 * s} cy={4 * s} rx={7 * s} ry={9 * s} fill="#14100a" />
    <path d={`M ${-4 * s} ${10 * s} L 0 ${18 * s} L ${4 * s} ${10 * s}`} fill="#2a2418" />
  </g>
);

export const HomininTree: React.FC<HomininTreeProps> = ({
  title = "ДЕРЕВО ЛЮДЕЙ",
  accent = "#1fa48a",
  species = DEF,
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames, width, height, fps } = useVideoConfig();
  const intro = interpolate(frame, [0, 22], [0, 1], { extrapolateRight: "clamp" });
  const exit = interpolate(frame, [durationInFrames - 16, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });
  const push = interpolate(frame, [0, durationInFrames], [1.02, 1.12], { easing: Easing.inOut(Easing.sin) });
  const titleIn = interpolate(frame, [12, 32], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  const rootX = width / 2, rootY = height - 120;
  const n = species.length;
  const spanW = width * 0.66;
  const nodes = species.map((sp, i) => ({
    ...sp,
    x: width / 2 - spanW / 2 + spanW * (i / (n - 1)),
    y: height * 0.30 + (i % 2) * 46,
    hi: sp.name.includes("SAPIENS"),
  }));

  return (
    <AbsoluteFill style={{ fontFamily: fontFamily("oswald"), opacity: exit }}>
      <AbsoluteFill style={{ background: "radial-gradient(ellipse at 50% 40%, #0b2024 0%, #071316 50%, #04090b 100%)" }} />
      <AbsoluteFill style={{ transform: `scale(${push})`, opacity: intro }}>
        <svg width={width} height={height} style={{ position: "absolute" }}>
          {/* ствол + ветви */}
          <path d={`M ${rootX} ${rootY} C ${rootX} ${rootY - 200}, ${width / 2} ${height * 0.62}, ${width / 2} ${height * 0.55}`}
            stroke={accent} strokeWidth={7} fill="none" opacity={0.5} style={{ filter: `drop-shadow(0 0 10px ${accent})` }} />
          {nodes.map((nd, i) => {
            const grow = interpolate(frame, [18 + i * 8, 46 + i * 8], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
            const midY = height * 0.55;
            return (
              <path key={i}
                d={`M ${width / 2} ${midY} C ${width / 2} ${midY - 60}, ${nd.x} ${nd.y + 120}, ${nd.x} ${nd.y + 46}`}
                stroke={nd.hi ? "#eafcf6" : accent} strokeWidth={nd.hi ? 5 : 3.4} fill="none"
                strokeDasharray={900} strokeDashoffset={900 * (1 - grow)}
                opacity={0.35 + grow * 0.5} style={{ filter: `drop-shadow(0 0 8px ${accent})` }} />
            );
          })}
          {/* черепа + подписи */}
          {nodes.map((nd, i) => {
            const pop = spring({ frame: frame - (30 + i * 8), fps, config: { damping: 12, stiffness: 120 } });
            return (
              <g key={i} transform={`translate(${nd.x}, ${nd.y}) scale(${Math.max(0.001, pop)})`}>
                <g transform={`scale(${nd.cranium})`}>
                  <Skull s={1} glow={nd.hi ? "#eafcf6" : accent} bright={nd.hi ? 1.8 : 1} />
                </g>
                <text x="0" y={78} fill={nd.hi ? "#eafcf6" : "#cfe8e2"} fontSize={nd.hi ? 30 : 25}
                  fontWeight={800} textAnchor="middle" style={{ fontFamily: fontFamily("oswald") }}>{nd.name}</text>
              </g>
            );
          })}
        </svg>
      </AbsoluteFill>
      <AbsoluteFill style={{ boxShadow: "inset 0 0 300px rgba(0,0,0,0.78)", pointerEvents: "none" }} />
      <AbsoluteFill style={{ justifyContent: "flex-start", alignItems: "flex-start", padding: 80, opacity: titleIn * exit }}>
        <div style={{ color: "#eafcf6", fontSize: 74, fontWeight: 800, letterSpacing: 2, textShadow: `0 0 34px ${accent}` }}>{title}</div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
