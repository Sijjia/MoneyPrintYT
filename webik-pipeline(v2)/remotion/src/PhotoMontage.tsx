import React from "react";
import { AbsoluteFill, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { fontFamily } from "./theme";

export type PhotoMontageProps = {
  images?: string[];   // пути относительно public/ (напр. "photos/x.jpg")
  caption?: string;
  accent?: string;
};

// Красивая компоновка НЕСКОЛЬКИХ реальных фото (2-4): Ken Burns, рамки со свечением,
// ступенчатое появление, тёмный био-фон, подпись. Полноэкранная (заменяет клип на V3).
const cellsFor = (n: number): { left: string; top: string; w: string; h: string }[] => {
  if (n <= 1) return [{ left: "6%", top: "8%", w: "88%", h: "84%" }];
  if (n === 2) return [
    { left: "5%", top: "12%", w: "44%", h: "76%" },
    { left: "51%", top: "12%", w: "44%", h: "76%" },
  ];
  if (n === 3) return [
    { left: "5%", top: "10%", w: "52%", h: "80%" },
    { left: "59%", top: "10%", w: "36%", h: "38%" },
    { left: "59%", top: "52%", w: "36%", h: "38%" },
  ];
  return [
    { left: "6%", top: "9%", w: "43%", h: "40%" },
    { left: "51%", top: "9%", w: "43%", h: "40%" },
    { left: "6%", top: "51%", w: "43%", h: "40%" },
    { left: "51%", top: "51%", w: "43%", h: "40%" },
  ];
};

export const PhotoMontage: React.FC<PhotoMontageProps> = ({
  images = [],
  caption = "",
  accent = "#1fa48a",
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames, fps } = useVideoConfig();
  const imgs = images.slice(0, 4);
  const cells = cellsFor(imgs.length);
  const exit = interpolate(frame, [durationInFrames - 14, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });

  return (
    <AbsoluteFill style={{ fontFamily: fontFamily("oswald"), opacity: exit, background: "radial-gradient(ellipse at 50% 45%, #0a1f24 0%, #06110f 60%, #03080a 100%)" }}>
      {imgs.map((src, i) => {
        const c = cells[i];
        const appear = spring({ frame: frame - i * 6, fps, config: { damping: 14, stiffness: 110 } });
        // Ken Burns: чередуем zoom-in / лёгкий пан
        const kb = interpolate(frame, [0, durationInFrames], [1.02, 1.14]);
        const panX = interpolate(frame, [0, durationInFrames], [0, i % 2 ? -18 : 18]);
        const panY = interpolate(frame, [0, durationInFrames], [0, i % 2 ? 12 : -12]);
        return (
          <div key={i} style={{
            position: "absolute", left: c.left, top: c.top, width: c.w, height: c.h,
            transform: `translateY(${(1 - appear) * 40}px) scale(${0.9 + appear * 0.1})`,
            opacity: appear, borderRadius: 10, overflow: "hidden",
            border: `2px solid rgba(122,233,212,0.45)`,
            boxShadow: `0 18px 60px rgba(0,0,0,0.7), 0 0 30px ${accent}44`,
          }}>
            <Img src={src.startsWith("http") ? src : staticFile(src)}
              style={{ width: "100%", height: "100%", objectFit: "cover",
                transform: `scale(${kb}) translate(${panX}px, ${panY}px)` }} />
            <div style={{ position: "absolute", inset: 0, boxShadow: "inset 0 0 60px rgba(0,0,0,0.5)" }} />
          </div>
        );
      })}
      <AbsoluteFill style={{ boxShadow: "inset 0 0 260px rgba(0,0,0,0.7)", pointerEvents: "none" }} />
      {caption ? (
        <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "flex-start", padding: 60 }}>
          <div style={{
            background: "rgba(3,14,12,0.72)", borderLeft: `4px solid ${accent}`, padding: "12px 22px",
            color: "#eafcf6", fontSize: 34, fontWeight: 700, letterSpacing: 1, backdropFilter: "blur(2px)",
          }}>{caption}</div>
        </AbsoluteFill>
      ) : null}
    </AbsoluteFill>
  );
};
