import React from "react";
import { AbsoluteFill, Img, staticFile, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { fontFamily } from "./theme";
import { mspring, enterUp } from "./anim";

export type EnumItem = { img?: string; label: string; sub?: string };
export type EnumShowcaseProps = {
  kicker?: string;
  title?: string;
  items?: EnumItem[];      // 2-4 карточки (картинка + подпись)
  accent?: string;
  caption?: string;
  durationInFrames?: number;
};

// Красивое ПЕРЕЧИСЛЕНИЕ: карточки с реальными фото + подписи, поочерёдный пружинный вход.
// Для «Куркума, ним, ашваганда…» и подобных списков — вместо «тупого футажа».
export const EnumShowcase: React.FC<EnumShowcaseProps> = ({
  kicker = "АЮРВЕДА",
  title = "ТЫСЯЧЕЛЕТНИЕ ЗНАНИЯ О РАСТЕНИЯХ",
  items = [
    { label: "КУРКУМА", sub: "противовоспалительное" },
    { label: "НИМ", sub: "антисептик" },
    { label: "АШВАГАНДА", sub: "адаптоген" },
  ],
  accent = "#e0a52a",
  caption = "",
  durationInFrames,
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames: dif } = useVideoConfig();
  const dur = durationInFrames ?? dif;
  const exit = interpolate(frame, [dur - 16, dur], [1, 0], { extrapolateLeft: "clamp" });
  const n = items.length;
  const cardW = Math.min(430, Math.floor((1620 - (n - 1) * 40) / n));

  return (
    <AbsoluteFill style={{ background: "linear-gradient(180deg,#1a1509 0%,#120e07 55%,#080604 100%)", opacity: exit, fontFamily: fontFamily("oswald") }}>
      <AbsoluteFill style={{ background: "radial-gradient(ellipse at 50% 40%, rgba(224,165,42,0.10), transparent 55%)" }} />

      <AbsoluteFill style={{ justifyContent: "flex-start", alignItems: "flex-start", padding: "70px 90px 0" }}>
        {(() => { const k = enterUp(frame, 30, 2, 26); const t = enterUp(frame, 30, 8, 42, { stiffness: 125, damping: 18 }); return (<>
          <div style={{ color: accent, fontSize: 30, fontWeight: 700, letterSpacing: 8, opacity: k.opacity, transform: `translateY(${k.translateY}px)` }}>{kicker}</div>
          <div style={{ color: "#f4ecd6", fontSize: 60, fontWeight: 700, lineHeight: 1.02, maxWidth: 1400, textShadow: "0 6px 30px rgba(0,0,0,0.85)", marginTop: 6, opacity: t.opacity, transform: `translateY(${t.translateY}px)` }}>{title}</div>
        </>); })()}
      </AbsoluteFill>

      {/* карточки */}
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", paddingTop: 60 }}>
        <div style={{ display: "flex", gap: 40 }}>
          {items.map((it, i) => {
            const s = mspring(frame, 30, { stiffness: 150, damping: 15, delay: 22 + i * 12 });
            const on = Math.min(1, s);
            return (
              <div key={i} style={{ width: cardW, opacity: on, transform: `translateY(${(1 - s) * 40}px) scale(${0.92 + s * 0.08})` }}>
                <div style={{ width: cardW, height: cardW * 0.72, borderRadius: 14, overflow: "hidden", border: `2px solid ${accent}55`,
                  boxShadow: "0 20px 60px rgba(0,0,0,0.6)", background: "#0d0a06", position: "relative" }}>
                  {it.img ? (
                    <Img src={staticFile(it.img)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
                  ) : (
                    <AbsoluteFill style={{ background: `radial-gradient(circle at 50% 40%, ${accent}33, transparent 70%)` }} />
                  )}
                  <AbsoluteFill style={{ boxShadow: "inset 0 -60px 80px rgba(0,0,0,0.7)", pointerEvents: "none" }} />
                </div>
                <div style={{ marginTop: 16, color: "#f6ecd4", fontSize: 40, fontWeight: 800, letterSpacing: 1 }}>{it.label}</div>
                {it.sub && <div style={{ color: accent, fontSize: 24, fontWeight: 600, marginTop: 2 }}>{it.sub}</div>}
              </div>
            );
          })}
        </div>
      </AbsoluteFill>

      {caption && (
        <div style={{ position: "absolute", left: 0, right: 0, bottom: 54, textAlign: "center", padding: "0 200px",
          color: "#ecdfc6", fontSize: 32, fontWeight: 500, textShadow: "0 4px 22px rgba(0,0,0,0.95)", fontFamily: fontFamily("montserrat"),
          opacity: interpolate(frame, [46, 60], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) * exit }}>{caption}</div>
      )}
      <AbsoluteFill style={{ boxShadow: "inset 0 0 300px rgba(0,0,0,0.78)", pointerEvents: "none" }} />
    </AbsoluteFill>
  );
};
