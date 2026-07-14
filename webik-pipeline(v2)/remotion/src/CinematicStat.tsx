import React from "react";
import {
  AbsoluteFill,
  Easing,
  Img,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { PALETTE, fontFamily, FontName } from "./theme";
import { Censored } from "./censor";

export type CinematicStatProps = {
  value: string;
  label: string;
  suffix?: string;
  sub?: string;
  bgImage?: string | null;
  accent?: string;
  textColor?: string;
  font?: FontName;
};

// Кинематографичная подача числа: медленный отъезд «камеры» (3D pull-back),
// наклон, параллакс фона, длинный вдумчивый ритм (~10с).
export const CinematicStat: React.FC<CinematicStatProps> = ({
  value,
  label,
  suffix = "",
  sub = "",
  bgImage = null,
  accent = PALETTE.red,
  textColor = PALETTE.cream,
  font = "oswald",
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  // «Камера»: медленный отъезд + 3D-наклон, плавный ease.
  const cam = interpolate(frame, [0, 135], [0, 1], {
    extrapolateRight: "clamp",
    easing: Easing.inOut(Easing.cubic),
  });
  const scale = interpolate(cam, [0, 1], [2.4, 1.0]);
  const ty = interpolate(cam, [0, 1], [150, 0]);
  const rotX = interpolate(cam, [0, 1], [10, 0]);

  // Счётчик — медленный.
  const target = parseInt(value.replace(/\D/g, ""), 10);
  const hasNum = !Number.isNaN(target);
  const ct = interpolate(frame, [0, 80], [0, 1], {
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });
  const shown = hasNum ? Math.round(target * ct).toLocaleString("ru-RU") : value;

  // Контекст проявляется, когда камера уже отъехала.
  const ctxOp = interpolate(frame, [80, 115], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  // Фон — медленный кен-бёрнс (параллакс).
  const bgScale = interpolate(frame, [0, durationInFrames], [1.3, 1.12]);

  const exit = interpolate(frame, [durationInFrames - 26, durationInFrames], [1, 0], {
    extrapolateLeft: "clamp",
  });

  return (
    <AbsoluteFill style={{ fontFamily: fontFamily(font), opacity: exit, background: "#05070c", overflow: "hidden" }}>
      {bgImage && (
        <AbsoluteFill style={{ transform: `scale(${bgScale})` }}>
          <Img
            src={staticFile(bgImage)}
            style={{ width: "100%", height: "100%", objectFit: "cover", filter: "brightness(0.5) grayscale(0.3)" }}
          />
        </AbsoluteFill>
      )}
      <AbsoluteFill
        style={{ background: "radial-gradient(circle at 50% 48%, rgba(0,0,0,0.5) 0%, rgba(0,0,0,0.35) 45%, rgba(0,0,0,0.75) 100%)" }}
      />

      {/* сцена под «камерой» */}
      <AbsoluteFill style={{ perspective: 1600, justifyContent: "center", alignItems: "center" }}>
        <div
          style={{
            transformStyle: "preserve-3d",
            transform: `translateY(${ty}px) rotateX(${rotX}deg) scale(${scale})`,
            textAlign: "center",
          }}
        >
          <div
            style={{
              color: textColor,
              fontSize: 360,
              fontWeight: 800,
              lineHeight: 0.9,
              letterSpacing: -8,
              textShadow: "0 24px 90px rgba(0,0,0,0.85)",
            }}
          >
            {shown}
            <span style={{ color: accent }}>{suffix}</span>
          </div>
          <div style={{ opacity: ctxOp, marginTop: 24 }}>
            <div
              style={{
                height: 4,
                width: 340,
                background: accent,
                margin: "0 auto 26px",
                borderRadius: 2,
                boxShadow: `0 0 20px ${accent}`,
              }}
            />
            <Censored
              text={label}
              style={{
                color: textColor,
                fontSize: 56,
                fontWeight: 600,
                letterSpacing: 3,
                textTransform: "uppercase",
                display: "inline-block",
              }}
            />
            {sub && (
              <div
                style={{
                  color: accent,
                  fontSize: 34,
                  fontWeight: 600,
                  letterSpacing: 2,
                  marginTop: 16,
                  textTransform: "uppercase",
                }}
              >
                {sub}
              </div>
            )}
          </div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
