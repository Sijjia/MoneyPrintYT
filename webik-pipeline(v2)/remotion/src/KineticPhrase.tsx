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
import { isSensitive } from "./censor";

export type KineticPhraseProps = {
  phrase: string;
  highlight?: number[];
  bgImage?: string | null;
  accent?: string;
  textColor?: string;
  font?: FontName;
};

// Ключевая фраза из закадра — влетает по словам.
export const KineticPhrase: React.FC<KineticPhraseProps> = ({
  phrase,
  highlight = [],
  bgImage = null,
  accent = PALETTE.red,
  textColor = PALETTE.cream,
  font = "oswald",
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  const words = phrase.split(/\s+/).filter(Boolean);
  const STAGGER = 4;
  const hl = new Set(highlight);

  const exit = interpolate(frame, [durationInFrames - 16, durationInFrames], [1, 0], {
    extrapolateLeft: "clamp",
  });

  return (
    <AbsoluteFill style={{ fontFamily: fontFamily(font), opacity: exit }}>
      {bgImage && (
        <Img src={staticFile(bgImage)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
      )}
      <AbsoluteFill
        style={{
          background:
            "linear-gradient(0deg, rgba(0,0,0,0.72) 0%, rgba(0,0,0,0.28) 30%, transparent 55%)",
        }}
      />
      <AbsoluteFill
        style={{
          justifyContent: "flex-end",
          alignItems: "center",
          paddingBottom: 150,
          paddingLeft: 160,
          paddingRight: 160,
        }}
      >
        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            justifyContent: "center",
            gap: "0 22px",
            maxWidth: 1500,
          }}
        >
          {words.map((w, i) => {
            const appear = spring({
              frame: frame - i * STAGGER,
              fps,
              config: { damping: 200, mass: 0.6 },
            });
            const y = interpolate(appear, [0, 1], [34, 0]);
            const o = interpolate(appear, [0, 1], [0, 1]);
            const entranceBlur = interpolate(appear, [0, 1], [10, 0]);
            const censorBlur = isSensitive(w) ? 7 : 0;
            const blur = Math.max(entranceBlur, censorBlur);
            return (
              <span
                key={i}
                style={{
                  display: "inline-block",
                  transform: `translateY(${y}px)`,
                  opacity: o,
                  filter: blur > 0 ? `blur(${blur}px)` : undefined,
                  color: hl.has(i) ? accent : textColor,
                  fontSize: 78,
                  fontWeight: 800,
                  lineHeight: 1.15,
                  textShadow: "0 6px 28px rgba(0,0,0,0.8)",
                }}
              >
                {w}
              </span>
            );
          })}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
