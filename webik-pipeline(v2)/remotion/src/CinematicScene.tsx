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

export type SceneStat = { value: string; label: string; suffix?: string };
export type CinematicSceneProps = {
  headline?: string;
  a: SceneStat;
  b: SceneStat;
  bgImage?: string | null;
  accent?: string;
  textColor?: string;
  font?: FontName;
};

// Мир (координатная плоскость), в котором расставлены блоки. «Камера» = трансформ
// этого мира: наезжает на A → панорама к B → отъезд, раскрывающий обе + шапку.
const AX = 760;
const AY = 640;
const BX = 1640;
const BY = 640;
const HX = 1200;
const HY = 250;

// плавный многосегментный проезд с ease на каждом участке
const seg = (frame: number, segs: [number, number, number, number][]): number => {
  for (const [f0, f1, v0, v1] of segs) {
    if (frame <= f0) return v0;
    if (frame <= f1) {
      return interpolate(frame, [f0, f1], [v0, v1], {
        easing: Easing.inOut(Easing.cubic),
      });
    }
  }
  return segs[segs.length - 1][3];
};

const StatBlock: React.FC<{
  x: number;
  y: number;
  stat: SceneStat;
  startF: number;
  accent: string;
  textColor: string;
  frame: number;
}> = ({ x, y, stat, startF, accent, textColor, frame }) => {
  const target = parseInt(stat.value.replace(/\D/g, ""), 10);
  const hasNum = !Number.isNaN(target);
  const ct = interpolate(frame, [startF, startF + 55], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });
  const shown = hasNum ? Math.round(target * ct).toLocaleString("ru-RU") : stat.value;
  const o = interpolate(frame, [startF, startF + 14], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const lineW = interpolate(frame, [startF + 10, startF + 40], [0, 300], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        position: "absolute",
        left: x,
        top: y,
        transform: "translate(-50%,-50%)",
        textAlign: "center",
        opacity: o,
      }}
    >
      <div style={{ color: textColor, fontSize: 250, fontWeight: 800, lineHeight: 0.9, letterSpacing: -5, textShadow: "0 16px 60px rgba(0,0,0,0.85)" }}>
        {shown}
        <span style={{ color: accent }}>{stat.suffix || ""}</span>
      </div>
      <div style={{ height: 4, width: lineW, background: accent, margin: "18px auto 16px", borderRadius: 2, boxShadow: `0 0 16px ${accent}` }} />
      <Censored
        text={stat.label}
        style={{ color: textColor, fontSize: 46, fontWeight: 600, letterSpacing: 3, textTransform: "uppercase", display: "inline-block" }}
      />
    </div>
  );
};

export const CinematicScene: React.FC<CinematicSceneProps> = ({
  headline = "",
  a,
  b,
  bgImage = null,
  accent = PALETTE.red,
  textColor = PALETTE.cream,
  font = "oswald",
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  // камера: фокус (fx,fy) + зум по фазам
  const fx = seg(frame, [
    [0, 150, AX, AX],
    [150, 250, AX, BX],
    [250, 320, BX, BX],
    [320, 430, BX, HX],
    [430, 999, HX, HX],
  ]);
  const fy = seg(frame, [
    [0, 320, AY, AY],
    [320, 430, AY, 560],
    [430, 999, 560, 560],
  ]);
  const zoom = seg(frame, [
    [0, 320, 1.55, 1.55],
    [320, 430, 1.55, 0.82],
    [430, 999, 0.82, 0.82],
  ]);
  const rotY = seg(frame, [
    [0, 250, 6, -6],
    [250, 430, -6, 0],
    [430, 999, 0, 0],
  ]);

  const tx = 960 - fx * zoom;
  const ty = 540 - fy * zoom;

  const headOpacity = interpolate(frame, [360, 410], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const bgScale = interpolate(frame, [0, durationInFrames], [1.32, 1.14]);
  const exit = interpolate(frame, [durationInFrames - 26, durationInFrames], [1, 0], {
    extrapolateLeft: "clamp",
  });

  return (
    <AbsoluteFill style={{ fontFamily: fontFamily(font), opacity: exit, background: "#05070c", overflow: "hidden" }}>
      {bgImage && (
        <AbsoluteFill style={{ transform: `scale(${bgScale})` }}>
          <Img src={staticFile(bgImage)} style={{ width: "100%", height: "100%", objectFit: "cover", filter: "brightness(0.4) grayscale(0.4)" }} />
        </AbsoluteFill>
      )}
      <AbsoluteFill style={{ background: "radial-gradient(circle at 50% 50%, rgba(0,0,0,0.5) 0%, rgba(0,0,0,0.4) 45%, rgba(0,0,0,0.78) 100%)" }} />

      <AbsoluteFill style={{ perspective: 1700, overflow: "hidden" }}>
        <div
          style={{
            position: "absolute",
            left: 0,
            top: 0,
            transformStyle: "preserve-3d",
            transform: `translate(${tx}px, ${ty}px) scale(${zoom}) rotateY(${rotY}deg)`,
            transformOrigin: "0 0",
          }}
        >
          {headline && (
            <div
              style={{
                position: "absolute",
                left: HX,
                top: HY,
                transform: "translate(-50%,-50%)",
                opacity: headOpacity,
                color: accent,
                fontSize: 72,
                fontWeight: 800,
                letterSpacing: 6,
                textTransform: "uppercase",
                whiteSpace: "nowrap",
                textShadow: "0 6px 30px rgba(0,0,0,0.9)",
              }}
            >
              {headline}
            </div>
          )}
          <StatBlock x={AX} y={AY} stat={a} startF={10} accent={accent} textColor={textColor} frame={frame} />
          <StatBlock x={BX} y={BY} stat={b} startF={175} accent={accent} textColor={textColor} frame={frame} />
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
