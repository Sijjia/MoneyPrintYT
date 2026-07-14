import React from "react";
import {
  AbsoluteFill,
  Easing,
  Img,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { PALETTE, fontFamily, FontName } from "./theme";
import { Censored } from "./censor";

// Блок в мировой плоскости.
export type SceneBlock = {
  id: string;
  kind: "stat" | "headline";
  x: number;
  y: number;
  value?: string;
  label?: string;
  suffix?: string;
  text?: string;
  sub?: string;
};

// Остановка камеры: на какой блок смотрим, зум, сколько кадров едем и держим.
export type SceneShot = {
  focus: string; // id блока
  zoom: number;
  move: number; // кадров на переезд к этой остановке
  hold: number; // кадров выдержки
};

export type SceneProps = {
  blocks: SceneBlock[];
  shots: SceneShot[];
  bgImage?: string | null;
  accent?: string;
  textColor?: string;
  font?: FontName;
};

const lerp = (a: number, b: number, t: number) => a + (b - a) * t;

const BlockView: React.FC<{
  b: SceneBlock;
  revealF: number;
  accent: string;
  textColor: string;
  frame: number;
}> = ({ b, revealF, accent, textColor, frame }) => {
  const o = interpolate(frame, [revealF, revealF + 16], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const y = interpolate(frame, [revealF, revealF + 20], [24, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });

  const wrap: React.CSSProperties = {
    position: "absolute",
    left: b.x,
    top: b.y,
    transform: `translate(-50%,-50%) translateY(${y}px)`,
    textAlign: "center",
    opacity: o,
  };

  if (b.kind === "headline") {
    return (
      <div style={{ ...wrap }}>
        <div
          style={{
            color: accent,
            fontSize: 72,
            fontWeight: 800,
            letterSpacing: 6,
            textTransform: "uppercase",
            whiteSpace: "nowrap",
            textShadow: "0 6px 30px rgba(0,0,0,0.9)",
          }}
        >
          {b.text || ""}
        </div>
        {b.sub && (
          <div style={{ color: textColor, fontSize: 38, fontWeight: 600, letterSpacing: 3, marginTop: 14, textTransform: "uppercase" }}>
            {b.sub}
          </div>
        )}
      </div>
    );
  }

  // stat
  const target = parseInt((b.value || "").replace(/\D/g, ""), 10);
  const hasNum = !Number.isNaN(target);
  const ct = interpolate(frame, [revealF, revealF + 55], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });
  const shown = hasNum ? Math.round(target * ct).toLocaleString("ru-RU") : b.value;
  const lineW = interpolate(frame, [revealF + 10, revealF + 40], [0, 300], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return (
    <div style={{ ...wrap }}>
      <div style={{ color: textColor, fontSize: 250, fontWeight: 800, lineHeight: 0.9, letterSpacing: -5, textShadow: "0 16px 60px rgba(0,0,0,0.85)" }}>
        {shown}
        <span style={{ color: accent }}>{b.suffix || ""}</span>
      </div>
      <div style={{ height: 4, width: lineW, background: accent, margin: "18px auto 16px", borderRadius: 2, boxShadow: `0 0 16px ${accent}` }} />
      <Censored
        text={b.label || ""}
        style={{ color: textColor, fontSize: 46, fontWeight: 600, letterSpacing: 3, textTransform: "uppercase", display: "inline-block" }}
      />
    </div>
  );
};

// Обобщённая кино-сцена: камера ведёт зрителя по блокам согласно shots.
// Длительность = сумма (move+hold) + хвост (задаётся durationInFrames).
export const Scene: React.FC<SceneProps> = ({
  blocks,
  shots,
  bgImage = null,
  accent = PALETTE.red,
  textColor = PALETTE.cream,
  font = "oswald",
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  const byId = Object.fromEntries(blocks.map((b) => [b.id, b]));
  const focusOf = (id: string) => byId[id] || { x: 1200, y: 600 };

  // окна остановок
  let t = 0;
  const wins = shots.map((s) => {
    const start = t;
    const moveEnd = start + s.move;
    t += s.move + s.hold;
    return { ...s, start, moveEnd, end: t };
  });

  // камера в текущем кадре
  const idx = Math.max(0, wins.findIndex((w) => frame < w.end));
  const cur = wins[idx === -1 ? wins.length - 1 : idx] || wins[wins.length - 1];
  const ci = wins.indexOf(cur);
  const prev = ci > 0 ? wins[ci - 1] : cur;
  const pf = focusOf(prev.focus);
  const cf = focusOf(cur.focus);
  const p = interpolate(frame, [cur.start, Math.max(cur.start + 1, cur.moveEnd)], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.inOut(Easing.cubic),
  });
  const camX = lerp(pf.x, cf.x, p);
  const camY = lerp(pf.y, cf.y, p);
  const zoom = lerp(prev.zoom, cur.zoom, p);

  const tx = 960 - camX * zoom + Math.cos(frame / 52) * 7;
  const ty = 540 - camY * zoom + Math.sin(frame / 44) * 6;

  // кадр появления блока = старт первой остановки, что на него смотрит
  const revealOf = (id: string) => {
    const w = wins.find((x) => x.focus === id);
    return w ? w.start : 0;
  };

  const bgScale = interpolate(frame, [0, durationInFrames], [1.32, 1.14]);
  const exit = interpolate(frame, [durationInFrames - 24, durationInFrames], [1, 0], {
    extrapolateLeft: "clamp",
  });

  return (
    <AbsoluteFill style={{ fontFamily: fontFamily(font), opacity: exit, background: "#05070c", overflow: "hidden" }}>
      {bgImage && (
        <AbsoluteFill style={{ transform: `scale(${bgScale})` }}>
          <Img src={staticFile(bgImage)} style={{ width: "100%", height: "100%", objectFit: "cover", filter: "brightness(0.4) grayscale(0.4)" }} />
        </AbsoluteFill>
      )}
      <AbsoluteFill style={{ background: "radial-gradient(circle at 50% 50%, rgba(0,0,0,0.5) 0%, rgba(0,0,0,0.4) 45%, rgba(0,0,0,0.78) 100%)" }} />

      <AbsoluteFill style={{ perspective: 1700, overflow: "hidden" }}>
        <div
          style={{
            position: "absolute",
            left: 0,
            top: 0,
            transformStyle: "preserve-3d",
            transform: `translate(${tx}px, ${ty}px) scale(${zoom})`,
            transformOrigin: "0 0",
          }}
        >
          {blocks.map((b) => (
            <BlockView key={b.id} b={b} revealF={revealOf(b.id)} accent={accent} textColor={textColor} frame={frame} />
          ))}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
