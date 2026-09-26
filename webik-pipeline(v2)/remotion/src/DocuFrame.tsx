import React from "react";
import {
  AbsoluteFill,
  Img,
  Easing,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { fontFamily } from "./theme";

export type DocuFrameProps = {
  imgSrc: string;          // путь в public/ (реальное фото)
  kicker?: string;         // «АРХИВ» / «2013» / «РАЗОБЛАЧЕНО»
  title?: string;          // подпись-заголовок
  source?: string;         // «Wikimedia Commons» / источник
  accent?: string;
  kenburns?: "in" | "out" | "left" | "right";
};

// Кинематографичная подача РЕАЛЬНОГО фото: full-bleed Ken-Burns + летербокс + зерно + лоуэр-терд.
export const DocuFrame: React.FC<DocuFrameProps> = ({
  imgSrc,
  kicker = "ARCHIVE",
  title = "",
  source = "",
  accent = "#e0b64a",
  kenburns = "in",
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames, width, height } = useVideoConfig();
  const p = durationInFrames > 1 ? frame / (durationInFrames - 1) : 0;
  const exit = interpolate(frame, [durationInFrames - 12, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });
  const intro = interpolate(frame, [0, 16], [0, 1], { extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });

  // Ken-Burns
  const z = kenburns === "out" ? interpolate(p, [0, 1], [1.14, 1.0]) : interpolate(p, [0, 1], [1.0, 1.14]);
  const tx = kenburns === "left" ? interpolate(p, [0, 1], [3, -3]) : kenburns === "right" ? interpolate(p, [0, 1], [-3, 3]) : 0;
  const barH = interpolate(intro, [0, 1], [0, height * 0.11]);

  return (
    <AbsoluteFill style={{ background: "#000", fontFamily: fontFamily("oswald"), opacity: exit, overflow: "hidden" }}>
      {/* реальное фото full-bleed с Ken-Burns */}
      <AbsoluteFill style={{ transform: `scale(${z}) translateX(${tx}%)` }}>
        <Img src={staticFile(imgSrc)} style={{ width: "100%", height: "100%", objectFit: "cover", filter: "saturate(0.92) contrast(1.06)" }} />
      </AbsoluteFill>
      {/* цветокоррекция-дымка + виньетка */}
      <AbsoluteFill style={{ background: "linear-gradient(180deg, rgba(0,0,0,0.45) 0%, rgba(0,0,0,0) 26%, rgba(0,0,0,0) 55%, rgba(0,0,0,0.82) 100%)", pointerEvents: "none" }} />
      <AbsoluteFill style={{ boxShadow: "inset 0 0 320px rgba(0,0,0,0.7)", pointerEvents: "none" }} />
      {/* лёгкое зерно */}
      <AbsoluteFill style={{ opacity: 0.06, backgroundImage: "repeating-linear-gradient(0deg, #fff 0, #fff 1px, transparent 1px, transparent 3px)", pointerEvents: "none" }} />

      {/* кино-летербокс */}
      <div style={{ position: "absolute", top: 0, left: 0, right: 0, height: barH, background: "#000" }} />
      <div style={{ position: "absolute", bottom: 0, left: 0, right: 0, height: barH, background: "#000" }} />

      {/* уголок-скобки кадра */}
      {intro > 0.5 && [[40, 40, "nwse"], [width - 92, 40, "nesw"]].map(([x, y], i) => (
        <div key={i} style={{ position: "absolute", left: x as number, top: (y as number) + barH, width: 52, height: 52,
          borderTop: `3px solid ${accent}`, borderLeft: i === 0 ? `3px solid ${accent}` : "none", borderRight: i === 1 ? `3px solid ${accent}` : "none", opacity: 0.85 }} />
      ))}

      {/* лоуэр-терд */}
      <div style={{ position: "absolute", left: 70, bottom: barH + 70, opacity: intro, transform: `translateY(${interpolate(intro, [0, 1], [24, 0])}px)`, maxWidth: width - 200 }}>
        <div style={{ display: "inline-block", background: accent, color: "#141414", fontSize: 26, fontWeight: 800, letterSpacing: 4, padding: "7px 18px", marginBottom: 14 }}>{kicker}</div>
        {title && <div style={{ color: "#fff", fontSize: 60, fontWeight: 700, lineHeight: 1.08, textShadow: "0 6px 30px rgba(0,0,0,0.95)", maxWidth: 1400 }}>{title}</div>}
        {source && <div style={{ color: "#c9ccd2", fontSize: 24, fontWeight: 500, letterSpacing: 1, marginTop: 12, opacity: 0.9 }}>▪ {source}</div>}
      </div>
    </AbsoluteFill>
  );
};
