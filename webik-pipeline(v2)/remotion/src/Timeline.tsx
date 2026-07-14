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

export type TimelineEvent = { year: string; label: string };
export type TimelineProps = {
  title?: string;
  events: TimelineEvent[];
  bgImage?: string | null;
  accent?: string;
  textColor?: string;
  font?: FontName;
};

// Хронология: горизонтальная линия рисуется, точки-события всплывают слева направо.
export const Timeline: React.FC<TimelineProps> = ({
  title = "",
  events,
  bgImage = null,
  accent = PALETTE.red,
  textColor = PALETTE.cream,
  font = "oswald",
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  const ev = events.slice(0, 5);
  const n = ev.length;
  const X0 = 220;
  const X1 = 1700;
  const span = X1 - X0;
  const Y = 560;

  // линия чертится
  const lineG = interpolate(frame, [4, 4 + 8 * Math.max(1, n)], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const lineW = span * lineG;

  const titleOpacity = interpolate(frame, [0, 12], [0, 1], { extrapolateRight: "clamp" });
  const exit = interpolate(frame, [durationInFrames - 16, durationInFrames], [1, 0], {
    extrapolateLeft: "clamp",
  });

  const xOf = (i: number) => (n === 1 ? (X0 + X1) / 2 : X0 + (span * i) / (n - 1));

  return (
    <AbsoluteFill style={{ fontFamily: fontFamily(font), opacity: exit }}>
      {bgImage && (
        <Img src={staticFile(bgImage)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
      )}
      <AbsoluteFill
        style={{ background: "linear-gradient(0deg, rgba(0,0,0,0.7) 0%, rgba(0,0,0,0.45) 50%, rgba(0,0,0,0.6) 100%)" }}
      />

      {title && (
        <div
          style={{
            position: "absolute",
            top: 300,
            width: "100%",
            textAlign: "center",
            opacity: titleOpacity,
            color: textColor,
            fontSize: 50,
            fontWeight: 700,
            letterSpacing: 2,
            textTransform: "uppercase",
            textShadow: "0 4px 20px rgba(0,0,0,0.9)",
          }}
        >
          {title}
        </div>
      )}

      {/* базовая линия */}
      <div style={{ position: "absolute", left: X0, top: Y, width: lineW, height: 4, background: "rgba(255,255,255,0.4)" }} />
      <div style={{ position: "absolute", left: X0, top: Y, width: lineW, height: 4, background: accent, opacity: 0.9 }} />

      {ev.map((e, i) => {
        const appear = spring({ frame: frame - (8 + i * 9), fps, config: { damping: 200, mass: 0.5 } });
        const s = interpolate(appear, [0, 1], [0, 1]);
        const x = xOf(i);
        return (
          <div key={i} style={{ position: "absolute", left: x, top: Y }}>
            {/* точка */}
            <div
              style={{
                position: "absolute",
                left: -13,
                top: -11,
                width: 26,
                height: 26,
                borderRadius: "50%",
                background: accent,
                transform: `scale(${s})`,
                boxShadow: `0 0 16px ${accent}`,
                border: "3px solid #0c0c0c",
              }}
            />
            {/* год сверху */}
            <div
              style={{
                position: "absolute",
                left: -90,
                top: -92,
                width: 180,
                textAlign: "center",
                opacity: s,
                color: accent,
                fontSize: 46,
                fontWeight: 800,
                textShadow: "0 3px 14px rgba(0,0,0,0.9)",
              }}
            >
              {e.year}
            </div>
            {/* событие снизу */}
            <Censored
              text={e.label}
              style={{
                position: "absolute",
                left: -140,
                top: 26,
                width: 280,
                textAlign: "center",
                opacity: s,
                color: textColor,
                fontSize: 28,
                fontWeight: 600,
                lineHeight: 1.15,
                display: "inline-block",
                textShadow: "0 3px 14px rgba(0,0,0,0.95)",
              }}
            />
          </div>
        );
      })}
    </AbsoluteFill>
  );
};
