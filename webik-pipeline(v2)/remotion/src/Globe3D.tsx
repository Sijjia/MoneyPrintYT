import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { ThreeCanvas } from "@remotion/three";
import { PALETTE } from "./theme";

export type GlobePlace = { lat: number; lon: number; label?: string };
export type Globe3DProps = {
  places?: GlobePlace[];
  accent?: string;
};

const R = 2;

// широта/долгота → точка на сфере
const latLon = (lat: number, lon: number, radius: number): [number, number, number] => {
  const phi = ((90 - lat) * Math.PI) / 180;
  const theta = ((lon + 180) * Math.PI) / 180;
  return [
    -radius * Math.sin(phi) * Math.cos(theta),
    radius * Math.cos(phi),
    radius * Math.sin(phi) * Math.sin(theta),
  ];
};

const Planet: React.FC<{ accent: string; places: GlobePlace[] }> = ({ accent, places }) => {
  const frame = useCurrentFrame();
  const rot = frame * 0.005;
  return (
    <group rotation={[0.32, rot, 0]}>
      {/* планета */}
      <mesh>
        <sphereGeometry args={[R, 64, 64]} />
        <meshStandardMaterial color="#0e1a30" emissive="#060c18" roughness={0.85} metalness={0.15} />
      </mesh>
      {/* каркас-сетка */}
      <mesh scale={1.004}>
        <sphereGeometry args={[R, 34, 24]} />
        <meshBasicMaterial color="#274169" wireframe transparent opacity={0.32} />
      </mesh>
      {/* атмосфера (обод) */}
      <mesh scale={1.07}>
        <sphereGeometry args={[R, 48, 48]} />
        <meshBasicMaterial color={accent} transparent opacity={0.07} side={2} />
      </mesh>
      {/* пины */}
      {places.map((p, i) => {
        const s = interpolate(frame, [12 + i * 7, 26 + i * 7], [0, 1], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        });
        const pos = latLon(p.lat, p.lon, R * 1.02);
        const pulse = 1 + 0.35 * Math.max(0, Math.sin(frame / 10 - i));
        return (
          <group key={i} position={pos}>
            <mesh scale={s}>
              <sphereGeometry args={[0.055, 16, 16]} />
              <meshBasicMaterial color={accent} />
            </mesh>
            <mesh scale={s * pulse}>
              <sphereGeometry args={[0.085, 16, 16]} />
              <meshBasicMaterial color={accent} transparent opacity={0.25} />
            </mesh>
          </group>
        );
      })}
    </group>
  );
};

// 3D-глобус культов — камера смотрит на медленно вращающуюся планету с пинами.
export const Globe3D: React.FC<Globe3DProps> = ({ places = [], accent = PALETTE.red }) => {
  const { width, height } = useVideoConfig();
  return (
    <AbsoluteFill style={{ background: "radial-gradient(circle at 50% 45%, #0a1428 0%, #04060c 72%)" }}>
      <ThreeCanvas width={width} height={height} camera={{ position: [0, 0, 5.2], fov: 42 }}>
        <ambientLight intensity={0.55} />
        <pointLight position={[6, 4, 6]} intensity={1.4} color="#ffffff" />
        <pointLight position={[-6, -2, -4]} intensity={0.5} color={accent} />
        <Planet accent={accent} places={places} />
      </ThreeCanvas>
    </AbsoluteFill>
  );
};
