import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { fontFamily } from "./theme";
import { ease, mspring, enterUp } from "./anim";

export type SkeletonLakeProps = {
  kicker?: string;      // «ROOPKUND» / «ОЗЕРО СКЕЛЕТОВ»
  title?: string;       // КАПСОМ
  eras?: { label: string; note: string }[];  // 3 группы ДНК (эпохи)
  accent?: string;
  caption?: string;
  durationInFrames?: number;
};

const DEF_ERAS = [
  { label: "1st c. CE", note: "locals" },
  { label: "9th c.", note: "Mediterranean" },
  { label: "19th c.", note: "pilgrims" },
];

// Рупкунд: ледяное гималайское озеро на дне, всплывающие черепа, три ДНК-маркера разных эпох,
// удары града сверху. Холодная палитра, разрежённый горный воздух.
export const SkeletonLake: React.FC<SkeletonLakeProps> = ({
  kicker = "ROOPKUND",
  title = "THE LAKE OF HUNDREDS OF SKELETONS",
  eras,
  accent = "#8fd3e6",
  caption = "",
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const intro = interpolate(frame, [0, 22], [0, 1], { extrapolateRight: "clamp" });
  const exit = interpolate(frame, [durationInFrames - 16, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });
  const E = (eras && eras.length ? eras : DEF_ERAS).slice(0, 3);

  const Skull = ({ x, y, s, o }: { x: number; y: number; s: number; o: number }) => (
    <g transform={`translate(${x},${y}) scale(${s})`} opacity={o}>
      <path d="M0,-20 C16,-20 22,-6 22,6 C22,14 16,20 12,24 L12,32 L-12,32 L-12,24 C-16,20 -22,14 -22,6 C-22,-6 -16,-20 0,-20 Z" fill="#e9eef0" opacity="0.92" />
      <circle cx="-9" cy="4" r="6" fill="#0a1418" /><circle cx="9" cy="4" r="6" fill="#0a1418" />
      <path d="M-3,14 L0,20 L3,14 Z" fill="#0a1418" />
      <rect x="-11" y="28" width="4" height="6" fill="#cfd9dc" /><rect x="-3" y="28" width="4" height="6" fill="#cfd9dc" /><rect x="5" y="28" width="4" height="6" fill="#cfd9dc" />
    </g>
  );

  return (
    <AbsoluteFill style={{ fontFamily: fontFamily("oswald"), opacity: exit, overflow: "hidden" }}>
      <AbsoluteFill style={{ background: "linear-gradient(180deg,#0a1822 0%,#0e2733 34%,#12333f 52%,#0c2531 70%,#06151d 100%)" }} />
      {/* горные пики фоном */}
      <svg width={1920} height={1080} viewBox="0 0 1920 1080" style={{ position: "absolute", inset: 0, opacity: intro * 0.9 }}>
        <polygon points="0,470 260,200 470,420 700,150 980,440 1240,220 1520,470 1780,260 1920,470 1920,560 0,560" fill="#16303b" opacity="0.8" />
        <polygon points="700,150 760,240 640,240" fill="#d7ebf2" opacity="0.7" />
        <polygon points="1240,220 1300,300 1180,300" fill="#d7ebf2" opacity="0.6" />
        {/* ледяное озеро */}
        <ellipse cx="960" cy="760" rx="820" ry="230" fill="#0e2c39" opacity="0.9" />
        <ellipse cx="960" cy="760" rx="820" ry="230" fill="none" stroke={accent} strokeWidth="2" opacity="0.4" />
        <ellipse cx="960" cy="740" rx="700" ry="150" fill="rgba(143,211,230,0.07)" />
      </svg>

      {/* всплывающие черепа в озере */}
      <svg width={1920} height={1080} viewBox="0 0 1920 1080" style={{ position: "absolute", inset: 0, opacity: intro }}>
        {[[560, 780, 1.6], [820, 830, 2.1], [1080, 800, 1.8], [1320, 840, 2.3], [700, 700, 1.3], [1180, 720, 1.5], [960, 770, 2.0]].map(([x, y, s], i) => {
          const p = interpolate(frame, [20 + i * 7, 54 + i * 7], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: ease.expoOut });
          const rise = (1 - p) * 26;
          const o = p * 0.92;
          const bob = Math.sin((frame + i * 20) / 22) * 3;
          return <Skull key={i} x={x} y={y + rise + bob} s={s} o={o} />;
        })}
      </svg>

      {/* град сверху */}
      {Array.from({ length: 40 }).map((_, i) => {
        const x = (i * 137.5) % 1920;
        const fall = ((frame * (10 + (i % 5) * 3)) % 1120);
        return <div key={i} style={{ position: "absolute", left: x, top: fall - 40, width: 6, height: 6, borderRadius: "50%", background: "#dff2f8", opacity: 0.5, boxShadow: `0 0 5px ${accent}` }} />;
      })}

      {/* три ДНК-маркера эпох */}
      <div style={{ position: "absolute", left: 0, right: 0, bottom: 150, display: "flex", justifyContent: "center", gap: 60 }}>
        {E.map((e, i) => {
          const s = mspring(frame, 30, { stiffness: 150, damping: 13, delay: 46 + i * 12 });
          const on = Math.min(1, s);
          return (
            <div key={i} style={{ opacity: on, transform: `translateY(${(1 - s) * 24}px) scale(${0.9 + s * 0.1})`, textAlign: "center" }}>
              <div style={{ width: 44, height: 70, margin: "0 auto 10px", position: "relative" }}>
                {Array.from({ length: 6 }).map((_, k) => (
                  <div key={k} style={{ position: "absolute", top: k * 12, left: 0, right: 0, height: 3, background: accent, borderRadius: 2,
                    transform: `scaleX(${Math.abs(Math.sin((frame / 8) + k * 0.7 + i))})`, opacity: 0.85 }} />
                ))}
              </div>
              <div style={{ color: "#eaf4f7", fontSize: 34, fontWeight: 800, fontFamily: fontFamily("oswald") }}>{e.label}</div>
              <div style={{ color: accent, fontSize: 22, fontWeight: 600, letterSpacing: 1 }}>{e.note}</div>
            </div>
          );
        })}
      </div>

      <AbsoluteFill style={{ justifyContent: "flex-start", alignItems: "flex-start", padding: "80px 90px", opacity: exit }}>
        {(() => { const k = enterUp(frame, 30, 2, 30); const t = enterUp(frame, 30, 8, 46); return (<>
          <div style={{ color: accent, fontSize: 30, fontWeight: 700, letterSpacing: 8, opacity: k.opacity, transform: `translateY(${k.translateY}px)` }}>{kicker}</div>
          <div style={{ color: "#eef7fa", fontSize: 72, fontWeight: 700, lineHeight: 1.02, textShadow: "0 6px 30px rgba(0,0,0,0.8)", maxWidth: 1100, marginTop: 6, opacity: t.opacity, transform: `translateY(${t.translateY}px)` }}>{title}</div>
        </>); })()}
      </AbsoluteFill>

      {caption && (
        <div style={{ position: "absolute", left: 0, right: 0, bottom: 60, textAlign: "center", padding: "0 200px",
          color: "#dcecf1", fontSize: 32, fontWeight: 500, textShadow: "0 4px 22px rgba(0,0,0,0.95)", fontFamily: fontFamily("montserrat"),
          opacity: interpolate(frame, [30, 46], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) * exit }}>{caption}</div>
      )}
      <AbsoluteFill style={{ boxShadow: "inset 0 0 300px rgba(0,0,0,0.78)", pointerEvents: "none" }} />
    </AbsoluteFill>
  );
};
