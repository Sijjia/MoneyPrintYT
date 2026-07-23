import React from "react";
import { AbsoluteFill, Easing, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { PALETTE, fontFamily } from "./theme";

// Граф связей: узлы (люди/организации) вспыхивают, между ними прочерчиваются линии —
// структура секты / кто с кем связан. Координаты узлов в % экрана; hot — главный узел.
export type GNode = { label?: string; x: number; y: number; hot?: boolean };
export type NetworkProps = {
  nodes?: GNode[];
  edges?: number[][];
  title?: string;
  accent?: string;
  // опц. кадр появления узла i (для синхрона с закадром); иначе 8+i*7
  nodeStart?: number[];
  titleStart?: number; // кадр появления заголовка
};

export const NetworkGraph: React.FC<NetworkProps> = ({ nodes = [], edges = [], title = "", accent = PALETTE.red, nodeStart, titleStart = 0 }) => {
  const frame = useCurrentFrame();
  const { durationInFrames, width, height } = useVideoConfig();
  const exit = interpolate(frame, [durationInFrames - 20, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });
  const drift = Math.sin(frame / 70) * 8;
  const pos = (n: GNode) => ({ x: (n.x / 100) * width + drift, y: (n.y / 100) * height });
  const startOf = (i: number) => (nodeStart && nodeStart[i] != null ? nodeStart[i] : 8 + i * 7);

  return (
    <AbsoluteFill style={{ background: "#05070c", opacity: exit, overflow: "hidden", fontFamily: fontFamily("oswald") }}>
      <AbsoluteFill style={{ background: "radial-gradient(circle at 50% 46%, rgba(217,40,40,0.08), rgba(0,0,0,0) 60%)" }} />

      <svg width={width} height={height} style={{ position: "absolute", inset: 0 }}>
        {edges.map(([a, b], i) => {
          if (!nodes[a] || !nodes[b]) return null;
          const pa = pos(nodes[a]);
          const pb = pos(nodes[b]);
          // ребро тянется, как только появился дальний узел
          const d = Math.max(startOf(a), startOf(b)) + 4;
          const p = interpolate(frame, [d, d + 18], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
          const x2 = pa.x + (pb.x - pa.x) * p;
          const y2 = pa.y + (pb.y - pa.y) * p;
          return <line key={i} x1={pa.x} y1={pa.y} x2={x2} y2={y2} stroke={accent} strokeWidth={2} opacity={0.5 * p} style={{ filter: `drop-shadow(0 0 4px ${accent}88)` }} />;
        })}
      </svg>

      {nodes.map((n, i) => {
        const p = pos(n);
        const d = startOf(i);
        const ap = interpolate(frame, [d, d + 12], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.back(1.5)) });
        const r = n.hot ? 32 : 18;
        const pulse = n.hot ? 1 + 0.14 * Math.sin(frame / 8) : 1;
        return (
          <div key={i} style={{ position: "absolute", left: p.x, top: p.y, transform: "translate(-50%,-50%)", opacity: ap }}>
            <div style={{ width: r * 2 * pulse, height: r * 2 * pulse, borderRadius: "50%", background: n.hot ? accent : "#16233b", border: `3px solid ${accent}`, boxShadow: n.hot ? `0 0 26px ${accent}` : `0 0 10px ${accent}55`, transform: `scale(${ap})` }} />
            {n.label && (
              <div style={{ position: "absolute", left: "50%", top: r * pulse + 10, transform: "translateX(-50%)", color: PALETTE.cream, fontSize: n.hot ? 32 : 26, fontWeight: n.hot ? 800 : 600, letterSpacing: 1, whiteSpace: "nowrap", textTransform: "uppercase", textShadow: "0 2px 8px #000" }}>{n.label}</div>
            )}
          </div>
        );
      })}

      {title && (
        <div style={{ position: "absolute", top: 78, width: "100%", textAlign: "center", color: PALETTE.cream, fontSize: 48, fontWeight: 800, letterSpacing: 5, textTransform: "uppercase", textShadow: "0 4px 20px #000", opacity: interpolate(frame, [titleStart, titleStart + 16], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) }}>{title}</div>
      )}
    </AbsoluteFill>
  );
};
