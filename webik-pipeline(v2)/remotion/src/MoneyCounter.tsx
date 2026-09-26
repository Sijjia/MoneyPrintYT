import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { fontFamily } from "./theme";

export type MoneyCounterProps = {
  number?: string;   // "125" / "350" / "60"
  prefix?: string;   // "−$" / "$" / ""
  suffix?: string;   // " МЛН" / " ЧЕЛОВЕК" / ""
  label?: string;
  sub?: string;
  negative?: boolean;
  accent?: string;
};

// Крупная драматичная цифра со счётчиком: провал/убыток/увольнения.
export const MoneyCounter: React.FC<MoneyCounterProps> = ({
  number = "125", prefix = "−$", suffix = " МЛН", label = "УБЫТОК", sub = "", negative = true,
  accent = "#d9282f",
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames, fps } = useVideoConfig();
  const intro = interpolate(frame, [0, 16], [0, 1], { extrapolateRight: "clamp" });
  const exit = interpolate(frame, [durationInFrames - 14, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });
  const target = parseInt((number || "0").replace(/\D/g, "")) || 0;
  const val = Math.round(interpolate(frame, [10, Math.min(durationInFrames - 20, 70)], [0, target],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }));
  const pop = spring({ frame: frame - 8, fps, config: { damping: 11, stiffness: 130 } });
  const arrow = interpolate(frame, [20, 40], [-30, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ fontFamily: fontFamily("oswald"), opacity: exit,
      background: "radial-gradient(ellipse at 50% 45%, #14090a 0%, #0a0608 55%, #050405 100%)" }}>
      <AbsoluteFill style={{ opacity: 0.05, backgroundImage:
        "repeating-linear-gradient(0deg, #fff 0, #fff 1px, transparent 1px, transparent 3px)" }} />
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", opacity: intro }}>
        <div style={{ textAlign: "center", transform: `scale(${0.9 + 0.1 * pop})` }}>
          <div style={{ color: "#9a9aa2", fontSize: 34, fontWeight: 700, letterSpacing: 6, textTransform: "uppercase" }}>{label}</div>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 18, marginTop: 6 }}>
            {negative && <div style={{ color: accent, fontSize: 90, transform: `translateY(${arrow}px)`, fontWeight: 800 }}>▼</div>}
            <div style={{ color: accent, fontSize: 190, fontWeight: 800, lineHeight: 0.9,
              textShadow: `0 0 44px ${accent}88` }}>{prefix}{val.toLocaleString("ru-RU")}{suffix}</div>
          </div>
          {sub ? <div style={{ color: "#cdd0d0", fontSize: 30, fontWeight: 700, letterSpacing: 2, marginTop: 8, textTransform: "uppercase" }}>{sub}</div> : null}
        </div>
      </AbsoluteFill>
      <AbsoluteFill style={{ boxShadow: "inset 0 0 260px rgba(0,0,0,0.72)", pointerEvents: "none" }} />
    </AbsoluteFill>
  );
};
