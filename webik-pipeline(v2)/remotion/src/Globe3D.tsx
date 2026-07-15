import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { ThreeCanvas } from "@remotion/three";
import { PALETTE, fontFamily } from "./theme";

export type GlobePlace = { lat: number; lon: number; label?: string };
export type Globe3DProps = {
  places?: GlobePlace[];
  accent?: string;
  title?: string;
};

const R = 2;
const CAM_Z = 5.2;
const FOV = 42;

type Vec3 = [number, number, number];

// широта/долгота → точка на сфере радиуса radius
const latLon = (lat: number, lon: number, radius: number): Vec3 => {
  const phi = ((90 - lat) * Math.PI) / 180;
  const theta = ((lon + 180) * Math.PI) / 180;
  return [
    -radius * Math.sin(phi) * Math.cos(theta),
    radius * Math.cos(phi),
    radius * Math.sin(phi) * Math.sin(theta),
  ];
};

// поворот точки: сначала вокруг Y (ry), затем вокруг X (rx) — тот же порядок,
// что и у three Euler [rx, ry, 0]. Считаем в JS, чтобы совпасть с проекцией.
const rot = (p: Vec3, rx: number, ry: number): Vec3 => {
  const [x, y, z] = p;
  const cy = Math.cos(ry), sy = Math.sin(ry);
  const x1 = x * cy + z * sy;
  const z1 = -x * sy + z * cy;
  const cx = Math.cos(rx), sx = Math.sin(rx);
  const y2 = y * cx - z1 * sx;
  const z2 = y * sx + z1 * cx;
  return [x1, y2, z2];
};

const norm = (v: Vec3): Vec3 => {
  const m = Math.hypot(v[0], v[1], v[2]) || 1;
  return [v[0] / m, v[1] / m, v[2] / m];
};

const dot = (a: Vec3, b: Vec3) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];

// разворот, ставящий центр масс пинов лицом к камере (+Z)
const facingRotation = (places: GlobePlace[]): [number, number] => {
  let cx = 0, cy = 0, cz = 0;
  for (const p of places) {
    const [x, y, z] = norm(latLon(p.lat, p.lon, 1));
    cx += x; cy += y; cz += z;
  }
  const c = norm([cx, cy, cz]);
  const ry = Math.atan2(-c[0], c[2]);
  const m = Math.hypot(c[0], c[2]);
  const rx = Math.atan2(c[1], m || 1e-6);
  return [rx, ry];
};

// точки большой дуги между двумя местами (slerp по сфере), приподнятые над поверхностью
const arcPoints = (a: Vec3, b: Vec3, rx: number, ry: number, steps = 24): Float32Array => {
  const ua = norm(a), ub = norm(b);
  const om = Math.acos(Math.max(-1, Math.min(1, dot(ua, ub))));
  const so = Math.sin(om) || 1e-6;
  const arr = new Float32Array((steps + 1) * 3);
  for (let i = 0; i <= steps; i++) {
    const t = i / steps;
    const k0 = Math.sin((1 - t) * om) / so;
    const k1 = Math.sin(t * om) / so;
    const lift = 1 + 0.18 * Math.sin(Math.PI * t); // дуга выгибается наружу
    const px = (k0 * ua[0] + k1 * ub[0]) * R * lift;
    const py = (k0 * ua[1] + k1 * ub[1]) * R * lift;
    const pz = (k0 * ua[2] + k1 * ub[2]) * R * lift;
    const [wx, wy, wz] = rot([px, py, pz], rx, ry);
    arr[i * 3] = wx; arr[i * 3 + 1] = wy; arr[i * 3 + 2] = wz;
  }
  return arr;
};

const Arc: React.FC<{ points: Float32Array; accent: string; op: number }> = ({ points, accent, op }) => (
  <line>
    <bufferGeometry>
      <bufferAttribute attach="attributes-position" args={[points, 3]} />
    </bufferGeometry>
    <lineBasicMaterial color={accent} transparent opacity={op} />
  </line>
);

