import React from "react";
import { AbsoluteFill, Easing, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { fontFamily } from "./theme";

export type PopulationCollapseProps = {
  title?: string;
  bigNumber?: string;
  sub?: string;
  accent?: string;
};

const rnd = (i: number, s = 1) => {
  const x = Math.sin(i * 73.31 + s * 41.7) * 43758.5453;
  return x - Math.floor(x);
};

// Поле из сотен фигур людей ГАСНЕТ до горстки выживших в центре — «нас было 1280».
export const PopulationCollapse: React.FC<PopulationCollapseProps> = ({
  title = "КРАХ ЧЕЛОВЕЧЕСТВА",
  bigNumber = "1 280",
  sub = "99% предков исчезло",
  accent = "#1fa48a",
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames, width, height } = useVideoConfig();
  const intro = interpolate(frame, [0, 20], [0, 1], { extrapolateRight: "clamp" });
  const exit = interpolate(frame, [durationInFrames - 16, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });

  const N = 260;
  const cxp = width / 2, cyp = height / 2 + 20;
  // прогресс вымирания 0..1
  const collapse = interpolate(frame, [30, durationInFrames - 40], [0, 1], { easing: Easing.inOut(Easing.cubic), extrapolateRight: "clamp" });
  const survivors = 18;

  const figs = Array.from({ length: N }).map((_, i) => {
    const gx = (i % 26), gy = Math.floor(i / 26);
    const x0 = width * 0.13 + gx * ((width * 0.74) / 25);
    const y0 = height * 0.16 + gy * ((height * 0.66) / 9);
    const survives = i < survivors;
    // выжившие сползаются в ПЛОТНУЮ горстку в центр, остальные гаснут
    const ax = survives ? cxp + (rnd(i, 4) - 0.5) * 118 : x0;
    const ay = survives ? cyp + (rnd(i, 5) - 0.5) * 72 : y0;
    const x = interpolate(collapse, [0, 1], [x0, ax]);
    const y = interpolate(collapse, [0, 1], [y0, ay]);
    let op: number;
    if (survives) op = 1;
    else {
      const th = 0.15 + rnd(i, 6) * 0.7; // индивидуальный порог гибели
      op = interpolate(collapse, [th, th + 0.12], [0.5, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
    }
    return { x, y, op, survives };
  });

  const counter = Math.round(interpolate(collapse, [0, 1], [1_280_000, 1280], { extrapolateRight: "clamp" }));

  return (
    <AbsoluteFill style={{ fontFamily: fontFamily("oswald"), opacity: exit }}>
      <AbsoluteFill style={{ background: "radial-gradient(ellipse at 50% 46%, #0a1d21 0%, #06110f 55%, #03080a 100%)" }} />
      <AbsoluteFill style={{ opacity: intro }}>
        <svg width={width} height={height} style={{ position: "absolute" }}>
          {figs.map((f, i) => {
            const sc = f.survives ? interpolate(collapse, [0, 1], [1, 1.9]) : 1;
            return (
              <g key={i} transform={`translate(${f.x},${f.y}) scale(${sc})`} opacity={f.op}
                 style={{ filter: f.survives ? `drop-shadow(0 0 ${5 + collapse * 8}px ${accent})` : "none" }}>
                <circle cx="0" cy="-8" r="4.6" fill={f.survives ? "#eafcf6" : "#8fb7b0"} />
                <path d="M -4.5 -3 Q 0 -5.5 4.5 -3 L 3.4 10 L -3.4 10 Z" fill={f.survives ? accent : "#5f807b"} />
              </g>
            );
          })}
        </svg>
      </AbsoluteFill>
      <AbsoluteFill style={{ boxShadow: "inset 0 0 320px rgba(0,0,0,0.82)", pointerEvents: "none" }} />
      {/* большое число + подпись */}
      <AbsoluteFill style={{ justifyContent: "flex-start", alignItems: "center", paddingTop: 54, opacity: intro * exit }}>
        <div style={{ color: "#8fb7b0", fontSize: 26, fontWeight: 700, letterSpacing: 6 }}>{title}</div>
      </AbsoluteFill>
      <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: 70, opacity: intro * exit }}>
        <div style={{ textAlign: "center" }}>
          <div style={{ color: "#eafcf6", fontSize: 130, fontWeight: 800, lineHeight: 0.9, letterSpacing: 2, textShadow: `0 0 44px ${accent}` }}>
            {counter.toLocaleString("ru-RU")}
          </div>
          <div style={{ color: accent, fontSize: 40, fontWeight: 700, letterSpacing: 3, textTransform: "uppercase", marginTop: 6 }}>{sub}</div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
