import React from "react";
import { AbsoluteFill, OffthreadVideo, staticFile, Loop, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { fontFamily } from "./theme";

export type DramaFreezeProps = {
  videoSrc?: string;
  videoLoopFrames?: number;
  title?: string;
  subtitle?: string;
  accent?: string;
};

// Драматизация страшного культового кадра: медленный зум, схлопывающаяся виньетка,
// вспышка-удар, красная подпись влетает. Для Волк-Смерть, казнь первенцев, геноцид панд.
export const DramaFreeze: React.FC<DramaFreezeProps> = ({
  videoSrc = "videos/dw_boo.mp4", videoLoopFrames = 150,
  title = "СТРАШНЫЙ КАДР", subtitle = "", accent = "#d9282f",
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames, width, height, fps } = useVideoConfig();
  const exit = interpolate(frame, [durationInFrames - 12, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });
  const zoom = interpolate(frame, [0, durationInFrames], [1.02, 1.18]);
  const desat = interpolate(frame, [0, 40], [0.9, 0.55], { extrapolateRight: "clamp" });
  const vig = interpolate(frame, [0, durationInFrames], [0.55, 0.95]);
  // вспышка-удар на 18 кадре
  const flash = frame >= 16 && frame < 22 ? (1 - (frame - 16) / 6) * 0.5 : 0;
  const shake = frame >= 16 && frame < 26 ? (Math.sin(frame * 3) * 8) * (1 - (frame - 16) / 10) : 0;
  // подпись
  const lab = spring({ frame: frame - 18, fps, config: { damping: 10, stiffness: 200 } });

  return (
    <AbsoluteFill style={{ opacity: exit, background: "#000", fontFamily: fontFamily("oswald") }}>
      <AbsoluteFill style={{ transform: `scale(${zoom}) translateX(${shake}px)`, filter: `saturate(${desat}) contrast(1.12) brightness(0.92)` }}>
        <Loop durationInFrames={Math.max(30, videoLoopFrames)}>
          <OffthreadVideo src={staticFile(videoSrc)} muted style={{ width: "100%", height: "100%", objectFit: "cover" }} />
        </Loop>
      </AbsoluteFill>
      {/* вспышка */}
      <AbsoluteFill style={{ background: "#fff", opacity: flash, pointerEvents: "none" }} />
      {/* виньетка */}
      <AbsoluteFill style={{ boxShadow: `inset 0 0 ${260 * vig}px rgba(0,0,0,${vig})`, pointerEvents: "none" }} />
      {/* скан-линии + зерно */}
      <AbsoluteFill style={{ opacity: 0.06, backgroundImage:
        "repeating-linear-gradient(0deg, #fff 0, #fff 1px, transparent 1px, transparent 3px)", pointerEvents: "none" }} />
      {/* красная полоса-подпись снизу */}
      <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: 70, opacity: lab }}>
        <div style={{ transform: `translateY(${(1 - lab) * 30}px)`, textAlign: "center",
          borderLeft: `6px solid ${accent}`, paddingLeft: 22 }}>
          <div style={{ color: "#fff", fontSize: 74, fontWeight: 800, letterSpacing: 2, textShadow: `0 0 30px ${accent}, 0 4px 14px #000` }}>{title}</div>
          {subtitle ? <div style={{ color: "#e8b7b9", fontSize: 28, fontWeight: 700, letterSpacing: 2, textTransform: "uppercase" }}>{subtitle}</div> : null}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
