import React from "react";
import { AbsoluteFill, OffthreadVideo, staticFile, Loop, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { fontFamily } from "./theme";

export type SplitCompareProps = {
  videoSrc?: string; videoLoopFrames?: number;
  videoSrcB?: string;
  title?: string;
  aLabel?: string; aSub?: string;
  bLabel?: string; bSub?: string;
  accent?: string;
};

// Сплит-скрин сравнение (Фарли vs Майерс, ранний CGI vs финал). Два кадра + подписи.
export const SplitCompare: React.FC<SplitCompareProps> = ({
  videoSrc = "videos/dw_boo.mp4", videoLoopFrames = 150, videoSrcB,
  title = "СРАВНЕНИЕ", aLabel = "БЫЛО", aSub = "", bLabel = "СТАЛО", bSub = "", accent = "#d9282f",
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames, width, height } = useVideoConfig();
  const exit = interpolate(frame, [durationInFrames - 12, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });
  const la = interpolate(frame, [4, 18], [-width / 2, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const lb = interpolate(frame, [8, 22], [width / 2, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const srcB = videoSrcB || videoSrc;

  const panel = (src: string, dx: number, startFrom: number, label: string, sub: string, filt: string) => (
    <div style={{ position: "absolute", top: 0, width: width / 2, height, overflow: "hidden", transform: `translateX(${dx}px)` }}>
      <Loop durationInFrames={Math.max(30, videoLoopFrames)}>
        <OffthreadVideo src={staticFile(src)} muted startFrom={startFrom}
          style={{ width: "100%", height: "100%", objectFit: "cover", filter: filt }} />
      </Loop>
      <AbsoluteFill style={{ boxShadow: "inset 0 0 140px rgba(0,0,0,0.7)", pointerEvents: "none" }} />
      <div style={{ position: "absolute", bottom: 60, left: 0, right: 0, textAlign: "center" }}>
        <div style={{ color: "#fff", fontSize: 46, fontWeight: 800, letterSpacing: 3, textShadow: "0 2px 12px #000" }}>{label}</div>
        {sub ? <div style={{ color: accent, fontSize: 24, fontWeight: 700, letterSpacing: 2 }}>{sub}</div> : null}
      </div>
    </div>
  );

  return (
    <AbsoluteFill style={{ opacity: exit, background: "#000", fontFamily: fontFamily("oswald") }}>
      <div style={{ position: "absolute", left: 0, top: 0 }}>{panel(videoSrc, la, 0, aLabel, aSub, "saturate(0.55) contrast(1.05) sepia(0.15)")}</div>
      <div style={{ position: "absolute", left: width / 2, top: 0 }}>{panel(srcB, lb, 20, bLabel, bSub, "saturate(1.05) contrast(1.05)")}</div>
      {/* разделитель */}
      <div style={{ position: "absolute", left: width / 2 - 3, top: 0, width: 6, height, background: accent,
        boxShadow: `0 0 24px ${accent}`, opacity: interpolate(frame, [16, 24], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) }} />
      {/* заголовок */}
      <AbsoluteFill style={{ justifyContent: "flex-start", alignItems: "center", paddingTop: 40,
        opacity: interpolate(frame, [10, 24], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) }}>
        <div style={{ color: "#fff", fontSize: 44, fontWeight: 800, letterSpacing: 4, background: "rgba(0,0,0,0.5)",
          padding: "6px 24px", borderRadius: 6 }}>{title}</div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
