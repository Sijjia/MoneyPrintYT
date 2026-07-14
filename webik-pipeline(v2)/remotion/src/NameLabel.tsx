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

export type NameLabelProps = {
  name: string;
  sub?: string;
  bgImage?: string | null;
  accent?: string;
  textColor?: string;
  font?: FontName;
  align?: "left" | "right";
  energy?: number;
};

// Нижний третий — представление человека/места/культа.
export const NameLabel: React.FC<NameLabelProps> = ({
  name,
  sub = "",
  bgImage = null,
  accent = PALETTE.red,
  textColor = PALETTE.cream,
  font = "oswald",
  align = "left",
  energy = 1,
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const right = align === "right";

  const enter = spring({ frame, fps, config: { damping: 200, mass: 0.7 / Math.max(0.5, energy) } });
  const lineW = interpolate(enter, [0, 1], [0, 620]);
  const nameY = interpolate(enter, [0, 1], [40, 0]);
  const nameOpacity = interpolate(frame, [2, 16], [0, 1], { extrapolateRight: "clamp" });
  const subOpacity = interpolate(frame, [12, 26], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const subX = interpolate(enter, [0, 1], [-24, 0]);
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
            "linear-gradient(0deg, rgba(0,0,0,0.8) 0%, rgba(0,0,0,0.35) 22%, transparent 42%)",
        }}
      />
      <AbsoluteFill
        style={{
          justifyContent: "flex-end",
          alignItems: right ? "flex-end" : "flex-start",
          textAlign: right ? "right" : "left",
          paddingLeft: right ? 0 : 150,
          paddingRight: right ? 150 : 0,
          paddingBottom: 165,
        }}
      >
        <div style={{ height: 4, width: lineW, background: accent, borderRadius: 2, marginBottom: 26 }} />
        <div style={{ overflow: "hidden" }}>
          <Censored
            text={name}
            style={{
              display: "inline-block",
              transform: `translateY(${nameY}px)`,
              opacity: nameOpacity,
              color: textColor,
              fontSize: 86,
              fontWeight: 800,
              lineHeight: 1.0,
              letterSpacing: -1,
              textShadow: "0 6px 30px rgba(0,0,0,0.7)",
            }}
          />
        </div>
        {sub && (
          <div
            style={{
              opacity: subOpacity,
              transform: `translateX(${subX}px)`,
              color: accent,
              fontSize: 40,
              fontWeight: 600,
              letterSpacing: 4,
              marginTop: 16,
              textTransform: "uppercase",
              textShadow: "0 3px 16px rgba(0,0,0,0.85)",
            }}
          >
            {sub}
          </div>
        )}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
