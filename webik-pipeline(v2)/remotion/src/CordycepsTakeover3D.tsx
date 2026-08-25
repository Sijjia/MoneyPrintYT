import React from "react";
import { AbsoluteFill, Easing, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { ThreeCanvas } from "@remotion/three";
import { fontFamily } from "./theme";

export type CordycepsTakeover3DProps = {
  title?: string;
  sub?: string;
  accent?: string;
};

const rnd = (i: number, s = 1) => {
  const x = Math.sin(i * 45.13 + s * 91.7) * 43758.5453;
  return x - Math.floor(x);
};

// Длинная кинематографичная 3D-сцена (Three.js/R3F): гриб-кордицепс захватывает
// муравья. Камера облетает, из головы в реальном 3D растёт стебель, споры
// разлетаются, зелёное биолюм-свечение и туман. Рассказывает «сценарий».
const Scene: React.FC<{ accent: string }> = ({ accent }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const t = frame / durationInFrames; // 0..1

  // рост стебля гриба
  const grow = interpolate(frame, [30, durationInFrames * 0.62], [0, 1], { easing: Easing.out(Easing.cubic), extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const stalkH = 1.25 * grow;
  const burst = interpolate(frame, [durationInFrames * 0.52, durationInFrames * 0.92], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  // сегменты стебля (изгиб) — растёт из ГОЛОВЫ, плотно перекрываются = непрерывный отросток
  const segs = 22;
  const stalk = Array.from({ length: segs }).map((_, i) => {
    const f = i / (segs - 1);
    const h = f * stalkH;
    const bend = Math.sin(f * 1.5) * 0.22;
    return [0.5 + bend, 0.5 + h, 0.02 + Math.cos(f * 1.5) * 0.06] as [number, number, number];
  });
  const tip = stalk[segs - 1];

  // споры
  const spores = Array.from({ length: 60 }).map((_, i) => {
    const rise = ((frame * (0.6 + rnd(i, 3) * 1.2)) + rnd(i, 1) * 200) % 60;
    const ph = rnd(i, 2) * Math.PI * 2;
    const rad = 0.15 + (rise / 60) * (1.6 + rnd(i, 4));
    return {
      pos: [tip[0] + Math.cos(ph) * rad, tip[1] + rise * 0.045, tip[2] + Math.sin(ph) * rad] as [number, number, number],
      s: (0.02 + rnd(i, 5) * 0.05) * (0.4 + burst),
      op: (0.3 + rnd(i, 6) * 0.6) * burst,
    };
  });

  const legAngles = [-0.9, -0.5, -0.1, 0.3, 0.7, 1.1];

  return (
    <>
      <fog attach="fog" args={["#04120a", 6, 17]} />
      <ambientLight intensity={0.5} />
      <pointLight position={[3.5, 4.5, 4]} intensity={2.2} color="#eaffe0" />
      <pointLight position={[-4, 1.5, -3]} intensity={0.9} color={accent} />
      <pointLight position={[-2, 2.5, 4]} intensity={0.8} color="#8fd1ff" />
      {/* биолюм-свет от кончика гриба */}
      <pointLight position={[tip[0], tip[1], tip[2]]} intensity={2.6 * grow} color={accent} distance={8} />

      {/* земля/подложка */}
      <mesh position={[0, -0.75, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <circleGeometry args={[9, 48]} />
        <meshStandardMaterial color="#0a1a0e" roughness={1} metalness={0} />
      </mesh>
      {/* лист-опора */}
      <mesh position={[0, -0.2, 0]} rotation={[-Math.PI / 2 + 0.15, 0, 0.2]}>
        <circleGeometry args={[1.7, 40]} />
        <meshStandardMaterial color="#123a1c" roughness={0.8} metalness={0.05} emissive="#0a2412" emissiveIntensity={0.4} />
      </mesh>

      {/* муравей (профиль из эллипсоидов) */}
      <group position={[0, 0, 0]} rotation={[0, 0.4, 0]}>
        {/* брюшко */}
        <mesh position={[-0.55, 0.28, 0]} scale={[0.55, 0.4, 0.42]}>
          <sphereGeometry args={[1, 24, 24]} />
          <meshStandardMaterial color="#150f0a" roughness={0.5} metalness={0.25} />
        </mesh>
        {/* грудь */}
        <mesh position={[0, 0.3, 0]} scale={[0.28, 0.26, 0.26]}>
          <sphereGeometry args={[1, 24, 24]} />
          <meshStandardMaterial color="#241a10" roughness={0.45} metalness={0.3} emissive="#0e2410" emissiveIntensity={0.35} />
        </mesh>
        {/* голова */}
        <mesh position={[0.5, 0.42, 0]} scale={[0.32, 0.3, 0.3]}>
          <sphereGeometry args={[1, 24, 24]} />
          <meshStandardMaterial color="#241a10" roughness={0.45} metalness={0.3} emissive="#0e2410" emissiveIntensity={0.35} />
        </mesh>
        {/* глаз (заражён — светится) */}
        <mesh position={[0.72, 0.48, 0.16]}>
          <sphereGeometry args={[0.05, 12, 12]} />
          <meshStandardMaterial color={accent} emissive={accent} emissiveIntensity={2} />
        </mesh>
        {/* жвалы/усики */}
        <mesh position={[0.82, 0.36, 0]} rotation={[0, 0, -0.5]} scale={[0.12, 0.02, 0.02]}>
          <cylinderGeometry args={[1, 1, 1, 8]} />
          <meshStandardMaterial color="#0d0906" />
        </mesh>
        {/* лапки */}
        {legAngles.map((a, i) => (
          <mesh key={i} position={[Math.sin(a) * 0.35, 0.02, Math.cos(a) * 0.18 * (i % 2 ? 1 : -1)]} rotation={[0, 0, 0.5 - a * 0.4]} scale={[0.014, 0.34, 0.014]}>
            <cylinderGeometry args={[1, 1, 1, 6]} />
            <meshStandardMaterial color="#0d0906" />
          </mesh>
        ))}
      </group>

      {/* стебель гриба из головы — толстый у основания, сужается кверху, плотно */}
      {stalk.map((p, i) => (
        <mesh key={i} position={p} scale={0.15 - (i / segs) * 0.07}>
          <sphereGeometry args={[1, 14, 14]} />
          <meshStandardMaterial color="#a9d97e" emissive={accent} emissiveIntensity={0.9 + (i / segs) * 1.1} roughness={0.55} />
        </mesh>
      ))}
      {/* спорангий (светящийся кончик) */}
      {grow > 0.05 && (
        <group position={tip}>
          <mesh scale={0.16 + 0.1 * grow}>
            <sphereGeometry args={[1, 24, 24]} />
            <meshStandardMaterial color="#b6f28a" emissive={accent} emissiveIntensity={1.8} roughness={0.4} />
          </mesh>
          <mesh scale={0.34 + 0.5 * burst}>
            <sphereGeometry args={[1, 16, 16]} />
            <meshBasicMaterial color={accent} transparent opacity={0.12 + 0.08 * grow} />
          </mesh>
        </group>
      )}

      {/* споры */}
      {spores.map((sp, i) => (
        <mesh key={i} position={sp.pos} scale={sp.s}>
          <sphereGeometry args={[1, 8, 8]} />
          <meshStandardMaterial color={accent} emissive={accent} emissiveIntensity={1.5} transparent opacity={sp.op} />
        </mesh>
      ))}
    </>
  );
};

export const CordycepsTakeover3D: React.FC<CordycepsTakeover3DProps> = ({
  title = "ЗАХВАТ ТЕЛА",
  sub = "гриб-кордицепс превращает муравья в зомби",
  accent = "#8fd14f",
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames, width, height } = useVideoConfig();
  const intro = interpolate(frame, [0, 24], [0, 1], { extrapolateRight: "clamp" });
  const exit = interpolate(frame, [durationInFrames - 20, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });
  const titleIn = interpolate(frame, [durationInFrames * 0.12, durationInFrames * 0.2], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  // облёт камеры + наезд
  const ang = interpolate(frame, [0, durationInFrames], [-0.7, 0.9], { easing: Easing.inOut(Easing.sin) });
  const camR = interpolate(frame, [0, durationInFrames], [4.6, 3.2], { easing: Easing.inOut(Easing.sin) });
  const camY = interpolate(frame, [0, durationInFrames], [1.9, 1.2]);
  const camX = Math.sin(ang) * camR;
  const camZ = Math.cos(ang) * camR;

  return (
    <AbsoluteFill style={{ fontFamily: fontFamily("oswald"), opacity: exit, background: "#04120a" }}>
      <AbsoluteFill style={{ opacity: intro }}>
        <ThreeCanvas width={width} height={height} camera={{ position: [camX, camY, camZ], fov: 52 }}>
          <Scene accent={accent} />
        </ThreeCanvas>
      </AbsoluteFill>
      <AbsoluteFill style={{ background: "radial-gradient(ellipse at 50% 55%, transparent 42%, rgba(2,10,5,0.66) 82%)", pointerEvents: "none" }} />
      <AbsoluteFill style={{ boxShadow: "inset 0 0 300px rgba(0,0,0,0.72)", pointerEvents: "none" }} />
      <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "flex-start", padding: 90, opacity: titleIn * exit }}>
        <div>
          <div style={{ color: "#eafcf6", fontSize: 100, fontWeight: 800, letterSpacing: 3, textShadow: `0 0 40px ${accent}` }}>{title}</div>
          <div style={{ color: accent, fontSize: 34, fontWeight: 700, letterSpacing: 2, textTransform: "uppercase", maxWidth: 900 }}>{sub}</div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
