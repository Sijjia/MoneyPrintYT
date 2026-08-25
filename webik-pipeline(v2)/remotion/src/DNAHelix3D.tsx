import React from "react";
import { AbsoluteFill, Easing, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { fontFamily } from "./theme";

export type DNAHelix3DProps = {
  title?: string;
  sub?: string;
  accent?: string;
};

const rnd = (i: number, s = 1) => {
  const x = Math.sin(i * 51.13 + s * 19.7) * 43758.5453;
  return x - Math.floor(x);
};

// Реалистичная 3D двойная спираль ДНК: две сахаро-фосфатные цепи + пары оснований,
// медленный оборот + подъём камеры, биолюминесцентное свечение, пылинки, глубина (DOF).
export const DNAHelix3D: React.FC<DNAHelix3DProps> = ({
  title = "ДНК",
  sub = "код жизни",
  accent = "#1fa48a",
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames, width, height } = useVideoConfig();

  const intro = interpolate(frame, [0, 22], [0, 1], { extrapolateRight: "clamp" });
  const exit = interpolate(frame, [durationInFrames - 16, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });
  const titleIn = interpolate(frame, [14, 34], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  const RUNGS = 40;
  const rise = 26;               // вертикальный шаг между парами (px)
  const radius = 155;            // радиус спирали
  const turn = 32;               // градусов на пару
  const spin = frame * 1.05;     // оборот всей молекулы
  const drift = interpolate(frame, [0, durationInFrames], [rise * 3.2, -rise * 3.2],
    { easing: Easing.inOut(Easing.sin) }); // «камера» плывёт вдоль оси
  const tilt = interpolate(frame, [0, durationInFrames], [-9, 9], { easing: Easing.inOut(Easing.sin) });

  const cx = width / 2;
  const cy = height / 2;

  return (
    <AbsoluteFill style={{ fontFamily: fontFamily("oswald"), opacity: exit }}>
      {/* фон: холодная органика */}
      <AbsoluteFill style={{ background: "radial-gradient(ellipse at 50% 42%, #0a1f24 0%, #071417 45%, #04090b 100%)" }} />
      {/* пылинки/частицы среды */}
      <AbsoluteFill style={{ opacity: intro * 0.8 }}>
        {Array.from({ length: 46 }).map((_, i) => {
          const p = (frame * (0.2 + rnd(i, 3) * 0.5) + rnd(i, 1) * 900) % (height + 80);
          return (
            <div key={i} style={{
              position: "absolute", left: `${rnd(i, 2) * 100}%`, top: p - 40,
              width: 2 + rnd(i, 5) * 3, height: 2 + rnd(i, 5) * 3, borderRadius: "50%",
              background: accent, opacity: 0.10 + rnd(i, 6) * 0.22,
              filter: `blur(${rnd(i, 7) * 2}px)`, boxShadow: `0 0 8px ${accent}`,
            }} />
          );
        })}
      </AbsoluteFill>

      {/* сцена со спиралью */}
      <AbsoluteFill style={{ perspective: 1400, opacity: intro }}>
        <div style={{
          position: "absolute", left: cx, top: cy,
          transformStyle: "preserve-3d",
          transform: `rotateX(${tilt}deg) translateY(${drift}px)`,
        }}>
          {Array.from({ length: RUNGS }).map((_, i) => {
            const y = (i - RUNGS / 2) * rise;
            const ang = (spin + i * turn) * (Math.PI / 180);
            const x1 = Math.cos(ang) * radius;
            const z1 = Math.sin(ang) * radius;
            const x2 = Math.cos(ang + Math.PI) * radius;
            const z2 = Math.sin(ang + Math.PI) * radius;
            // глубина → размер/яркость/блюр (DOF)
            const d1 = (z1 + radius) / (2 * radius);
            const d2 = (z2 + radius) / (2 * radius);
            const node = (x: number, z: number, d: number, hue: string) => (
              <div style={{
                position: "absolute",
                transform: `translate3d(${x}px, ${y}px, ${z}px)`,
                width: 20 + d * 16, height: 20 + d * 16, marginLeft: -(10 + d * 8), marginTop: -(10 + d * 8),
                borderRadius: "50%",
                background: `radial-gradient(circle at 35% 30%, #eafcf6, ${hue} 60%, #06312b)`,
                boxShadow: `0 0 ${8 + d * 22}px ${hue}`,
                opacity: 0.35 + d * 0.65, filter: `blur(${(1 - d) * 2.2}px)`,
              }} />
            );
            // «ступенька» — пара оснований между цепями.
            // Ширина = горизонтальное расстояние между цепями → естественно сужается
            // при обороте (цепи «сходятся» на ребре). Без поворота = чисто, не диагонали.
            const midx = (x1 + x2) / 2, midz = (z1 + z2) / 2, midd = (d1 + d2) / 2;
            const rw = Math.abs(x1 - x2);
            return (
              <div key={i} style={{ position: "absolute", transformStyle: "preserve-3d" }}>
                {/* перекладина (водородные связи) */}
                <div style={{
                  position: "absolute",
                  transform: `translate3d(${midx}px, ${y}px, ${midz}px)`,
                  width: rw, height: 4, marginLeft: -rw / 2, marginTop: -2, borderRadius: 3,
                  background: `linear-gradient(90deg, #7fe9d4, ${accent} 50%, #12907e)`,
                  opacity: (0.18 + midd * 0.42) * (rw / (2 * radius)) ** 0.5,
                  filter: `blur(${(1 - midd) * 1.2}px)`,
                  boxShadow: `0 0 ${5 + midd * 8}px ${accent}`,
                }} />
                {node(x1, z1, d1, accent)}
                {node(x2, z2, d2, "#12907e")}
              </div>
            );
          })}
        </div>
      </AbsoluteFill>

      {/* туман глубины + виньетка */}
      <AbsoluteFill style={{ background: "radial-gradient(ellipse at 50% 50%, transparent 30%, rgba(4,9,11,0.72) 78%)", pointerEvents: "none" }} />
      <AbsoluteFill style={{ boxShadow: "inset 0 0 320px rgba(0,0,0,0.8)", pointerEvents: "none" }} />

      {/* заголовок */}
      <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "flex-start", padding: 90, opacity: titleIn * exit }}>
        <div>
          <div style={{ color: "#eafcf6", fontSize: 118, fontWeight: 800, lineHeight: 0.92, letterSpacing: 2, textShadow: `0 0 40px ${accent}` }}>{title}</div>
          <div style={{ color: accent, fontSize: 46, fontWeight: 700, letterSpacing: 4, textTransform: "uppercase", textShadow: "0 6px 30px rgba(0,0,0,0.8)" }}>{sub}</div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
