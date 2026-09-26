import { AbsoluteFill, Img, staticFile, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import React from "react";

/** Аутро: просто капибара (липсинк) в центре на ЧЁРНОМ фоне + фейд в чёрное. Без текста/кнопок. */
type Props = { mouth?: number[] };

export const MascotOutro: React.FC<Props> = ({ mouth = [] }) => {
  const frame = useCurrentFrame();
  const { width, height, durationInFrames } = useVideoConfig();

  const mh = height * 0.9, mw = mh * (1370 / 3068), cx = width * 0.5;
  const mopen = interpolate(mouth[frame] ?? 0, [0, 1], [0, 1]);
  const bob = Math.sin(frame / 50) * 4;
  const appear = interpolate(frame, [0, 12], [0, 1], { extrapolateRight: "clamp" });
  const fade = interpolate(frame, [durationInFrames - 22, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });

  return (
    <AbsoluteFill style={{ background: "#000", opacity: Math.min(appear, fade) }}>
      <div style={{ position: "absolute", left: cx - mw * 0.4, top: height - mh * 0.22, width: mw * 0.8, height: mh * 0.16,
        background: "radial-gradient(ellipse, rgba(0,0,0,.6), transparent 70%)", filter: "blur(6px)" }} />
      <div style={{ position: "absolute", left: cx - mw / 2, top: height - mh + bob - height * 0.02, width: mw, height: mh }}>
        <Img src={staticFile("mascot/closed.png")} style={{ width: "100%", position: "absolute", top: 0, left: 0 }} />
        <Img src={staticFile("mascot/open.png")} style={{ width: "100%", position: "absolute", top: 0, left: 0, opacity: mopen }} />
      </div>
    </AbsoluteFill>
  );
};

export default MascotOutro;
