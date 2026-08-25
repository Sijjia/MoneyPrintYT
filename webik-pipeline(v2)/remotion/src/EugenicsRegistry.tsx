import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { fontFamily } from "./theme";

export type EugenicsRegistryProps = {
  title?: string;
  counter?: string;
  stamp?: string;
  accent?: string;
};

const rnd = (i: number, s = 1) => {
  const x = Math.sin(i * 29.7 + s * 13.3) * 43758.5453;
  return x - Math.floor(x);
};

// Архив принудительной стерилизации: сетка карточек-досье, по каждой ОДНА за другой
// с размаху бьёт красный штамп. Счётчик растёт. Холодно, документально, динамично.
export const EugenicsRegistry: React.FC<EugenicsRegistryProps> = ({
  title = "ПРИНУДИТЕЛЬНАЯ СТЕРИЛИЗАЦИЯ",
  counter = "63 000",
  stamp = "СТЕРИЛИЗОВАН",
  accent = "#d92828",
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames, width, height, fps } = useVideoConfig();
  const intro = interpolate(frame, [0, 20], [0, 1], { extrapolateRight: "clamp" });
  const exit = interpolate(frame, [durationInFrames - 16, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });

  const cols = 5, rows = 3, N = cols * rows;
  const cardW = width * 0.15, cardH = height * 0.2;
  const gapX = (width - cols * cardW) / (cols + 1);
  const gapY = (height * 0.72 - rows * cardH) / (rows + 1);

  const target = parseInt((counter || "0").replace(/\D/g, "")) || 0;
  const cnt = Math.round(interpolate(frame, [24, durationInFrames - 30], [0, target], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }));

  return (
    <AbsoluteFill style={{ fontFamily: fontFamily("oswald"), opacity: exit }}>
      <AbsoluteFill style={{ background: "radial-gradient(ellipse at 50% 40%, #10171b 0%, #0a1013 55%, #05080a 100%)" }} />
      {/* заголовок */}
      <AbsoluteFill style={{ justifyContent: "flex-start", alignItems: "center", paddingTop: 40, opacity: intro }}>
        <div style={{ color: "#e8ecec", fontSize: 44, fontWeight: 800, letterSpacing: 3 }}>{title}</div>
      </AbsoluteFill>

      <AbsoluteFill style={{ opacity: intro }}>
        {Array.from({ length: N }).map((_, i) => {
          const c = i % cols, r = Math.floor(i / cols);
          const x = gapX + c * (cardW + gapX);
          const y = height * 0.16 + gapY + r * (cardH + gapY);
          const t0 = 26 + i * (durationInFrames * 0.5 / N);
          const slam = spring({ frame: frame - t0, fps, config: { damping: 9, stiffness: 200 } });
          const stampScale = interpolate(slam, [0, 1], [2.6, 1]);
          const stamped = frame > t0;
          return (
            <div key={i} style={{
              position: "absolute", left: x, top: y, width: cardW, height: cardH,
              background: "#171e22", border: "1px solid #2b3a40", borderRadius: 4,
              boxShadow: "0 8px 24px rgba(0,0,0,0.5)", overflow: "hidden",
            }}>
              {/* мугшот-плейсхолдер */}
              <div style={{ position: "absolute", left: 10, top: 10, width: cardW * 0.3, height: cardW * 0.3,
                borderRadius: "50%", background: "#33444b" }} />
              {/* строки данных (зачёркнуты) */}
              {[0, 1, 2, 3].map((k) => (
                <div key={k} style={{ position: "absolute", left: cardW * 0.42, top: 14 + k * 16,
                  width: cardW * 0.48 * (0.6 + rnd(i, k) * 0.4), height: 6, background: "#2f3d43", borderRadius: 3 }} />
              ))}
              {[0, 1, 2].map((k) => (
                <div key={"b" + k} style={{ position: "absolute", left: 10, top: cardH * 0.55 + k * 14,
                  width: cardW * 0.8 * (0.5 + rnd(i, k + 5) * 0.5), height: 6, background: "#26333a", borderRadius: 3 }} />
              ))}
              {/* КРАСНЫЙ ШТАМП */}
              {stamped && (
                <div style={{
                  position: "absolute", left: "50%", top: "54%",
                  transform: `translate(-50%,-50%) rotate(-14deg) scale(${stampScale})`,
                  color: accent, border: `3px solid ${accent}`, borderRadius: 6, padding: "4px 8px",
                  fontSize: cardW * 0.11, fontWeight: 800, letterSpacing: 1, opacity: 0.92,
                  boxShadow: `0 0 12px ${accent}66`, whiteSpace: "nowrap",
                }}>{stamp}</div>
              )}
            </div>
          );
        })}
      </AbsoluteFill>

      <AbsoluteFill style={{ boxShadow: "inset 0 0 280px rgba(0,0,0,0.72)", pointerEvents: "none" }} />
      {/* счётчик */}
      <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: 42, opacity: intro * exit }}>
        <div style={{ textAlign: "center" }}>
          <div style={{ color: accent, fontSize: 108, fontWeight: 800, lineHeight: 0.9, textShadow: `0 0 30px ${accent}88` }}>
            {cnt.toLocaleString("ru-RU")}
          </div>
          <div style={{ color: "#cdd6d6", fontSize: 28, fontWeight: 700, letterSpacing: 3, textTransform: "uppercase" }}>человек</div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
