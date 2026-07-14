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

export type MapPlace = { label: string; lat: number; lon: number };
export type MapPinsProps = {
  title?: string;
  places: MapPlace[];
  bgImage?: string | null; // не используется, для единообразия сигнатуры
  accent?: string;
  textColor?: string;
  font?: FontName;
};

// Карта равнопромежуточной проекции 1920x967 → линейный пересчёт координат.
const MAP_W = 1920;
const MAP_H = 967;
const MAP_TOP = (1080 - MAP_H) / 2; // центрируем по вертикали

const Pin: React.FC<{
  place: MapPlace;
  delay: number;
  accent: string;
  textColor: string;
}> = ({ place, delay, accent, textColor }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame: frame - delay, fps, config: { damping: 12, stiffness: 130, mass: 0.6 } });
  const drop = interpolate(s, [0, 1], [-30, 0]);
  const o = interpolate(s, [0, 1], [0, 1]);
  // пульс-кольцо
  const p = Math.max(0, ((frame - delay) % 48) / 48);
  const ringScale = 1 + p * 2.4;
  const ringOp = s * (1 - p) * 0.55;

  const xPct = ((place.lon + 180) / 360) * 100;
  const yPct = ((90 - place.lat) / 180) * 100;

  return (
    <div style={{ position: "absolute", left: `${xPct}%`, top: `${yPct}%`, transform: "translate(-50%,-50%)" }}>
      {/* пульс */}
      <div
        style={{
          position: "absolute",
          left: -14,
          top: -14,
          width: 28,
          height: 28,
          borderRadius: "50%",
          border: `2px solid ${accent}`,
          transform: `scale(${ringScale})`,
          opacity: ringOp,
        }}
      />
      {/* точка */}
      <div
        style={{
          position: "absolute",
          left: -9,
          top: -9 + drop,
          width: 18,
          height: 18,
          borderRadius: "50%",
          background: accent,
          opacity: o,
          boxShadow: `0 0 14px ${accent}`,
          border: "2px solid #0b0b0b",
        }}
      />
      {/* подпись */}
      <Censored
        text={place.label}
        style={{
          position: "absolute",
          left: -110,
          top: -58 + drop,
          width: 220,
          textAlign: "center",
          opacity: o,
          color: textColor,
          fontSize: 30,
          fontWeight: 700,
          letterSpacing: 1,
          display: "inline-block",
          textShadow: "0 2px 10px rgba(0,0,0,1), 0 0 6px rgba(0,0,0,1)",
        }}
      />
    </div>
  );
};

// Карта с пинами: география событий (перечисление мест).
export const MapPins: React.FC<MapPinsProps> = ({
  title = "",
  places,
  accent = PALETTE.red,
  textColor = PALETTE.cream,
  font = "oswald",
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const pl = places.slice(0, 6);

  const titleOpacity = interpolate(frame, [0, 12], [0, 1], { extrapolateRight: "clamp" });
  const exit = interpolate(frame, [durationInFrames - 16, durationInFrames], [1, 0], {
    extrapolateLeft: "clamp",
  });

  return (
    <AbsoluteFill style={{ fontFamily: fontFamily(font), opacity: exit, background: "#05070c" }}>
      {/* карта, тёмная обработка */}
      <div style={{ position: "absolute", left: 0, top: MAP_TOP, width: MAP_W, height: MAP_H }}>
        <Img
          src={staticFile("world_equi.jpg")}
          style={{
            width: "100%",
            height: "100%",
            objectFit: "fill",
            filter: "grayscale(1) brightness(0.42) contrast(1.08)",
          }}
        />
        {/* тёмно-синий тон поверх */}
        <AbsoluteFill style={{ background: "#0a1830", mixBlendMode: "multiply", opacity: 0.55 }} />
        {/* виньетка */}
        <AbsoluteFill style={{ boxShadow: "inset 0 0 300px rgba(0,0,0,0.8)" }} />
        {/* пины (в системе координат карты) */}
        {pl.map((p, i) => (
          <Pin key={i} place={p} delay={10 + i * 10} accent={accent} textColor={textColor} />
        ))}
      </div>

      {title && (
        <div
          style={{
            position: "absolute",
            top: 60,
            width: "100%",
            textAlign: "center",
            opacity: titleOpacity,
            color: textColor,
            fontSize: 52,
            fontWeight: 800,
            letterSpacing: 3,
            textTransform: "uppercase",
            textShadow: "0 4px 20px rgba(0,0,0,1)",
          }}
        >
          {title}
        </div>
      )}
    </AbsoluteFill>
  );
};
