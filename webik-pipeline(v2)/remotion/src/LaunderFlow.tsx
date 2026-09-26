import React from "react";
import {
  AbsoluteFill,
  Easing,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { fontFamily } from "./theme";

export type LaunderFlowProps = {
  steps?: { label: string; sub?: string }[]; // цепочка отмыва
  caption?: string;
  accent?: string;
};

const DEFAULT_STEPS = [
  { label: "КРАДЕНАЯ КАРТА", sub: "чужие деньги" },
  { label: "ПОКУПКА ROBUX", sub: "80 000 R$" },
  { label: "ПЕРЕПРОДАЖА", sub: "со скидкой" },
  { label: "ЧИСТЫЕ ДЕНЬГИ", sub: "на счёт" },
];

// Схема отмыва денег через Robux: узлы-этапы соединяются потоком, деньги «очищаются».
export const LaunderFlow: React.FC<LaunderFlowProps> = ({
  steps = DEFAULT_STEPS, caption = "", accent = "#39d98a",
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames, width } = useVideoConfig();
  const exit = interpolate(frame, [durationInFrames - 12, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });
  const n = steps.length;
  const colDirty = "#e2231a", colClean = accent;

  return (
    <AbsoluteFill style={{ background: "radial-gradient(ellipse at 50% 45%, #12100c 0%, #0a0807 60%, #050403 100%)", fontFamily: fontFamily("oswald"), opacity: exit }}>
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", flexDirection: "row", gap: 0, padding: "0 90px" }}>
        {steps.map((s, i) => {
          const at = 8 + i * 16;
          const app = interpolate(frame, [at, at + 12], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
          // цвет узла плавно от «грязного» к «чистому» по цепочке
          const mix = i / (n - 1);
          const col = i === 0 ? colDirty : i === n - 1 ? colClean : "#c8a24a";
          return (
            <React.Fragment key={i}>
              <div style={{ width: 300, textAlign: "center", opacity: app, transform: `translateY(${interpolate(app, [0, 1], [30, 0])}px)` }}>
                <div style={{ width: 200, height: 200, margin: "0 auto", borderRadius: 24, border: `3px solid ${col}`,
                  background: "linear-gradient(180deg, rgba(20,22,28,0.9), rgba(10,11,15,0.9))", boxShadow: `0 0 40px ${col}44`,
                  display: "flex", alignItems: "center", justifyContent: "center", fontSize: 84 }}>
                  {["💳", "🪙", "🔁", "💵"][i] || "◆"}
                </div>
                <div style={{ color: col, fontSize: 30, fontWeight: 700, letterSpacing: 2, marginTop: 16 }}>{s.label}</div>
                {s.sub && <div style={{ color: "#aab", fontSize: 22, marginTop: 4 }}>{s.sub}</div>}
              </div>
              {i < n - 1 && (
                <div style={{ width: 90, display: "flex", alignItems: "center", justifyContent: "center", opacity: interpolate(frame, [at + 8, at + 18], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) }}>
                  <svg width={90} height={40} viewBox="0 0 90 40">
                    <line x1="0" y1="20" x2="66" y2="20" stroke="#c8a24a" strokeWidth="5" strokeDasharray="8 6" style={{ strokeDashoffset: -frame * 2 }} />
                    <polygon points="66,10 90,20 66,30" fill="#c8a24a" />
                  </svg>
                </div>
              )}
            </React.Fragment>
          );
        })}
      </AbsoluteFill>

      <AbsoluteFill style={{ justifyContent: "flex-start", alignItems: "center", paddingTop: 90 }}>
        <div style={{ color: "#fff", fontSize: 46, fontWeight: 700, letterSpacing: 3, opacity: interpolate(frame, [4, 16], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) }}>
          КАК ОТМЫВАЮТ ДЕНЬГИ ЧЕРЕЗ ROBUX
        </div>
      </AbsoluteFill>

      {caption && (
        <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: 84,
          opacity: interpolate(frame, [22, 36], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) }) * exit }}>
          <div style={{ maxWidth: 1500, textAlign: "center", color: "#f4f1ea", fontSize: 44, fontWeight: 600, textShadow: "0 4px 24px rgba(0,0,0,0.9)", lineHeight: 1.15, borderLeft: `4px solid ${accent}`, borderRight: `4px solid ${accent}`, padding: "6px 34px" }}>{caption}</div>
        </AbsoluteFill>
      )}
      <AbsoluteFill style={{ boxShadow: "inset 0 0 280px rgba(0,0,0,0.85)", pointerEvents: "none" }} />
    </AbsoluteFill>
  );
};
