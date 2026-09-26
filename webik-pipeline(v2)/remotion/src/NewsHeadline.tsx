import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { fontFamily } from "./theme";

export type NewsHeadlineProps = {
  headline?: string;
  source?: string;
  date?: string;
  accent?: string;
};

// Газетный заголовок: увольнения, поглощение, война с кинотеатрами.
export const NewsHeadline: React.FC<NewsHeadlineProps> = ({
  headline = "DREAMWORKS УВОЛЬНЯЕТ 350 СОТРУДНИКОВ",
  source = "THE HOLLYWOOD REPORTER", date = "2013", accent = "#d9282f",
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames, width, fps } = useVideoConfig();
  const exit = interpolate(frame, [durationInFrames - 14, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });
  const slam = spring({ frame: frame - 6, fps, config: { damping: 12, stiffness: 160 } });
  const paperY = interpolate(slam, [0, 1], [80, 0]);
  const rot = interpolate(slam, [0, 1], [-3, -1.2]);

  return (
    <AbsoluteFill style={{ fontFamily: fontFamily("oswald"), opacity: exit,
      background: "radial-gradient(ellipse at 50% 40%, #16161a 0%, #0a0a0d 60%, #050506 100%)" }}>
      {/* газетный лист */}
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
        <div style={{ width: width * 0.72, background: "#ece7db", color: "#12100c", padding: "40px 46px",
          transform: `translateY(${paperY}px) rotate(${rot}deg)`, opacity: slam,
          boxShadow: "0 40px 90px rgba(0,0,0,0.6)", border: "1px solid #cfc8b8" }}>
          {/* масти-хед */}
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end",
            borderBottom: "3px solid #12100c", paddingBottom: 8 }}>
            <span style={{ fontSize: 30, fontWeight: 800, letterSpacing: 2, fontFamily: "Georgia, serif" }}>{source}</span>
            <span style={{ fontSize: 20, fontWeight: 700, color: "#4a463c" }}>{date}</span>
          </div>
          {/* заголовок */}
          <div style={{ fontSize: 74, fontWeight: 800, lineHeight: 1.02, marginTop: 22, fontFamily: "Georgia, serif",
            letterSpacing: -1 }}>{headline}</div>
          {/* колонки-текст (редакт) */}
          <div style={{ display: "flex", gap: 26, marginTop: 26 }}>
            {[0, 1, 2].map((c) => (
              <div key={c} style={{ flex: 1 }}>
                {Array.from({ length: 7 }).map((_, i) => {
                  const w = 55 + ((i * 37 + c * 13) % 45);
                  const show = interpolate(frame, [20 + i * 2 + c, 26 + i * 2 + c], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
                  return <div key={i} style={{ height: 7, width: `${w}%`, background: "#8a8577",
                    marginBottom: 8, opacity: 0.5 * show, borderRadius: 2 }} />;
                })}
              </div>
            ))}
          </div>
        </div>
      </AbsoluteFill>
      {/* красная печать поверх */}
      <AbsoluteFill style={{ justifyContent: "flex-start", alignItems: "flex-end", padding: 70,
        opacity: interpolate(frame, [24, 34], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) }}>
        <div style={{ color: accent, border: `4px solid ${accent}`, borderRadius: 8, padding: "6px 16px",
          fontSize: 30, fontWeight: 800, letterSpacing: 3, transform: "rotate(8deg)", opacity: 0.9 }}>ФАКТ</div>
      </AbsoluteFill>
      <AbsoluteFill style={{ boxShadow: "inset 0 0 240px rgba(0,0,0,0.6)", pointerEvents: "none" }} />
    </AbsoluteFill>
  );
};
