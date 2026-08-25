import React from "react";
import { AbsoluteFill, Easing, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { fontFamily } from "./theme";

export type VirusGenomeProps = {
  title?: string;
  sub?: string;
  accent?: string;
};

const rnd = (i: number, s = 1) => {
  const x = Math.sin(i * 33.9 + s * 12.1) * 43758.5453;
  return x - Math.floor(x);
};

// Горизонтальная нить ДНК; вирусный капсид спускается и ВСТРАИВАЕТ свой участок —
// сегменты «вирусного» кода светятся вдоль генома (синцитин, «8% — вирус»).
export const VirusGenome: React.FC<VirusGenomeProps> = ({
  title = "8% ТЫ — ВИРУС",
  sub = "древние ретровирусы в ДНК",
  accent = "#1fa48a",
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames, width, height } = useVideoConfig();
  const intro = interpolate(frame, [0, 20], [0, 1], { extrapolateRight: "clamp" });
  const exit = interpolate(frame, [durationInFrames - 16, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });
  const titleIn = interpolate(frame, [16, 36], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  const midY = height * 0.5;
  const rungs = 46;
  const dock = interpolate(frame, [24, 70], [0, 1], { easing: Easing.out(Easing.cubic), extrapolateRight: "clamp" });
  const capX = width * 0.5, capY = interpolate(dock, [0, 1], [-160, midY - 70]);
  const integrate = interpolate(frame, [70, durationInFrames - 30], [0, 1], { extrapolateRight: "clamp" });
  // индексы «вирусных» вставок
  const viral = new Set([6, 7, 8, 19, 20, 33, 34, 35]);

  const capsid = (cx: number, cy: number, r: number, op: number) => {
    const pts = Array.from({ length: 6 }).map((_, k) => {
      const a = (Math.PI / 3) * k - Math.PI / 6;
      return `${cx + Math.cos(a) * r},${cy + Math.sin(a) * r}`;
    }).join(" ");
    return <g opacity={op} style={{ filter: `drop-shadow(0 0 16px ${accent})` }}>
      <polygon points={pts} fill="#0c2b28" stroke={accent} strokeWidth={3} />
      <polygon points={pts} fill="none" stroke="#7fe9d4" strokeWidth={1} opacity={0.6}
        transform={`scale(0.6)`} style={{ transformOrigin: `${cx}px ${cy}px` }} />
      <circle cx={cx} cy={cy} r={r * 0.28} fill={accent} />
      {/* хвостовые нити фага */}
      <line x1={cx} y1={cy + r} x2={cx} y2={cy + r + 20} stroke={accent} strokeWidth={2} />
    </g>;
  };

  return (
    <AbsoluteFill style={{ fontFamily: fontFamily("oswald"), opacity: exit }}>
      <AbsoluteFill style={{ background: "radial-gradient(ellipse at 50% 50%, #0a1f24 0%, #06120f 55%, #03080a 100%)" }} />
      <AbsoluteFill style={{ opacity: intro }}>
        <svg width={width} height={height} style={{ position: "absolute" }}>
          {/* две волнистые рельсы + перекладины */}
          {Array.from({ length: rungs }).map((_, i) => {
            const x = width * 0.08 + i * ((width * 0.84) / (rungs - 1));
            const ph = i * 0.5 + frame * 0.05;
            const yA = midY + Math.sin(ph) * 40;
            const yB = midY - Math.sin(ph) * 40;
            const isViral = viral.has(i);
            const lit = isViral ? (0.35 + 0.65 * integrate) : 1;
            const col = isViral ? accent : "#2f4d49";
            return (
              <g key={i} opacity={0.4 + lit * 0.55}>
                <line x1={x} y1={yA} x2={x} y2={yB} stroke={col} strokeWidth={isViral ? 5 : 3}
                  style={isViral ? { filter: `drop-shadow(0 0 8px ${accent})` } : undefined} />
                <circle cx={x} cy={yA} r={isViral ? 6 : 4} fill={isViral ? "#eafcf6" : "#4b6f6a"} />
                <circle cx={x} cy={yB} r={isViral ? 6 : 4} fill={isViral ? "#eafcf6" : "#4b6f6a"} />
              </g>
            );
          })}
          {/* рельсы (соединяем верхние/нижние точки плавной линией) */}
          {[1, -1].map((sgn, s) => {
            const d = Array.from({ length: rungs }).map((_, i) => {
              const x = width * 0.08 + i * ((width * 0.84) / (rungs - 1));
              const y = midY + sgn * Math.sin(i * 0.5 + frame * 0.05) * 40;
              return `${i === 0 ? "M" : "L"} ${x} ${y}`;
            }).join(" ");
            return <path key={s} d={d} stroke="#3f6b66" strokeWidth={2.5} fill="none" opacity={0.5} />;
          })}
          {capsid(capX, capY, 46, dock)}
        </svg>
      </AbsoluteFill>
      <AbsoluteFill style={{ boxShadow: "inset 0 0 300px rgba(0,0,0,0.8)", pointerEvents: "none" }} />
      <AbsoluteFill style={{ justifyContent: "flex-start", alignItems: "flex-start", padding: 84, opacity: titleIn * exit }}>
        <div>
          <div style={{ color: "#eafcf6", fontSize: 92, fontWeight: 800, letterSpacing: 2, textShadow: `0 0 34px ${accent}` }}>{title}</div>
          <div style={{ color: accent, fontSize: 36, fontWeight: 700, letterSpacing: 3, textTransform: "uppercase" }}>{sub}</div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
