import React from "react";
import {
  AbsoluteFill,
  Img,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { PALETTE, fontFamily, FontName } from "./theme";
import { Censored } from "./censor";

export type SpotlightProps = {
  label?: string;
  /** Центр фокуса, % (по умолчанию центр). */
  x?: number;
  y?: number;
  bgImage?: string | null;
  accent?: string;
  textColor?: string;
  font?: FontName;
};

// Фокус-затемнение: периферия затемняется, внимание — на область кадра.
export const Spotlight: React.FC<SpotlightProps> = ({
  label = "",
  x = 50,
  y = 48,
  bgImage = null,
  accent = PALETTE.red,
  textColor = PALETTE.cream,
  font = "oswald",
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  const inMask = interpolate(frame, [0, 14], [0, 1], { extrapolateRight: "clamp" });
  // лёгкое «сжатие» дыры — эффект наезда
  const hole = interpolate(frame, [0, 20], [34, 26], { extrapolateRight: "clamp" });
  const dark = 0.72 * inMask;

  const labelOpacity = interpolate(frame, [10, 24], [0, 1], {
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
      {/* маска-фокус */}
      <AbsoluteFill
        style={{
          background: `radial-gradient(circle at ${x}% ${y}%, transparent ${hole - 8}%, rgba(0,0,0,${dark}) ${hole + 6}%)`,
        }}
      />
      {/* акцентное кольцо вокруг фокуса */}
      <div
        style={{
          position: "absolute",
          left: `${x}%`,
          top: `${y}%`,
          width: 560,
          height: 560,
          marginLeft: -280,
          marginTop: -280,
          borderRadius: "50%",
          border: `2px solid ${accent}`,
          opacity: inMask * 0.5,
          boxShadow: `0 0 30px ${accent}66 inset`,
        }}
      />
      {label && (
        <div
          style={{
            position: "absolute",
            left: 0,
            right: 0,
            bottom: 150,
            textAlign: "center",
            opacity: labelOpacity,
            color: textColor,
            fontSize: 46,
            fontWeight: 700,
            letterSpacing: 2,
            textTransform: "uppercase",
            textShadow: "0 3px 18px rgba(0,0,0,1)",
          }}
        >
          <Censored text={label} style={{ display: "inline-block" }} />
        </div>
      )}
    </AbsoluteFill>
  );
};
