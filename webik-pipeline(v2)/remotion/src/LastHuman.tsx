import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { fontFamily } from "./theme";

export type LastHumanProps = {
  title?: string;
  sub?: string;
  accent?: string;
};

const Skull: React.FC<{ s: number; glow: string; bright: number }> = ({ s, glow, bright }) => (
  <g style={{ filter: `drop-shadow(0 0 ${9 * bright}px ${glow})` }}>
    <ellipse cx="0" cy="0" rx={40 * s} ry={35 * s} fill="#ece5d2" opacity={0.92} />
    <path d={`M ${-35 * s} ${7 * s} Q 0 ${52 * s} ${35 * s} ${7 * s} L ${26 * s} ${30 * s} Q 0 ${46 * s} ${-26 * s} ${30 * s} Z`} fill="#ded6bf" />
    <ellipse cx={-15 * s} cy={5 * s} rx={8 * s} ry={11 * s} fill="#14100a" />
    <ellipse cx={15 * s} cy={5 * s} rx={8 * s} ry={11 * s} fill="#14100a" />
    <path d={`M ${-5 * s} ${12 * s} L 0 ${21 * s} L ${5 * s} ${12 * s}`} fill="#2a2418" />
  </g>
);

// «Мы остались одни»: 4 вида людей, три гаснут с красным крестом (истреблены),
// Homo sapiens остаётся светиться. Под финал темы вымерших видов.
export const LastHuman: React.FC<LastHumanProps> = ({
  title = "МЫ ОСТАЛИСЬ ОДНИ",
  sub = "потому что были опаснее",
  accent = "#1fa48a",
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames, width, height } = useVideoConfig();
  const intro = interpolate(frame, [0, 18], [0, 1], { extrapolateRight: "clamp" });
  const exit = interpolate(frame, [durationInFrames - 16, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });
  const titleIn = interpolate(frame, [durationInFrames * 0.5, durationInFrames * 0.62], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  const names = ["ДЕНИСОВЕЦ", "НЕАНДЕРТАЛЕЦ", "ХОББИТ", "HOMO SAPIENS"];
  const N = 4;
  const spanW = width * 0.72;
  const y = height * 0.42;

  return (
    <AbsoluteFill style={{ fontFamily: fontFamily("oswald"), opacity: exit }}>
      <AbsoluteFill style={{ background: "radial-gradient(ellipse at 50% 42%, #0b2024 0%, #071316 55%, #04090b 100%)" }} />
      <AbsoluteFill style={{ opacity: intro }}>
        <svg width={width} height={height} style={{ position: "absolute" }}>
          {names.map((nm, i) => {
            const x = width / 2 - spanW / 2 + spanW * (i / (N - 1));
            const sapiens = i === N - 1;
            // три вида гаснут по очереди
            const kill = sapiens ? 0 : interpolate(frame, [30 + i * 22, 52 + i * 22], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
            const alive = 1 - kill;
            return (
              <g key={i} transform={`translate(${x},${y})`}>
                <g opacity={sapiens ? 1 : 0.25 + alive * 0.75}>
                  <Skull s={sapiens ? 1.25 : 1} glow={sapiens ? "#eafcf6" : accent} bright={sapiens ? 1.8 : alive} />
                </g>
                <text x="0" y={78} fill={sapiens ? "#eafcf6" : "#7f9995"} fontSize={sapiens ? 30 : 24} fontWeight={800}
                  textAnchor="middle" opacity={sapiens ? 1 : 0.3 + alive * 0.7} style={{ fontFamily: fontFamily("oswald") }}>{nm}</text>
                {/* красный крест на истреблённых */}
                {!sapiens && kill > 0.1 && (
                  <g stroke="#d92828" strokeWidth={7} strokeLinecap="round" opacity={kill} style={{ filter: "drop-shadow(0 0 8px #d92828)" }}>
                    <line x1={-46} y1={-46} x2={46} y2={46} />
                    <line x1={46} y1={-46} x2={-46} y2={46} />
                  </g>
                )}
              </g>
            );
          })}
        </svg>
      </AbsoluteFill>
      <AbsoluteFill style={{ boxShadow: "inset 0 0 300px rgba(0,0,0,0.78)", pointerEvents: "none" }} />
      <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: 90, opacity: titleIn * exit }}>
        <div style={{ textAlign: "center" }}>
          <div style={{ color: "#eafcf6", fontSize: 92, fontWeight: 800, letterSpacing: 3, textShadow: `0 0 34px ${accent}` }}>{title}</div>
          <div style={{ color: accent, fontSize: 34, fontWeight: 700, letterSpacing: 2, textTransform: "uppercase" }}>{sub}</div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
