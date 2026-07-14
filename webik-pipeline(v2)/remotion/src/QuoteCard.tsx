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

export type QuoteCardProps = {
  text: string;
  author?: string;
  bgImage?: string | null;
  accent?: string;
  textColor?: string;
  font?: FontName;
  energy?: number;
};

// Цитата: крупная кавычка, текст, атрибуция. Для ПРЯМЫХ цитат из закадра.
export const QuoteCard: React.FC<QuoteCardProps> = ({
  text,
  author = "",
  bgImage = null,
  accent = PALETTE.red,
  textColor = PALETTE.cream,
  font = "oswald",
  energy = 1,
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  const enter = spring({ frame, fps, config: { damping: 200, mass: 0.7 / Math.max(0.5, energy) } });
  const markScale = interpolate(enter, [0, 1], [0.3, 1]);
  const markOpacity = interpolate(frame, [0, 10], [0, 1], { extrapolateRight: "clamp" });
  const textY = interpolate(enter, [0, 1], [30, 0]);
  const textOpacity = interpolate(frame, [4, 18], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const authorOpacity = interpolate(frame, [16, 30], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const exit = interpolate(frame, [durationInFrames - 16, durationInFrames], [1, 0], {
    extrapolateLeft: "clamp",
  });

  return (
    <AbsoluteFill style={{ fontFamily: fontFamily(font), opacity: exit }}>
      {bgImage && (
        <Img src={staticFile(bgImage)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
      )}
      <AbsoluteFill
        style={{ background: "radial-gradient(circle at 50% 50%, rgba(0,0,0,0.78) 0%, rgba(0,0,0,0.5) 55%, rgba(0,0,0,0.35) 100%)" }}
      />
      <AbsoluteFill
        style={{
          justifyContent: "center",
          alignItems: "center",
          flexDirection: "column",
          padding: "0 220px",
        }}
      >
        <div
          style={{
            opacity: markOpacity,
            transform: `scale(${markScale})`,
            color: accent,
            fontSize: 200,
            fontWeight: 800,
            lineHeight: 0.6,
            height: 90,
          }}
        >
          «
        </div>
        <Censored
          text={text}
          style={{
            opacity: textOpacity,
            transform: `translateY(${textY}px)`,
            color: textColor,
            fontSize: 68,
            fontWeight: 700,
            fontStyle: "italic",
            textAlign: "center",
            lineHeight: 1.2,
            maxWidth: 1400,
            display: "inline-block",
            textShadow: "0 6px 30px rgba(0,0,0,0.85)",
          }}
        />
        {author && (
          <div
            style={{
              opacity: authorOpacity,
              marginTop: 40,
              color: accent,
              fontSize: 40,
              fontWeight: 600,
              letterSpacing: 3,
              textTransform: "uppercase",
              textShadow: "0 3px 16px rgba(0,0,0,0.9)",
            }}
          >
            — {author}
          </div>
        )}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
