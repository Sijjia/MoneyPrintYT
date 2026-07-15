import React from "react";
import { AbsoluteFill, Easing, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { PALETTE, fontFamily } from "./theme";
import { Censored } from "./censor";

// Пропорция как ФИЗИЧЕСКАЯ заливка: сосуд наполняется красным снизу до доли/процента,
// число тикает синхронно. Сама заливка = статистика.
export type ProportionProps = {
  percent?: number;
  label?: string;
  sub?: string;
  accent?: string;
};

const W = 440;
const H = 620;

export const ProportionFill: React.FC<ProportionProps> = ({
  percent = 50,
  label = "",
  sub = "",
  accent = PALETTE.red,
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const pct = Math.max(0, Math.min(100, percent));

  const fillFrac = interpolate(frame, [12, 80], [0, pct / 100], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.inOut(Easing.cubic),
  });
  const shownPct = Math.round(fillFrac * 100);
  const fillH = fillFrac * H;
  const wave = Math.sin(frame / 9) * 7;
  const exit = interpolate(frame, [durationInFrames - 20, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });

  return (
    <AbsoluteFill style={{ fontFamily: fontFamily("oswald"), background: "#05070c", opacity: exit, overflow: "hidden" }}>
      <AbsoluteFill style={{ background: "radial-gradient(circle at 42% 50%, rgba(217,40,40,0.10) 0%, rgba(0,0,0,0) 58%)" }} />
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", gap: 90, flexDirection: "row" }}>
        {/* сосуд */}
        <div style={{ position: "relative", width: W, height: H, borderRadius: 26, border: "3px solid rgba(255,255,255,0.16)", overflow: "hidden", background: "rgba(255,255,255,0.03)", boxShadow: "inset 0 0 60px rgba(0,0,0,0.6)" }}>
          {/* заливка */}
          <div style={{ position: "absolute", left: 0, right: 0, bottom: 0, height: fillH, background: `linear-gradient(180deg, ${accent} 0%, #8f1616 100%)`, boxShadow: `0 0 40px ${accent}aa` }}>
            {/* волна на поверхности */}
            <div style={{ position: "absolute", top: -14 + wave, left: 0, right: 0, height: 28, borderRadius: "50%", background: accent, opacity: 0.85, filter: "blur(1px)" }} />
            <div style={{ position: "absolute", top: -8 - wave, left: 0, right: 0, height: 20, borderRadius: "50%", background: "#b52020", opacity: 0.6 }} />
          </div>
          {/* деления */}
          {[25, 50, 75].map((t) => (
            <div key={t} style={{ position: "absolute", right: 0, bottom: (t / 100) * H, width: 26, height: 2, background: "rgba(255,255,255,0.25)" }} />
          ))}
        </div>
        {/* число + подпись */}
        <div style={{ display: "flex", flexDirection: "column", justifyContent: "center", maxWidth: 720 }}>
          <div style={{ display: "flex", alignItems: "baseline" }}>
            <span style={{ color: accent, fontSize: 260, fontWeight: 800, lineHeight: 0.85, letterSpacing: -6, textShadow: "0 16px 60px rgba(0,0,0,0.8)" }}>{shownPct}</span>
            <span style={{ color: accent, fontSize: 120, fontWeight: 800 }}>%</span>
          </div>
          {label && (
            <div style={{ marginTop: 18 }}>
              <Censored text={label} style={{ color: PALETTE.cream, fontSize: 56, fontWeight: 700, letterSpacing: 2, textTransform: "uppercase", display: "inline-block", lineHeight: 1.1 }} />
            </div>
          )}
          {sub && <div style={{ marginTop: 14, color: PALETTE.cream, opacity: 0.6, fontSize: 30, fontWeight: 500, letterSpacing: 3, textTransform: "uppercase" }}>{sub}</div>}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
