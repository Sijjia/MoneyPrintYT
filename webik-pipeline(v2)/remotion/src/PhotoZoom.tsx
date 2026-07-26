import React from "react";
import { AbsoluteFill, Img, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";

// Плавный лёгкий зум фото — CSS-трансформ (sub-pixel, НЕ трясётся как ffmpeg zoompan).
// Архив-грейд: лёгкое обесцвечивание + виньетка + едва заметное зерно.
export type PhotoZoomProps = { img?: string; dir?: "in" | "out"; z0?: number; z1?: number };

export const PhotoZoom: React.FC<PhotoZoomProps> = ({ img = "", dir = "in", z0 = 1.0, z1 = 1.06 }) => {
  const f = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const from = dir === "in" ? z0 : z1;
  const to = dir === "in" ? z1 : z0;
  const scale = interpolate(f, [0, durationInFrames], [from, to], { extrapolateRight: "clamp" });
  // очень медленный дрейф центра — оживляет без «тряски»
  const px = Math.sin(f / 200) * 0.6;
  const py = Math.cos(f / 240) * 0.4;
  return (
    <AbsoluteFill style={{ background: "#000", overflow: "hidden" }}>
      <AbsoluteFill style={{ transform: `translate(${px}%, ${py}%) scale(${scale})`, transformOrigin: "50% 50%" }}>
        {img ? (
          <Img src={staticFile(img)} style={{ width: "100%", height: "100%", objectFit: "cover",
            filter: "grayscale(0.32) contrast(1.08) brightness(0.95) saturate(0.85)" }} />
        ) : null}
      </AbsoluteFill>
      {/* виньетка */}
      <AbsoluteFill style={{ background: "radial-gradient(circle at 50% 48%, rgba(0,0,0,0) 55%, rgba(0,0,0,0.5) 100%)", pointerEvents: "none" }} />
      {/* лёгкое зерно */}
      <svg width="1920" height="1080" style={{ position: "absolute", inset: 0, opacity: 0.05, mixBlendMode: "overlay", pointerEvents: "none" }}>
        <filter id="pzg"><feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed={f % 50} stitchTiles="stitch" /></filter>
        <rect width="1920" height="1080" filter="url(#pzg)" />
      </svg>
    </AbsoluteFill>
  );
};
