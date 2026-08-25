import React from "react";
import {
  AbsoluteFill,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { PALETTE, fontFamily } from "./theme";

export type AbyssDescentProps = {
  title?: string;
  accent?: string;
};

const rnd = (i: number, s = 1) => {
  const x = Math.sin(i * 73.1 + s * 19.7) * 43758.5453;
  return x - Math.floor(x);
};

// Погружение в бездну: камера падает вниз сквозь холодные частицы к красному свечению.
export const AbyssDescent: React.FC<AbyssDescentProps> = ({
  title = "БЕЗДНА",
  accent = PALETTE.red,
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  const intro = interpolate(frame, [0, 20], [0, 1], { extrapolateRight: "clamp" });
  const exit = interpolate(frame, [durationInFrames - 20, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });
  const dive = interpolate(frame, [0, durationInFrames], [-200, 2600]);
  const sway = Math.sin(frame / 50) * 3;

  // частицы (пузыри/лёд) поднимаются вверх (камера падает)
  const parts = Array.from({ length: 90 }).map((_, i) => {
    const x = rnd(i, 1) * 100;
    const speed = 20 + rnd(i, 2) * 40;
    const y = (100 - ((frame * speed) / 30 + rnd(i, 3) * 100) % 130);
    const r = 1 + rnd(i, 4) * 4;
    return { x, y, r, o: 0.2 + rnd(i, 5) * 0.5, key: i };
  });
  // рваные ледяные стены по бокам, уходящие в глубину
  const shards = Array.from({ length: 10 }).flatMap((_, i) =>
    [-1, 1].map((side) => ({ z: -300 - i * 480, side, h: 500 + rnd(i, 6) * 400, key: `${i}-${side}` }))
  );

  return (
    <AbsoluteFill style={{ fontFamily: fontFamily("oswald"), opacity: exit }}>
      {/* градиент глубины: тёмный верх → кроваво-красное свечение внизу */}
      <AbsoluteFill style={{ background: "linear-gradient(180deg, #04070d 0%, #0a0608 45%, #3a0808 82%, #6e0d0d 100%)" }} />
      <AbsoluteFill style={{ background: "radial-gradient(ellipse at 50% 108%, rgba(217,40,40,0.5), transparent 55%)" }} />

      {/* 3D-стены */}
      <AbsoluteFill style={{ perspective: 1000, opacity: intro }}>
        <div style={{ position: "absolute", left: "50%", top: "50%", transformStyle: "preserve-3d", transform: `translate(-50%,-50%) rotateZ(${sway}deg) translateZ(${dive}px)` }}>
          {shards.map(({ z, side, h, key }) => (
            <div
              key={key}
              style={{
                position: "absolute",
                transform: `translate3d(${side * 640}px, 0px, ${z}px) rotateY(${side * 18}deg)`,
                width: 240,
                height: h,
                marginLeft: -120,
                marginTop: -h / 2,
                background: "linear-gradient(90deg, rgba(30,50,70,0.85), rgba(10,18,26,0.6))",
                clipPath: side < 0
                  ? "polygon(0 0, 100% 12%, 78% 50%, 100% 88%, 0 100%)"
                  : "polygon(0 12%, 100% 0, 100% 100%, 0 88%, 22% 50%)",
                boxShadow: `inset 0 0 60px rgba(0,0,0,0.6)`,
                opacity: 0.8,
              }}
            />
          ))}
        </div>
      </AbsoluteFill>

      {/* частицы */}
      <AbsoluteFill style={{ opacity: intro, pointerEvents: "none" }}>
        {parts.map((p) => (
          <div key={p.key} style={{ position: "absolute", left: `${p.x}%`, top: `${p.y}%`, width: p.r * 2, height: p.r * 2, borderRadius: "50%", background: "#bcd6ee", opacity: p.o, boxShadow: "0 0 6px rgba(180,214,238,0.6)" }} />
        ))}
      </AbsoluteFill>

      {/* виньетка */}
      <AbsoluteFill style={{ boxShadow: "inset 0 0 340px rgba(0,0,0,0.8)", pointerEvents: "none" }} />

      {title && (
        <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", opacity: interpolate(frame, [20, 40], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) * exit }}>
          <div style={{ color: PALETTE.cream, fontSize: 120, fontWeight: 800, letterSpacing: 14, textTransform: "uppercase", textShadow: `0 0 60px ${accent}, 0 8px 40px rgba(0,0,0,0.9)` }}>{title}</div>
        </AbsoluteFill>
      )}
    </AbsoluteFill>
  );
};
