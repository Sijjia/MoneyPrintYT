import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

export type TopicCardProps = {
  title: string;
  level: string;
  topicIndex: number;
  /** true = прозрачный фон (оверлей поверх видео); false = тёмный фон (титр-карточка). */
  transparent?: boolean;
};

const GOLD = "#c8a24a";
const CREAM = "#f4f1ea";
const FONT =
  "'Montserrat', 'Segoe UI', 'Arial', 'Helvetica Neue', system-ui, sans-serif";

export const TopicCard: React.FC<TopicCardProps> = ({
  title,
  level,
  topicIndex,
  transparent = false,
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  // Вход: пружина для мягкого «наплыва»
  const enter = spring({ frame, fps, config: { damping: 200, mass: 0.9 } });
  const titleY = interpolate(enter, [0, 1], [46, 0]);
  const titleBlur = interpolate(enter, [0, 1], [18, 0]);
  const titleOpacity = interpolate(frame, [0, 16], [0, 1], {
    extrapolateRight: "clamp",
  });

  // Надзаголовок (уровень · тема)
  const kickerOpacity = interpolate(frame, [6, 22], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Растущая акцентная линия под заголовком
  const lineW = interpolate(enter, [0, 1], [0, 560]);

  // Мягкий постоянный дрейф — чтобы кадр «дышал», не был статичным
  const drift = Math.sin(frame / 42) * 4;

  // Выход: плавное затухание в последние 18 кадров
  const exitOpacity = interpolate(
    frame,
    [durationInFrames - 18, durationInFrames],
    [1, 0],
    { extrapolateLeft: "clamp" }
  );

  const bg = transparent
    ? "transparent"
    : "radial-gradient(circle at 50% 42%, #14171c 0%, #07080a 78%)";

  return (
    <AbsoluteFill style={{ background: bg, opacity: exitOpacity, fontFamily: FONT }}>
      {/* лёгкая виньетка для глубины (только на тёмном фоне) */}
      {!transparent && (
        <AbsoluteFill
          style={{
            background:
              "radial-gradient(circle at 50% 50%, transparent 55%, rgba(0,0,0,0.55) 100%)",
          }}
        />
      )}

      <AbsoluteFill
        style={{
          justifyContent: "center",
          alignItems: "center",
          flexDirection: "column",
          padding: "0 120px",
        }}
      >
        <div
          style={{
            opacity: kickerOpacity,
            transform: `translateY(${drift}px)`,
            letterSpacing: 10,
            color: GOLD,
            fontSize: 32,
            fontWeight: 600,
            textTransform: "uppercase",
            marginBottom: 30,
          }}
        >
          {level} · Тема {topicIndex}
        </div>

        <div
          style={{
            opacity: titleOpacity,
            filter: `blur(${titleBlur}px)`,
            transform: `translateY(${titleY}px)`,
            color: CREAM,
            fontSize: 98,
            fontWeight: 800,
            textAlign: "center",
            maxWidth: 1560,
            lineHeight: 1.04,
            textTransform: "uppercase",
            textShadow: "0 8px 40px rgba(0,0,0,0.6)",
          }}
        >
          {title}
        </div>

        <div
          style={{
            marginTop: 44,
            width: lineW,
            height: 4,
            borderRadius: 2,
            background: `linear-gradient(90deg, transparent, ${GOLD}, transparent)`,
          }}
        />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
