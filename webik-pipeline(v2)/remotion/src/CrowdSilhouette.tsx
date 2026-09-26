import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { ThreeCanvas } from "@remotion/three";
import { fontFamily } from "./theme";
import { ease, mspring, enterUp } from "./anim";

export type CrowdSilhouetteProps = {
  kicker?: string;
  title?: string;
  countText?: string;       // большая анимированная цифра
  countLabel?: string;
  stats?: { value: string; label: string }[];  // доп. цифры справа (штаты/языки)
  accent?: string;
  light?: boolean;          // true = чёрные силуэты на светлом (классика), false = светлые на тёмном
  caption?: string;
  durationInFrames?: number;
};

const rnd = (i: number, s = 1) => { const x = Math.sin(i * 41.3 + s * 8.7) * 43758.5; return x - Math.floor(x); };

// Одна человеческая фигура из примитивов (flat-shader → идеальный силуэт). Шаг анимируется по кадру.
const Figure: React.FC<{ frame: number; ph: number; col: string; scale: number }> = ({ frame, ph, col, scale }) => {
  const t = (frame + ph) / 8;
  const swing = Math.sin(t) * 0.5;             // руки/ноги
  const bob = Math.abs(Math.sin(t)) * 0.05;    // вертикальный боб при шаге
  const mat = <meshBasicMaterial color={col} toneMapped={false} />;
  return (
    <group scale={[scale, scale, scale]} position={[0, bob, 0]}>
      {/* голова */}
      <mesh position={[0, 1.62, 0]}><sphereGeometry args={[0.17, 16, 16]} />{mat}</mesh>
      {/* торс */}
      <mesh position={[0, 1.15, 0]}><capsuleGeometry args={[0.16, 0.5, 6, 12]} />{mat}</mesh>
      {/* руки */}
      <mesh position={[-0.24, 1.2, 0]} rotation={[swing, 0, 0.12]}><capsuleGeometry args={[0.06, 0.5, 4, 8]} />{mat}</mesh>
      <mesh position={[0.24, 1.2, 0]} rotation={[-swing, 0, -0.12]}><capsuleGeometry args={[0.06, 0.5, 4, 8]} />{mat}</mesh>
      {/* ноги */}
      <mesh position={[-0.1, 0.5, 0]} rotation={[-swing, 0, 0]}><capsuleGeometry args={[0.075, 0.6, 4, 8]} />{mat}</mesh>
      <mesh position={[0.1, 0.5, 0]} rotation={[swing, 0, 0]}><capsuleGeometry args={[0.075, 0.6, 4, 8]} />{mat}</mesh>
    </group>
  );
};

