import React from "react";
import {
  AbsoluteFill,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { PALETTE, fontFamily } from "./theme";

export type SurveillanceGridProps = {
  title?: string;
  accent?: string;
};

// Полёт камеры сквозь 3D-сеть следящих «глаз/камер» с линиями связи и разверткой.
export const SurveillanceGrid: React.FC<SurveillanceGridProps> = ({
  title = "ТОТАЛЬНАЯ СЛЕЖКА",
  accent = PALETTE.red,
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  const fly = interpolate(frame, [0, durationInFrames], [0, 5200], { extrapolateRight: "clamp" });
  const sway = Math.sin(frame / 40) * 4;
  const swayY = Math.cos(frame / 52) * 2.5;
  const intro = interpolate(frame, [0, 16], [0, 1], { extrapolateRight: "clamp" });
  const exit = interpolate(frame, [durationInFrames - 20, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });

  // узлы сетки: несколько «стен» в глубину, в каждой сетка X×Y
  const COLS = 5, ROWS = 3, DEPTH = 8;
  const nodes: { x: number; y: number; z: number; on: number; key: string }[] = [];
  for (let d = 0; d < DEPTH; d++) {
    for (let r = 0; r < ROWS; r++) {
      for (let c = 0; c < COLS; c++) {
        const x = (c - (COLS - 1) / 2) * 440;
        const y = (r - (ROWS - 1) / 2) * 380;
        const z = -700 - d * 560;
        // мигание «активной» камеры псевдослучайно, но детерминированно
        const on = (Math.sin(d * 7.1 + r * 3.3 + c * 1.7 + frame / 9) + 1) / 2;
        nodes.push({ x, y, z, on, key: `${d}-${r}-${c}` });
      }
    }
  }

  return (
    <AbsoluteFill style={{ fontFamily: fontFamily("oswald"), opacity: exit }}>
      <AbsoluteFill style={{ background: "radial-gradient(circle at 50% 50%, #200606 0%, #0c0303 55%, #050101 100%)" }} />

      <AbsoluteFill style={{ perspective: 1000, opacity: intro }}>
        <div
          style={{
            position: "absolute",
            left: "50%",
            top: "50%",
            transformStyle: "preserve-3d",
            transform: `translate(-50%,-50%) rotateY(${sway}deg) rotateX(${swayY}deg) translateZ(${fly}px)`,
          }}
        >
          {nodes.map(({ x, y, z, on, key }) => (
            <div
              key={key}
              style={{
                position: "absolute",
                transform: `translate3d(${x}px, ${y}px, ${z}px)`,
                marginLeft: -60,
                marginTop: -60,
                width: 120,
                height: 120,
              }}
            >
              {/* корпус камеры / глаз */}
              <svg width={120} height={120} viewBox="-60 -60 120 120" style={{ filter: `drop-shadow(0 0 ${8 + on * 22}px ${accent})` }}>
                <circle cx="0" cy="0" r="52" fill="none" stroke={accent} strokeWidth="3" opacity={0.5 + on * 0.5} />
                <circle cx="0" cy="0" r="34" fill="#1a0505" stroke={accent} strokeWidth="2" opacity="0.8" />
                <circle cx="0" cy="0" r={12 + on * 6} fill={accent} opacity={0.6 + on * 0.4} />
                {/* «веки»-скобки */}
                <path d="M-50 0 Q0 -46 50 0" fill="none" stroke={accent} strokeWidth="3" opacity={on} />
                <path d="M-50 0 Q0 46 50 0" fill="none" stroke={accent} strokeWidth="3" opacity={on} />
              </svg>
            </div>
          ))}
        </div>
      </AbsoluteFill>

      {/* горизонтальная развёртка */}
      <AbsoluteFill style={{ opacity: 0.5 * intro, pointerEvents: "none" }}>
        <div style={{ position: "absolute", left: 0, right: 0, top: `${(frame * 1.3) % 100}%`, height: 90, background: `linear-gradient(180deg, transparent, ${accent}33, transparent)` }} />
      </AbsoluteFill>
      {/* скан-лайны + виньетка */}
      <AbsoluteFill style={{ background: "repeating-linear-gradient(0deg, rgba(217,40,40,0.06) 0px, rgba(217,40,40,0.06) 1px, transparent 3px, transparent 6px)", pointerEvents: "none" }} />
      <AbsoluteFill style={{ boxShadow: "inset 0 0 300px rgba(0,0,0,0.85)", pointerEvents: "none" }} />

      {/* хедер-терминал */}
      <AbsoluteFill style={{ justifyContent: "flex-start", alignItems: "flex-start", padding: 60, opacity: intro }}>
        <div style={{ color: accent, fontSize: 30, letterSpacing: 6, fontWeight: 600 }}>
          ● LIVE · {(Math.floor(frame / 60)).toString().padStart(2, "0")}:{(frame % 60).toString().padStart(2, "0")} · СЕКТОР {(frame % 88 + 12)}
        </div>
      </AbsoluteFill>

      {/* заголовок */}
      {title && (
        <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: 90, opacity: interpolate(frame, [16, 34], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) * exit }}>
          <div style={{ color: PALETTE.cream, fontSize: 86, fontWeight: 800, letterSpacing: 6, textTransform: "uppercase", textShadow: `0 0 40px ${accent}, 0 6px 30px rgba(0,0,0,0.85)` }}>{title}</div>
        </AbsoluteFill>
      )}
    </AbsoluteFill>
  );
};
