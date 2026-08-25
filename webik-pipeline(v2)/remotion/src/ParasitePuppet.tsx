import React from "react";
import { AbsoluteFill, Easing, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { fontFamily } from "./theme";

export type ParasitePuppetProps = {
  title?: string;
  sub?: string;
  accent?: string;
};

const rnd = (i: number, s = 1) => {
  const x = Math.sin(i * 63.7 + s * 27.3) * 43758.5453;
  return x - Math.floor(x);
};

// Муравей-зомби: из головы прорастает стебель кордицепса, сверху — нити-марионетки,
// вокруг дрейфуют споры. Жутко, органично.
export const ParasitePuppet: React.FC<ParasitePuppetProps> = ({
  title = "КУКЛОВОД",
  sub = "гриб управляет телом",
  accent = "#8fd14f",
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames, width, height } = useVideoConfig();
  const intro = interpolate(frame, [0, 20], [0, 1], { extrapolateRight: "clamp" });
  const exit = interpolate(frame, [durationInFrames - 16, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });
  const titleIn = interpolate(frame, [14, 34], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  const cx = width * 0.44, cy = height * 0.62;
  const sway = Math.sin(frame / 22) * 4;
  const stalk = interpolate(frame, [20, durationInFrames - 30], [0, 1], { easing: Easing.out(Easing.cubic), extrapolateRight: "clamp" });
  const stalkH = 220 * stalk;

  return (
    <AbsoluteFill style={{ fontFamily: fontFamily("oswald"), opacity: exit }}>
      <AbsoluteFill style={{ background: "radial-gradient(ellipse at 44% 55%, #0e1e10 0%, #08130a 55%, #040806 100%)" }} />
      {/* споры */}
      <AbsoluteFill style={{ opacity: intro }}>
        {Array.from({ length: 40 }).map((_, i) => {
          const p = (frame * (0.3 + rnd(i, 3) * 0.6) + rnd(i, 1) * 800) % (height + 60);
          return <div key={i} style={{
            position: "absolute", left: `${20 + rnd(i, 2) * 60}%`, top: height - p,
            width: 3 + rnd(i, 5) * 3, height: 3 + rnd(i, 5) * 3, borderRadius: "50%",
            background: accent, opacity: 0.12 + rnd(i, 6) * 0.28, filter: `blur(${rnd(i, 7) * 1.6}px)`,
            boxShadow: `0 0 8px ${accent}`,
          }} />;
        })}
      </AbsoluteFill>

      <AbsoluteFill style={{ opacity: intro }}>
        <svg width={width} height={height} style={{ position: "absolute" }}>
          {/* нити-марионетки сверху к телу */}
          {[[-40, "голова"], [10, "грудь"], [55, "брюшко"]].map(([dx], k) => (
            <line key={k} x1={cx + (dx as number) + sway * 0.4} y1={0} x2={cx + (dx as number)} y2={cy - 10 + k * 8}
              stroke="#dfeecb" strokeWidth={1.4} opacity={0.35} />
          ))}
          <g transform={`translate(${cx + sway}, ${cy})`}>
            {/* стебель кордицепса из головы */}
            <path d={`M -46 -10 q -14 ${-stalkH * 0.5} -6 ${-stalkH}`} stroke="#b7d98a" strokeWidth={7} fill="none"
              style={{ filter: `drop-shadow(0 0 10px ${accent})` }} opacity={0.9} />
            <circle cx={-52 - 0} cy={-10 - stalkH} r={12 + 6 * stalk} fill={accent}
              style={{ filter: `drop-shadow(0 0 16px ${accent})` }} opacity={0.9} />
            {/* тело муравья (профиль): 3 сегмента */}
            <ellipse cx={40} cy={0} rx={34} ry={22} fill="#1a1410" stroke="#3a2f22" strokeWidth={2} />
            <ellipse cx={2} cy={-2} rx={16} ry={14} fill="#221a13" stroke="#3a2f22" strokeWidth={2} />
            <ellipse cx={-40} cy={-8} rx={20} ry={17} fill="#241b12" stroke="#3a2f22" strokeWidth={2} />
            {/* глаз + жвалы */}
            <circle cx={-46} cy={-10} r={3.4} fill={accent} style={{ filter: `drop-shadow(0 0 5px ${accent})` }} />
            <path d="M -58 -4 q -10 2 -14 -4" stroke="#3a2f22" strokeWidth={2.4} fill="none" />
            {/* усики */}
            <path d="M -50 -18 q -14 -14 -4 -26" stroke="#2c2116" strokeWidth={2.4} fill="none" />
            {/* лапки (вцепился в лист) */}
            {[-18, 4, 26].map((lx, i) => (
              <g key={i} stroke="#2c2116" strokeWidth={2.6} fill="none">
                <path d={`M ${lx} 14 q ${6 - i * 3} 20 ${-6} 34`} />
                <path d={`M ${lx + 8} 14 q ${10 - i * 3} 22 ${2} 36`} />
              </g>
            ))}
            {/* лист-опора */}
            <path d="M -70 52 Q 30 40 90 54 Q 20 66 -70 60 Z" fill="#12301a" stroke="#1e4a29" strokeWidth={2} opacity={0.9} />
          </g>
        </svg>
      </AbsoluteFill>

      <AbsoluteFill style={{ boxShadow: "inset 0 0 300px rgba(0,0,0,0.8)", pointerEvents: "none" }} />
      <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "flex-end", padding: 90, opacity: titleIn * exit }}>
        <div style={{ textAlign: "right" }}>
          <div style={{ color: "#eafcf6", fontSize: 96, fontWeight: 800, letterSpacing: 3, textShadow: `0 0 34px ${accent}` }}>{title}</div>
          <div style={{ color: accent, fontSize: 38, fontWeight: 700, letterSpacing: 3, textTransform: "uppercase" }}>{sub}</div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
