import React from "react";
import { AbsoluteFill, OffthreadVideo, staticFile, Loop, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { fontFamily } from "./theme";

export type UncannyCGIProps = {
  videoSrc?: string; videoLoopFrames?: number;
  title?: string; subtitle?: string; accent?: string;
};

// Жуткий ранний CGI: холодный больной фильтр, лёгкий варп/хром-аберрация, метка «Зловещая долина».
export const UncannyCGI: React.FC<UncannyCGIProps> = ({
  videoSrc = "videos/dw_boo.mp4", videoLoopFrames = 150,
  title = "ЗЛОВЕЩАЯ ДОЛИНА", subtitle = "РАННИЙ CGI DREAMWORKS", accent = "#7fd14f",
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const exit = interpolate(frame, [durationInFrames - 12, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });
  const intro = interpolate(frame, [0, 14], [0, 1], { extrapolateRight: "clamp" });
  const ab = 3 + Math.sin(frame / 5) * 3;
  const warp = 1.02 + Math.sin(frame / 20) * 0.01;

  const layer = (dx: number, mix: string, op: number) => (
    <AbsoluteFill style={{ transform: `scale(${warp}) translateX(${dx}px)`, mixBlendMode: mix as any, opacity: op,
      filter: "saturate(0.5) contrast(1.15) hue-rotate(-12deg) brightness(0.9)" }}>
      <Loop durationInFrames={Math.max(30, videoLoopFrames)}>
        <OffthreadVideo src={staticFile(videoSrc)} muted style={{ width: "100%", height: "100%", objectFit: "cover" }} />
      </Loop>
    </AbsoluteFill>
  );

  return (
    <AbsoluteFill style={{ opacity: exit, background: "#04060a", fontFamily: fontFamily("oswald") }}>
      {layer(0, "normal", 1)}
      {layer(-ab, "screen", 0.4)}
      {layer(ab, "screen", 0.4)}
      {/* больной зеленоватый оттенок */}
      <AbsoluteFill style={{ background: `radial-gradient(ellipse at 50% 45%, ${accent}18 0%, transparent 60%)`, mixBlendMode: "overlay" }} />
      {/* скан-линии + случайная полоса-помеха */}
      <AbsoluteFill style={{ opacity: 0.12, backgroundImage:
        "repeating-linear-gradient(0deg, #000 0, #000 1px, transparent 1px, transparent 3px)", pointerEvents: "none" }} />
      <div style={{ position: "absolute", left: 0, right: 0, top: (frame * 11) % 1080, height: 22,
        background: "rgba(255,255,255,0.05)", pointerEvents: "none" }} />
      <AbsoluteFill style={{ boxShadow: "inset 0 0 240px rgba(0,0,0,0.82)", pointerEvents: "none" }} />
      <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: 70, opacity: intro }}>
        <div style={{ textAlign: "center", borderLeft: `6px solid ${accent}`, paddingLeft: 20 }}>
          <div style={{ color: "#eafce0", fontSize: 72, fontWeight: 800, letterSpacing: 3, textShadow: `0 0 24px ${accent}` }}>{title}</div>
          <div style={{ color: accent, fontSize: 26, fontWeight: 700, letterSpacing: 3 }}>{subtitle}</div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
