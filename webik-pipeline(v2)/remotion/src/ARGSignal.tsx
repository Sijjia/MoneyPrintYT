import React from "react";
import {
  AbsoluteFill,
  Easing,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
  random,
} from "remotion";
import { fontFamily } from "./theme";

export type ARGSignalProps = {
  mode: "signal" | "decode" | "silence" | "static" | "terminated" | "abandoned";
  caption: string;       // короткая фраза внизу
  code?: string;         // строка «кода»/адреса
  accent?: string;
  lang?: "ru" | "en";    // язык внутренних надписей терминала
};

const L = {
  ru: {
    signal: "INCOMING SIGNAL", decode: "DECODING", silence: "SIGNAL LOST",
    static: "NO RESPONSE", terminated: "TRANSMISSION ENDED", abandoned: "PROJECT ABANDONED",
    progress: "PROGRESS", source: "SOURCE: UNKNOWN", noAnswer: "NO ANSWER",
    connLost: "CONNECTION LOST", lastUpd: "LAST UPDATE: —", recv: "RECEIVING",
  },
  en: {
    signal: "INCOMING SIGNAL", decode: "DECRYPTING", silence: "SIGNAL LOST",
    static: "NO ANSWER", terminated: "TRANSMISSION ENDED", abandoned: "PROJECT ABANDONED",
    progress: "PROGRESS", source: "SOURCE: UNKNOWN", noAnswer: "NO ANSWER",
    connLost: "CONNECTION LOST", lastUpd: "LAST UPDATE: —", recv: "RECEIVING",
  },
} as const;

const MONO = "'Consolas', 'Courier New', monospace";
const GLYPHS = "ABCDEFGHKLMNPRSTVXZ0123456789#%@&$?><=/\\|+*".split("");

// Дешифрующийся текст: символы «схлопываются» из мусора в целевую строку.
const Scramble: React.FC<{ text: string; frame: number; start: number; per: number; style?: React.CSSProperties }> = ({ text, frame, start, per, style }) => {
  const chars = text.split("").map((ch, i) => {
    if (ch === " ") return " ";
    const solved = frame > start + i * per;
    if (solved) return ch;
    const g = GLYPHS[Math.floor(random(`${i}-${Math.floor(frame / 2)}`) * GLYPHS.length)];
    return g;
  });
  return <span style={style}>{chars.join("")}</span>;
};

// Осциллограмма: живая (signal/decode) или плоская (silence).
const Wave: React.FC<{ frame: number; accent: string; alive: number; w: number; h: number }> = ({ frame, accent, alive, w, h }) => {
  const n = 120;
  const pts: string[] = [];
  for (let i = 0; i <= n; i++) {
    const x = (i / n) * w;
    const noise = (random(`w${i}`) - 0.5) * 2;
    const y = h / 2 + alive * (Math.sin(i * 0.35 + frame * 0.3) * (h * 0.3) + noise * h * 0.22 * Math.sin(frame * 0.2 + i));
    pts.push(`${x.toFixed(1)},${y.toFixed(1)}`);
  }
  return (
    <svg width={w} height={h} style={{ display: "block" }}>
      <polyline points={pts.join(" ")} fill="none" stroke={accent} strokeWidth={3} opacity={0.9} />
      <polyline points={pts.join(" ")} fill="none" stroke={accent} strokeWidth={8} opacity={0.18} />
    </svg>
  );
};

