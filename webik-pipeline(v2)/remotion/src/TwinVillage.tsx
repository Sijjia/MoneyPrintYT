import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { fontFamily } from "./theme";
import { ease, mspring, enterUp } from "./anim";

export type TwinVillageProps = {
  kicker?: string;
  title?: string;
  countText?: string;   // «400»
  countLabel?: string;
  multiplier?: string;  // «×6 нормы»
  accent?: string;
  caption?: string;
  durationInFrames?: number;
};

// Деревня близнецов Кодинхи: сетка одинаковых силуэтов, каждый «дублируется» (copy-paste glitch),
// счётчик пар + «×6 нормы». Ощущение сбоя реальности.
export const TwinVillage: React.FC<TwinVillageProps> = ({
  kicker = "KODINHI",
  title = "THE VILLAGE OF TWINS",
  countText = "400",
  countLabel = "pairs of twins",
  multiplier = "×6 the global average",
  accent = "#6fd0c8",
  caption = "",
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const exit = interpolate(frame, [durationInFrames - 16, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });
  const target = parseInt(countText.replace(/\D/g, "") || "0", 10);
  const cnt = Math.round(mspring(frame, 30, { stiffness: 80, damping: 16, delay: 12 }) * target);

  const cols = 8, rows = 4;
  const Person = ({ dim }: { dim: number }) => (
    <g opacity={dim}>
      <circle cx="0" cy="-26" r="13" fill="#cfeeea" />
      <path d="M0,-13 L0,28 M0,-4 L-16,14 M0,-4 L16,14 M0,28 L-11,54 M0,28 L11,54" stroke="#cfeeea" strokeWidth="7" fill="none" strokeLinecap="round" />
    </g>
  );

  return (
    <AbsoluteFill style={{ fontFamily: fontFamily("oswald"), opacity: exit, overflow: "hidden" }}>
      <AbsoluteFill style={{ background: "radial-gradient(ellipse at 50% 45%, #0e2422 0%, #0a1917 55%, #050d0c 100%)" }} />
      <svg width={1920} height={1080} viewBox="0 0 1920 1080" style={{ position: "absolute", inset: 0 }}>
        {Array.from({ length: cols * rows }).map((_, i) => {
          const c = i % cols, r = Math.floor(i / cols);
          const x = 300 + c * 175, y = 320 + r * 150;
          // появление парами волной
          const s = mspring(frame, 30, { stiffness: 140, damping: 15, delay: 10 + i * 2.2 });
          const on = Math.min(1, s);
          // «дубль» — призрачная копия, сдвинутая, мигает (copy-paste)
          const gx = 26 + Math.sin((frame + i * 9) / 16) * 6;
          const ghost = 0.25 + 0.2 * Math.sin((frame + i * 11) / 10);
          return (
            <g key={i} transform={`translate(${x},${y}) scale(${0.6 + s * 0.4})`} opacity={on}>
              <g transform={`translate(${gx},0)`}><Person dim={ghost} /></g>
              <Person dim={0.95} />
            </g>
          );
        })}
      </svg>

      <AbsoluteFill style={{ justifyContent: "flex-start", alignItems: "flex-start", padding: "78px 90px", opacity: exit }}>
        {(() => { const k = enterUp(frame, 30, 2, 26); const t = enterUp(frame, 30, 8, 42, { stiffness: 125, damping: 18 }); return (<>
          <div style={{ color: accent, fontSize: 30, fontWeight: 700, letterSpacing: 10, opacity: k.opacity, transform: `translateY(${k.translateY}px)` }}>{kicker}</div>
          <div style={{ color: "#e9f7f5", fontSize: 72, fontWeight: 700, lineHeight: 1.02, textShadow: "0 6px 30px rgba(0,0,0,0.85)", marginTop: 6, opacity: t.opacity, transform: `translateY(${t.translateY}px)` }}>{title}</div>
        </>); })()}
      </AbsoluteFill>

      <div style={{ position: "absolute", right: 90, top: 300, textAlign: "right" }}>
        <div style={{ color: "#fff", fontSize: 100, fontWeight: 800, fontVariantNumeric: "tabular-nums", textShadow: `0 0 28px ${accent}`, fontFamily: fontFamily("oswald") }}>{cnt.toLocaleString("ru-RU")}</div>
        <div style={{ color: "#e9f7f5", fontSize: 28, fontWeight: 600 }}>{countLabel}</div>
        <div style={{ marginTop: 12, display: "inline-block", background: accent, color: "#08201e", fontSize: 26, fontWeight: 800, letterSpacing: 1, padding: "8px 18px", borderRadius: 6,
          opacity: interpolate(frame, [40, 54], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) }}>{multiplier}</div>
      </div>

      {caption && (
        <div style={{ position: "absolute", left: 0, right: 0, bottom: 62, textAlign: "center", padding: "0 200px",
          color: "#dcefec", fontSize: 32, fontWeight: 500, textShadow: "0 4px 22px rgba(0,0,0,0.95)", fontFamily: fontFamily("montserrat"),
          opacity: interpolate(frame, [34, 48], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) * exit }}>{caption}</div>
      )}
      <AbsoluteFill style={{ boxShadow: "inset 0 0 300px rgba(0,0,0,0.8)", pointerEvents: "none" }} />
    </AbsoluteFill>
  );
};
