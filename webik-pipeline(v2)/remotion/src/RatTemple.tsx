import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { fontFamily } from "./theme";
import { ease, mspring, enterUp } from "./anim";

export type RatTempleProps = {
  kicker?: string;
  title?: string;
  countText?: string;   // «25 000»
  countLabel?: string;
  accent?: string;
  caption?: string;
  durationInFrames?: number;
};

const rnd = (i: number, s = 1) => { const x = Math.sin(i * 33.7 + s * 7.1) * 43758.5; return x - Math.floor(x); };

// Храм Карни Мата: мраморный зал, пол «кишит» движущимися крысами-силуэтами, счётчик 25000,
// одна БЕЛАЯ крыса светится (удача), миски с молоком.
export const RatTemple: React.FC<RatTempleProps> = ({
  kicker = "KARNI MATA TEMPLE",
  title = "25,000 SACRED RATS",
  countText = "25 000",
  countLabel = "sacred rats in the temple",
  accent = "#c9a24a",
  caption = "",
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const exit = interpolate(frame, [durationInFrames - 16, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });
  const appear = interpolate(frame, [0, 30], [0, 1], { extrapolateRight: "clamp", easing: ease.expoOut });
  const target = parseInt(countText.replace(/\D/g, "") || "0", 10);
  const cnt = Math.round(mspring(frame, 30, { stiffness: 60, damping: 18, delay: 10 }) * target);

  const Rat = ({ x, y, s, ph }: { x: number; y: number; s: number; ph: number }) => {
    const wx = x + Math.sin((frame + ph) / 18) * 26;
    const wy = y + Math.cos((frame + ph) / 24) * 12;
    return (
      <g transform={`translate(${wx},${wy}) scale(${s})`} opacity="0.9">
        <ellipse cx="0" cy="0" rx="13" ry="7" fill="#20140c" />
        <circle cx="11" cy="-2" r="4" fill="#20140c" />
        <path d="M-13,0 q-16,3 -22,-4" fill="none" stroke="#20140c" strokeWidth="2" />
      </g>
    );
  };

  return (
    <AbsoluteFill style={{ fontFamily: fontFamily("oswald"), opacity: exit, overflow: "hidden" }}>
      <AbsoluteFill style={{ background: "linear-gradient(180deg,#2a2118 0%,#211a12 45%,#161009 100%)" }} />
      {/* мраморные арки храма */}
      <svg width={1920} height={1080} viewBox="0 0 1920 1080" style={{ position: "absolute", inset: 0, opacity: appear * 0.6 }}>
        {[300, 700, 1100, 1500].map((x, i) => (
          <path key={i} d={`M${x},700 L${x},360 Q${x + 100},270 ${x + 200},360 L${x + 200},700`} fill="none" stroke="#4a3c28" strokeWidth="10" opacity="0.5" />
        ))}
        <rect x="0" y="690" width="1920" height="390" fill="#2c2115" opacity="0.6" />
        {/* миски с молоком */}
        {[420, 960, 1500].map((x, i) => <ellipse key={i} cx={x} cy={840 + i * 10} rx="70" ry="20" fill="#d9cdb0" opacity="0.5" />)}
      </svg>

      {/* пол кишит крысами */}
      <svg width={1920} height={1080} viewBox="0 0 1920 1080" style={{ position: "absolute", inset: 0, opacity: appear }}>
        {Array.from({ length: 150 }).map((_, i) => {
          const x = rnd(i, 1) * 1920;
          const y = 700 + rnd(i, 2) * 360;
          const s = 0.7 + rnd(i, 3) * 0.9 + (y - 700) / 500;
          return <Rat key={i} x={x} y={y} s={s} ph={i * 13} />;
        })}
        {/* белая крыса — удача */}
        {(() => { const wx = 960 + Math.sin(frame / 20) * 40; const wy = 820 + Math.cos(frame / 26) * 16; const g = 0.6 + 0.4 * Math.sin(frame / 8); return (
          <g transform={`translate(${wx},${wy}) scale(2.0)`} style={{ filter: `drop-shadow(0 0 ${8 + g * 10}px ${accent})` }}>
            <ellipse cx="0" cy="0" rx="13" ry="7" fill="#f4efe4" /><circle cx="11" cy="-2" r="4" fill="#f4efe4" />
            <path d="M-13,0 q-16,3 -22,-4" fill="none" stroke="#f4efe4" strokeWidth="2" />
          </g>
        ); })()}
      </svg>

      <AbsoluteFill style={{ justifyContent: "flex-start", alignItems: "flex-start", padding: "78px 90px", opacity: exit }}>
        {(() => { const k = enterUp(frame, 30, 2, 26); const t = enterUp(frame, 30, 8, 42, { stiffness: 125, damping: 18 }); return (<>
          <div style={{ color: accent, fontSize: 30, fontWeight: 700, letterSpacing: 8, opacity: k.opacity, transform: `translateY(${k.translateY}px)` }}>{kicker}</div>
          <div style={{ color: "#f4ecd8", fontSize: 68, fontWeight: 700, lineHeight: 1.02, textShadow: "0 6px 30px rgba(0,0,0,0.85)", marginTop: 6, opacity: t.opacity, transform: `translateY(${t.translateY}px)` }}>{title}</div>
        </>); })()}
      </AbsoluteFill>

      <div style={{ position: "absolute", right: 90, top: 300, textAlign: "right" }}>
        <div style={{ color: "#fff", fontSize: 92, fontWeight: 800, fontVariantNumeric: "tabular-nums", textShadow: `0 0 26px ${accent}`, fontFamily: fontFamily("oswald") }}>{cnt.toLocaleString("ru-RU")}</div>
        <div style={{ color: accent, fontSize: 26, fontWeight: 600 }}>{countLabel}</div>
      </div>

      {caption && (
        <div style={{ position: "absolute", left: 0, right: 0, bottom: 62, textAlign: "center", padding: "0 200px",
          color: "#ecdfc6", fontSize: 32, fontWeight: 500, textShadow: "0 4px 22px rgba(0,0,0,0.95)", fontFamily: fontFamily("montserrat"),
          opacity: interpolate(frame, [34, 48], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) * exit }}>{caption}</div>
      )}
      <AbsoluteFill style={{ boxShadow: "inset 0 0 300px rgba(0,0,0,0.8)", pointerEvents: "none" }} />
    </AbsoluteFill>
  );
};