const Planet: React.FC<{ accent: string; rx: number; ry: number }> = ({ accent, rx, ry }) => (
  <group rotation={[rx, ry, 0]}>
    <mesh>
      <sphereGeometry args={[R, 64, 64]} />
      <meshStandardMaterial color="#0e1a30" emissive="#060c18" roughness={0.85} metalness={0.15} />
    </mesh>
    <mesh scale={1.004}>
      <sphereGeometry args={[R, 34, 24]} />
      <meshBasicMaterial color="#2a4670" wireframe transparent opacity={0.28} />
    </mesh>
    <mesh scale={1.08}>
      <sphereGeometry args={[R, 48, 48]} />
      <meshBasicMaterial color={accent} transparent opacity={0.09} side={2} />
    </mesh>
  </group>
);

// маркер-«булавка»: столбик от поверхности наружу + светящаяся голова
const Pin: React.FC<{ pos: Vec3; accent: string; grow: number; pulse: number }> = ({ pos, accent, grow, pulse }) => {
  const outer = norm(pos);
  const base: Vec3 = [outer[0] * R * 1.005, outer[1] * R * 1.005, outer[2] * R * 1.005];
  const head: Vec3 = [outer[0] * R * 1.16, outer[1] * R * 1.16, outer[2] * R * 1.16];
  const mid: Vec3 = [(base[0] + head[0]) / 2, (base[1] + head[1]) / 2, (base[2] + head[2]) / 2];
  const stick = new Float32Array([...base, ...head]);
  return (
    <group>
      <line>
        <bufferGeometry>
          <bufferAttribute attach="attributes-position" args={[stick, 3]} />
        </bufferGeometry>
        <lineBasicMaterial color={accent} transparent opacity={0.9 * grow} />
      </line>
      <group position={head} scale={grow}>
        <mesh>
          <sphereGeometry args={[0.07, 20, 20]} />
          <meshBasicMaterial color={accent} />
        </mesh>
        <mesh scale={pulse}>
          <sphereGeometry args={[0.12, 20, 20]} />
          <meshBasicMaterial color={accent} transparent opacity={0.22} />
        </mesh>
      </group>
      <mesh position={mid} />
    </group>
  );
};

