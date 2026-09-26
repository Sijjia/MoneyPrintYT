import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { fontFamily } from "./theme";

export type StudioTimelineProps = {
  title?: string;
  events?: { year: string; text: string }[];
  accent?: string;
};

// Хронология событий студии (крах, поглощение). Точки на линии проявляются по очереди.
export const StudioTimeline: React.FC<StudioTimelineProps> = ({
  title = "КРИЗИС СТУДИИ",
  events = [
    { year: "2013", text: "ПРОВАЛ «ХРАНИТЕЛЕЙ СНОВ»" },
    { year: "2014", text: "500 УВОЛЕНЫ, УБЫТКИ" },
    { year: "2016", text: "ПОГЛОЩЕНИЕ COMCAST" },
  ],
  accent = "#d9282f",
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames, width, height } = useVideoConfig();
  const intro = interpolate(frame, [0, 16], [0, 1], { extrapolateRight: "clamp" });
  const exit = interpolate(frame, [durationInFrames - 14, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });
  const N = events.length;
  const x0 = width * 0.12, x1 = width * 0.88, y = height * 0.56;
  const lineGrow = interpolate(frame, [10, 50], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ fontFamily: fontFamily("oswald"), opacity: exit,
      background: "radial-gradient(ellipse at 50% 45%, #101014 0%, #08080b 60%, #040405 100%)" }}>
      <AbsoluteFill style={{ opacity: 0.05, backgroundImage:
        "repeating-linear-gradient(0deg, #fff 0, #fff 1px, transparent 1px, transparent 3px)" }} />
      <AbsoluteFill style={{ justifyContent: "flex-start", alignItems: "center", paddingTop: 70, opacity: intro }}>
        <div style={{ color: "#f2f2f4", fontSize: 66, fontWeight: 800, letterSpacing: 4, textShadow: `0 0 24px ${accent}55` }}>{title}</div>
      </AbsoluteFill>
      <svg width={width} height={height} style={{ position: "absolute" }}>
        <line x1={x0} y1={y} x2={x0 + (x1 - x0) * lineGrow} y2={y} stroke={accent} strokeWidth={3} opacity={0.7} />
        {events.map((e, i) => {
          const x = x0 + (x1 - x0) * (N === 1 ? 0.5 : i / (N - 1));
          const t0 = 20 + i * 12;
          const pop = interpolate(frame, [t0, t0 + 12], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
          const up = i % 2 === 0;
          return (
            <g key={i} opacity={pop} transform={`translate(${x},${y})`}>
              <circle r={11 * pop} fill={accent} style={{ filter: `drop-shadow(0 0 10px ${accent})` }} />
              <line x1={0} y1={0} x2={0} y2={up ? -70 : 70} stroke={accent} strokeWidth={2} opacity={0.5} />
              <text x={0} y={up ? -92 : 100} fill="#fff" fontSize={44} fontWeight={800} textAnchor="middle"
                style={{ fontFamily: fontFamily("oswald") }}>{e.year}</text>
              <text x={0} y={up ? -60 : 132} fill="#b7b7bf" fontSize={22} fontWeight={700} textAnchor="middle"
                style={{ fontFamily: fontFamily("oswald") }}>{e.text}</text>
            </g>
          );
        })}
      </svg>
      <AbsoluteFill style={{ boxShadow: "inset 0 0 240px rgba(0,0,0,0.7)", pointerEvents: "none" }} />
    </AbsoluteFill>
  );
};