export const ARGSignal: React.FC<ARGSignalProps> = ({ mode, caption, code = "", accent, lang = "ru" }) => {
  const frame = useCurrentFrame();
  const { durationInFrames, width, height } = useVideoConfig();
  const tr = L[lang] || L.ru;

  const acc = accent || (mode === "terminated" || mode === "silence" ? "#e23b3b" : mode === "abandoned" ? "#b09256" : "#5f9d84");
  const boot = interpolate(frame, [0, 12], [0, 1], { extrapolateRight: "clamp" });
  const exit = interpolate(frame, [durationInFrames - 12, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });
  const flicker = 0.9 + 0.1 * Math.sin(frame * 1.9) * Math.sin(frame * 0.7);
  const scanY = (frame * 7) % 100;
  const glitchOn = random(`g${Math.floor(frame / 9)}`) > 0.78;
  const glitchX = glitchOn ? (random(`gx${Math.floor(frame / 9)}`) - 0.5) * 24 : 0;

  const alive = mode === "silence" || mode === "static" ? 0.06 : mode === "abandoned" ? 0.25 : 1;
  const staticHeavy = mode === "static" ? 0.5 : mode === "terminated" ? 0.32 : 0.14;

  const header = tr[mode];

  const decodePct = Math.min(99, Math.floor(interpolate(frame, [10, durationInFrames - 20], [4, 99], { extrapolateRight: "clamp" })));
  const codeLine = code || "as://hidden/" + header.toLowerCase().replace(/\s/g, "_");

  // фоновый «код-дождь» столбиками
  const cols = Math.floor(width / 60);
  const rain = Array.from({ length: cols }, (_, c) => {
    const speed = 0.4 + random(`s${c}`) * 1.4;
    const rows = Math.floor(height / 34) + 2;
    const off = (frame * speed + random(`o${c}`) * rows) % rows;
    return { c, off, rows, speed };
  });

  return (
    <AbsoluteFill style={{ background: "#060608", fontFamily: MONO, opacity: exit }}>
      {/* код-дождь */}
      <AbsoluteFill style={{ opacity: 0.16 * boot, transform: `translateX(${glitchX}px)` }}>
        {rain.map(({ c, off, rows }) => (
          <div key={c} style={{ position: "absolute", left: c * 60 + 14, top: 0, color: acc, fontSize: 24, lineHeight: "34px" }}>
            {Array.from({ length: rows }, (_, r) => {
              const d = Math.abs(r - off);
              const op = Math.max(0, 1 - d / 4);
              return (
                <div key={r} style={{ opacity: op, color: r === Math.round(off) ? "#d8fff0" : acc }}>
                  {GLYPHS[Math.floor(random(`r${c}-${r}-${Math.floor(frame / 3)}`) * GLYPHS.length)]}
                </div>
              );
            })}
          </div>
        ))}
      </AbsoluteFill>

      {/* центральная панель */}
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", opacity: boot * flicker }}>
        <div
          style={{
            width: 1400,
            background: "linear-gradient(180deg, rgba(6,10,9,0.86), rgba(4,6,8,0.9))",
            border: `2px solid ${acc}`,
            boxShadow: `0 0 20px ${acc}22, inset 0 0 80px rgba(0,0,0,0.7)`,
            padding: "46px 60px 54px",
            position: "relative",
            transform: `translateX(${glitchX * 0.5}px)`,
          }}
        >
          {/* уголки */}
          {[["left", "top"], ["right", "top"], ["left", "bottom"], ["right", "bottom"]].map(([x, y], i) => (
            <div key={i} style={{ position: "absolute", [x]: 12, [y]: 12, width: 40, height: 40, borderTop: y === "top" ? `3px solid ${acc}` : "none", borderBottom: y === "bottom" ? `3px solid ${acc}` : "none", borderLeft: x === "left" ? `3px solid ${acc}` : "none", borderRight: x === "right" ? `3px solid ${acc}` : "none" }} />
          ))}

          {/* хедер */}
          <div style={{ display: "flex", alignItems: "center", gap: 16, color: acc, fontSize: 30, letterSpacing: 6, fontWeight: 700 }}>
            <span style={{ opacity: Math.sin(frame * 0.5) > 0 ? 1 : 0.25 }}>●</span>
            {header}
            <span style={{ marginLeft: "auto", fontSize: 22, opacity: 0.75, letterSpacing: 3 }}>
              AS//NIGHT · {Math.floor(frame / 30).toString().padStart(2, "0")}:{((frame * 2) % 60).toString().padStart(2, "0")}
            </span>
          </div>

          {/* адрес/код */}
          <div style={{ marginTop: 20, color: "#cdd8d2", fontSize: 34, letterSpacing: 2 }}>
            <span style={{ color: acc }}>&gt; </span>
            <Scramble text={codeLine} frame={frame} start={14} per={1.4} />
            <span style={{ opacity: Math.floor(frame / 8) % 2 ? 1 : 0 }}> ▮</span>
          </div>

          {/* осциллограмма */}
          <div style={{ marginTop: 30, border: `1px solid ${acc}55`, background: "rgba(0,0,0,0.4)", position: "relative", overflow: "hidden" }}>
            <Wave frame={frame} accent={acc} alive={alive} w={1280} h={200} />
            {/* прогресс дешифровки */}
            {mode === "decode" && (
              <div style={{ position: "absolute", left: 0, bottom: 0, height: 6, width: `${decodePct}%`, background: acc, boxShadow: `0 0 5px ${acc}66` }} />
            )}
          </div>

          {/* строка статуса под волной */}
          <div style={{ marginTop: 18, display: "flex", gap: 40, color: acc, fontSize: 24, letterSpacing: 3, opacity: 0.85 }}>
            {mode === "decode" && <span>{tr.progress} {decodePct}%</span>}
            {mode === "signal" && <span>{tr.source}</span>}
            {(mode === "silence" || mode === "static") && <span style={{ color: "#e23b3b" }}>{tr.noAnswer}</span>}
            {mode === "terminated" && <span style={{ color: "#e23b3b" }}>{tr.connLost}</span>}
            {mode === "abandoned" && <span>{tr.lastUpd}</span>}
            <span style={{ marginLeft: "auto" }}>{["◐", "◓", "◑", "◒"][Math.floor(frame / 6) % 4]} {tr.recv}</span>
          </div>

          {/* красная планка-цензура для terminated */}
          {(mode === "terminated" || mode === "abandoned") && (
            <div style={{ position: "absolute", left: 60, right: 60, top: "52%", height: 46, background: mode === "terminated" ? "#e23b3b" : "#00000000", border: mode === "abandoned" ? `2px dashed ${acc}` : "none", transform: `rotate(-1.5deg)`, opacity: interpolate(frame, [16, 26], [0, 0.9], { extrapolateRight: "clamp" }) }} />
          )}
        </div>
      </AbsoluteFill>

      {/* подпись-реплика внизу */}
      <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: 90, opacity: interpolate(frame, [18, 34], [0, 1], { extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) }) * exit }}>
        <div style={{ maxWidth: 1500, textAlign: "center", color: "#f4f1ea", fontFamily: fontFamily("oswald"), fontSize: 50, fontWeight: 600, letterSpacing: 1, textShadow: "0 4px 24px rgba(0,0,0,0.9)", lineHeight: 1.15, borderLeft: `4px solid ${acc}`, borderRight: `4px solid ${acc}`, padding: "6px 34px" }}>
          {caption}
        </div>
      </AbsoluteFill>

      {/* статик-шум */}
      <AbsoluteFill style={{ opacity: staticHeavy * (0.7 + 0.3 * Math.sin(frame)) , mixBlendMode: "screen", pointerEvents: "none" }}>
        <svg width={width} height={height}>
          <filter id="n"><feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed={Math.floor(frame / 2) % 50} /></filter>
          <rect width={width} height={height} filter="url(#n)" opacity="0.5" />
        </svg>
      </AbsoluteFill>

      {/* скан-лайны + бегущая развёртка */}
      <AbsoluteFill style={{ background: "repeating-linear-gradient(0deg, rgba(0,0,0,0.35) 0px, rgba(0,0,0,0.35) 1px, transparent 3px, transparent 5px)", pointerEvents: "none" }} />
      <div style={{ position: "absolute", left: 0, right: 0, top: `${scanY}%`, height: 120, background: `linear-gradient(180deg, transparent, ${acc}12, transparent)`, pointerEvents: "none" }} />
      {/* виньетка */}
      <AbsoluteFill style={{ boxShadow: "inset 0 0 300px rgba(0,0,0,0.95)", pointerEvents: "none" }} />
      {/* глитч-полоса */}
      {glitchOn && (
        <div style={{ position: "absolute", left: 0, right: 0, top: `${random(`gy${Math.floor(frame / 9)}`) * 80 + 10}%`, height: 8 + random(`gh${Math.floor(frame / 9)}`) * 30, background: acc, opacity: 0.25, mixBlendMode: "screen", transform: `translateX(${glitchX * 2}px)` }} />
      )}
    </AbsoluteFill>
  );
};