// 3D-глобус культов: планета разворачивается к пинам, дуги связывают очаги,
// экранные подписи городов появляются по мере проявления пинов.
export const Globe3D: React.FC<Globe3DProps> = ({ places = [], accent = PALETTE.red, title = "" }) => {
  const { width, height, durationInFrames } = useVideoConfig();
  const frame = useCurrentFrame();

  const [rx0, ry0] = places.length ? facingRotation(places) : [0.3, 0];
  const drift = 0.14 * Math.sin(frame / 110); // лёгкое дыхание, не убегает
  const ry = ry0 + drift;
  const rx = rx0;

  // мировые позиции голов пинов (совпадают с three-поворотом [rx, ry, 0])
  const heads: Vec3[] = places.map((p) => rot(latLon(p.lat, p.lon, R * 1.16), rx, ry));

  // проекция мир → экран (камера в [0,0,CAM_Z], смотрит -Z)
  const tanHalf = Math.tan((FOV * Math.PI) / 180 / 2);
  const aspect = width / height;
  const project = (p: Vec3) => {
    const d = CAM_Z - p[2];
    const ndcX = p[0] / (d * tanHalf * aspect);
    const ndcY = p[1] / (d * tanHalf);
    return {
      x: (ndcX * 0.5 + 0.5) * width,
      y: (1 - (ndcY * 0.5 + 0.5)) * height,
      front: p[2] > 0.15, // на передней полусфере (не за планетой)
    };
  };

  const titleOp = interpolate(frame, [8, 24], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const exit = interpolate(frame, [durationInFrames - 20, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });

  // раскладка подписей с анти-коллизией: близкие по вертикали пины (один регион)
  // разводим по строкам, чтобы названия не наезжали; выноска ведёт к пину.
  type Lbl = { i: number; label: string; px: number; py: number; flip: boolean; ly: number };
  const labels: Lbl[] = places
    .map((p, i): Lbl | null => {
      if (!p.label) return null;
      const sp = project(heads[i]);
      if (!sp.front) return null;
      return { i, label: p.label, px: sp.x, py: sp.y, flip: sp.x > width * 0.72, ly: sp.y };
    })
    .filter((l): l is Lbl => l !== null);
  const ROW = 40;
  for (const side of [false, true]) {
    const grp = labels.filter((l) => l.flip === side).sort((a, b) => a.py - b.py);
    let lastY = -Infinity;
    for (const l of grp) {
      let ly = Math.max(40, Math.min(height - 52, l.py - 4));
      if (ly < lastY + ROW) ly = lastY + ROW;
      l.ly = Math.min(height - 52, ly);
      lastY = l.ly;
    }
  }

  const arcs = places.length > 1
    ? places.slice(0, -1).map((_, i) => ({
        key: i,
        pts: arcPoints(latLon(places[i].lat, places[i].lon, 1), latLon(places[i + 1].lat, places[i + 1].lon, 1), rx, ry),
        op: interpolate(frame, [30 + i * 6, 48 + i * 6], [0, 0.55], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
      }))
    : [];

  return (
    <AbsoluteFill style={{ background: "radial-gradient(circle at 50% 45%, #0a1428 0%, #04060c 72%)", opacity: exit }}>
      <ThreeCanvas width={width} height={height} camera={{ position: [0, 0, CAM_Z], fov: FOV }}>
        <ambientLight intensity={0.55} />
        <pointLight position={[6, 4, 6]} intensity={1.4} color="#ffffff" />
        <pointLight position={[-6, -2, -4]} intensity={0.5} color={accent} />
        <Planet accent={accent} rx={rx} ry={ry} />
        {arcs.map((a) => (
          <Arc key={a.key} points={a.pts} accent={accent} op={a.op} />
        ))}
        {places.map((p, i) => {
          const grow = interpolate(frame, [14 + i * 7, 30 + i * 7], [0, 1], {
            extrapolateLeft: "clamp", extrapolateRight: "clamp",
          });
          const pulse = 1 + 0.4 * Math.max(0, Math.sin(frame / 9 - i));
          // heads[i] — уже повёрнутая позиция (совпадает с проекцией подписи)
          return <Pin key={i} pos={heads[i]} accent={accent} grow={grow} pulse={pulse} />;
        })}
      </ThreeCanvas>

      {/* экранные подписи очагов с выносками */}
      <AbsoluteFill style={{ pointerEvents: "none" }}>
        {labels.map((l) => {
          const op = interpolate(frame, [26 + l.i * 7, 42 + l.i * 7], [0, 1], {
            extrapolateLeft: "clamp", extrapolateRight: "clamp",
          }) * exit;
          const dir = l.flip ? -1 : 1;
          const stubX = l.px + dir * 16;                 // горизонтальный вынос
          const dy = l.ly - l.py;
          return (
            <React.Fragment key={l.i}>
              {/* L-выноска: вертикаль от пина к строке + горизонтальный вынос */}
              {Math.abs(dy) > 3 && (
                <div style={{
                  position: "absolute", left: l.px - 1, top: Math.min(l.py, l.ly),
                  width: 2, height: Math.abs(dy), background: accent, opacity: 0.6 * op,
                }} />
              )}
              <div style={{
                position: "absolute", top: l.ly - 1,
                left: dir > 0 ? l.px : stubX, width: 16, height: 2,
                background: accent, opacity: 0.75 * op, boxShadow: `0 0 8px ${accent}`,
              }} />
              <div style={{
                position: "absolute", top: l.ly - 15, opacity: op,
                left: dir > 0 ? stubX + 8 : undefined,
                right: dir < 0 ? width - stubX + 8 : undefined,
                fontFamily: fontFamily("oswald"), color: "#f4f1ea", fontSize: 30, fontWeight: 700,
                letterSpacing: 2, textTransform: "uppercase", whiteSpace: "nowrap",
                textShadow: "0 2px 14px rgba(0,0,0,0.95)",
              }}>{l.label}</div>
            </React.Fragment>
          );
        })}
      </AbsoluteFill>

      {title && (
        <AbsoluteFill style={{ pointerEvents: "none", justifyContent: "flex-start", alignItems: "center", paddingTop: 84 }}>
          <div style={{ opacity: titleOp * exit, fontFamily: fontFamily("oswald"), color: "#f4f1ea", fontSize: 58, fontWeight: 800, letterSpacing: 4, textTransform: "uppercase", textShadow: "0 6px 30px rgba(0,0,0,0.95)" }}>
            {title}
          </div>
        </AbsoluteFill>
      )}
    </AbsoluteFill>
  );
};