const Crowd: React.FC<{ frame: number; col: string; n: number }> = ({ frame, col, n }) => {
  const figs = React.useMemo(() => Array.from({ length: n }).map((_, i) => {
    const row = Math.floor(i / 8);
    const z = -row * 1.7 - 0.5;
    const x = ((i % 8) - 3.5) * 1.5 + (rnd(i, 3) - 0.5) * 0.8;
    const sc = 1 - row * 0.06;
    return { i, x, z, sc, ph: rnd(i, 1) * 30, drift: 0.3 + rnd(i, 2) * 0.5 };
  }), [n]);
  return (
    <group>
      {figs.map((f) => {
        const x = f.x + Math.sin((frame + f.ph) / 40) * 0.15;
        const appear = interpolate(frame, [4 + f.i * 1.2, 20 + f.i * 1.2], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
        return (
          <group key={f.i} position={[x, -1.2, f.z]} scale={[appear, appear, appear]}>
            <Figure frame={frame} ph={f.ph} col={col} scale={f.sc} />
          </group>
        );
      })}
    </group>
  );
};

// Силуэтная 3D-сцена толпы: flat-shader (без света/теней) → чистые узнаваемые силуэты людей.
// Высокий контраст (1-bit). Для «1.4 млрд / штаты / паломники / последователи».
export const CrowdSilhouette: React.FC<CrowdSilhouetteProps> = ({
  kicker = "ИНДИЯ",
  title = "1,4 МИЛЛИАРДА ЧЕЛОВЕК",
  countText = "1 400 000 000",
  countLabel = "человек",
  stats = [{ value: "22", label: "официальных языка" }, { value: "29", label: "штатов-«стран»" }],
  accent = "#d24a2a",
  light = true,
  caption = "",
  durationInFrames,
}) => {
  const frame = useCurrentFrame();
  const { width, height, durationInFrames: dif } = useVideoConfig();
  const dur = durationInFrames ?? dif;
  const exit = interpolate(frame, [dur - 16, dur], [1, 0], { extrapolateLeft: "clamp" });
  const bg = light ? "#ece7dd" : "#0a0a0c";
  const fig = light ? "#12100e" : "#f2efe8";
  const camX = Math.sin(frame / 90) * 1.2;
  const target = parseInt(countText.replace(/\D/g, "") || "0", 10);
  const cnt = Math.round(mspring(frame, 30, { stiffness: 30, damping: 20, delay: 10 }) * target);

  return (
    <AbsoluteFill style={{ background: bg, opacity: exit, fontFamily: fontFamily("oswald") }}>
      {/* лёгкая текстура-грейн для «плёнки» */}
      <ThreeCanvas width={width} height={height} camera={{ position: [camX, 0.8, 7.5], fov: 42 }}>
        <ambientLight intensity={1} />
        <Crowd frame={frame} col={fig} n={40} />
        {/* земля-силуэт (тонкая полоса) */}
        <mesh position={[0, -1.35, -3]} rotation={[-Math.PI / 2, 0, 0]}>
          <planeGeometry args={[60, 30]} />
          <meshBasicMaterial color={light ? "#ddd6c8" : "#111114"} toneMapped={false} />
        </mesh>
      </ThreeCanvas>

      {/* виньетка + грейн */}
      <AbsoluteFill style={{ boxShadow: `inset 0 0 320px ${light ? "rgba(150,140,120,0.5)" : "rgba(0,0,0,0.85)"}`, pointerEvents: "none" }} />

      {/* заголовок */}
      <AbsoluteFill style={{ justifyContent: "flex-start", alignItems: "flex-start", padding: "78px 90px", pointerEvents: "none" }}>
        {(() => { const k = enterUp(frame, 30, 2, 26); const t = enterUp(frame, 30, 8, 42, { stiffness: 125, damping: 18 }); return (<>
          <div style={{ color: accent, fontSize: 30, fontWeight: 700, letterSpacing: 8, opacity: k.opacity, transform: `translateY(${k.translateY}px)` }}>{kicker}</div>
          <div style={{ color: fig, fontSize: 74, fontWeight: 800, lineHeight: 1.0, textShadow: light ? "none" : "0 6px 30px rgba(0,0,0,0.7)", marginTop: 6, opacity: t.opacity, transform: `translateY(${t.translateY}px)` }}>{title}</div>
        </>); })()}
      </AbsoluteFill>

      {/* большая цифра + доп.статы справа — в панели с подложкой (читаемо над силуэтами) */}
      <div style={{ position: "absolute", right: 70, top: 250, textAlign: "right", padding: "26px 30px", borderRadius: 12,
        background: light ? "rgba(236,231,221,0.82)" : "rgba(10,10,12,0.72)", backdropFilter: "blur(2px)",
        boxShadow: light ? "0 10px 40px rgba(120,110,90,0.25)" : "0 10px 40px rgba(0,0,0,0.6)" }}>
        <div style={{ color: accent, fontSize: 70, fontWeight: 800, fontVariantNumeric: "tabular-nums", lineHeight: 1, fontFamily: fontFamily("oswald") }}>{cnt.toLocaleString("ru-RU")}</div>
        <div style={{ color: fig, fontSize: 25, fontWeight: 600, marginTop: 2 }}>{countLabel}</div>
        <div style={{ marginTop: 22, paddingTop: 18, borderTop: `2px solid ${fig}22`, display: "flex", flexDirection: "column", gap: 12, alignItems: "flex-end" }}>
          {stats.map((s, i) => { const on = mspring(frame, 30, { stiffness: 150, damping: 14, delay: 40 + i * 10 }); return (
            <div key={i} style={{ opacity: Math.min(1, on), transform: `translateX(${(1 - on) * 30}px)`, display: "flex", alignItems: "baseline", gap: 12, whiteSpace: "nowrap" }}>
              <span style={{ color: accent, fontSize: 46, fontWeight: 800, fontFamily: fontFamily("oswald") }}>{s.value}</span>
              <span style={{ color: fig, fontSize: 23, fontWeight: 600 }}>{s.label}</span>
            </div>); })}
        </div>
      </div>

      {caption && (
        <div style={{ position: "absolute", left: 0, right: 0, bottom: 60, textAlign: "center", padding: "0 200px",
          color: fig, fontSize: 32, fontWeight: 600, fontFamily: fontFamily("montserrat"),
          opacity: interpolate(frame, [40, 54], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) * exit }}>{caption}</div>
      )}
    </AbsoluteFill>
  );
};
