import React from "react";
import {
  AbsoluteFill,
  Img,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { PALETTE, fontFamily, FontName } from "./theme";
import { Censored } from "./censor";

export type PictographProps = {
  filled: number;
  total: number;
  label: string;
  bgImage?: string | null;
  accent?: string;
  textColor?: string;
  font?: FontName;
};

// Пиктограмма «X из Y»: ряд фигур, часть закрашена акцентом — эмоционально о доле.
export const Pictograph: React.FC<PictographProps> = ({
  filled,
  total,
  label,
  bgImage = null,
  accent = PALETTE.red,
  textColor = PALETTE.cream,
  font = "oswald",
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  const n = Math.max(1, Math.min(total, 20));
  const nFilled = Math.max(0, Math.min(filled, n));

  const headOpacity = interpolate(frame, [0, 12], [0, 1], { extrapolateRight: "clamp" });
  const exit = interpolate(frame, [durationInFrames - 16, durationInFrames], [1, 0], {
    extrapolateLeft: "clamp",
  });

  return (
    <AbsoluteFill style={{ fontFamily: fontFamily(font), opacity: exit }}>
      {bgImage && (
        <Img src={staticFile(bgImage)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
      )}
      <AbsoluteFill
        style={{ background: "linear-gradient(0deg, rgba(0,0,0,0.72) 0%, rgba(0,0,0,0.3) 40%, transparent 62%)" }}
      />
      <AbsoluteFill
        style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: 150 }}
      >
        <div
          style={{
            opacity: headOpacity,
            color: textColor,
            fontSize: 64,
            fontWeight: 800,
            marginBottom: 34,
            textShadow: "0 4px 20px rgba(0,0,0,0.9)",
          }}
        >
          {nFilled} <span style={{ color: accent }}>из</span> {n}
        </div>
        <div style={{ display: "flex", gap: 16, marginBottom: 30 }}>
          {Array.from({ length: n }).map((_, i) => {
            const isOn = i < nFilled;
            const appear = spring({ frame: frame - 10 - i * 3, fps, config: { damping: 200, mass: 0.5 } });
            const s = interpolate(appear, [0, 1], [0.4, 1]);
            const o = interpolate(appear, [0, 1], [0, 1]);
            return (
              <svg key={i} width="58" height="82" viewBox="0 0 58 82" style={{ transform: `scale(${s})`, opacity: o }}>
                {/* фигура человека */}
                <circle cx="29" cy="17" r="15" fill={isOn ? accent : "rgba(255,255,255,0.28)"} />
                <path
                  d="M6 82 C6 52 18 40 29 40 C40 40 52 52 52 82 Z"
                  fill={isOn ? accent : "rgba(255,255,255,0.28)"}
                />
              </svg>
            );
          })}
        </div>
        <Censored
          text={label}
          style={{
            color: textColor,
            fontSize: 44,
            fontWeight: 600,
            letterSpacing: 2,
            textTransform: "uppercase",
            display: "inline-block",
            textShadow: "0 3px 16px rgba(0,0,0,0.9)",
          }}
        />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
