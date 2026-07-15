import React from "react";
import { AbsoluteFill, Easing, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { PALETTE, fontFamily } from "./theme";
import { Censored } from "./censor";

// «X из Y» как ОБРАЗ: сетка фигурок людей, доля filled/total заливается красным
// по ходу речи. Большие числа — представительная сетка (до 240 фигур), маленькие —
// один-в-один. Данность становится визуальной, без «парящих цифр».
export type CrowdProps = {
  total?: number;
  filled?: number;
  label?: string;
  sub?: string;
  accent?: string;
};

const COLS = 24;
const MAXN = 240;

const Figure: React.FC<{ on: boolean; ap: number; accent: string }> = ({ on, ap, accent }) => (
  <svg width="34" height="48" viewBox="0 0 58 82" style={{ opacity: ap, transform: `scale(${0.6 + 0.4 * ap})` }}>
    <circle cx="29" cy="17" r="15" fill={on ? accent : "rgba(255,255,255,0.22)"} />
    <path d="M6 82 C6 52 18 40 29 40 C40 40 52 52 52 82 Z" fill={on ? accent : "rgba(255,255,255,0.22)"} />
  </svg>
);

export const CrowdPictograph: React.FC<CrowdProps> = ({
  total = 100,
  filled = 50,
  label = "",
  sub = "",
  accent = PALETTE.red,
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  const tot = Math.max(1, Math.round(total));
  const fil = Math.max(0, Math.min(tot, Math.round(filled)));
  const frac = fil / tot;
  const N = Math.min(MAXN, tot);
  const nRed = Math.round(N * frac);
  const rows = Math.ceil(N / COLS);

  const ct = interpolate(frame, [12, 74], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });
  const shown = Math.round(fil * ct).toLocaleString("ru-RU");
  const zoom = interpolate(frame, [0, durationInFrames], [1.06, 1.0]);
  const exit = interpolate(frame, [durationInFrames - 20, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });

  return (
    <AbsoluteFill style={{ fontFamily: fontFamily("oswald"), background: "#05070c", opacity: exit, overflow: "hidden" }}>
      <AbsoluteFill style={{ background: "radial-gradient(circle at 50% 46%, rgba(217,40,40,0.10) 0%, rgba(0,0,0,0.0) 55%)" }} />
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", transform: `scale(${zoom})` }}>
        {/* большое число сверху */}
        <div style={{ display: "flex", alignItems: "baseline", gap: 22, marginBottom: 34 }}>
          <span style={{ color: accent, fontSize: 150, fontWeight: 800, lineHeight: 0.9, textShadow: "0 12px 50px rgba(0,0,0,0.8)" }}>{shown}</span>
          <span style={{ color: PALETTE.cream, fontSize: 66, fontWeight: 600, opacity: 0.7 }}>из {tot.toLocaleString("ru-RU")}</span>
        </div>
        {/* сетка фигурок */}
        <div style={{ display: "grid", gridTemplateColumns: `repeat(${COLS}, 40px)`, gap: 6, justifyContent: "center", maxWidth: 1500 }}>
          {Array.from({ length: N }).map((_, i) => {
            const r = Math.floor(i / COLS);
            const delay = 8 + r * 3 + (i % COLS) * 0.6;
            const ap = interpolate(frame, [delay, delay + 12], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
            // краснеют «слева-сверху» по порядку, чуть позже появления
            const redAt = 24 + (i / Math.max(1, nRed)) * 40;
            const isRed = i < nRed && frame >= redAt;
            return <Figure key={i} on={isRed} ap={ap} accent={accent} />;
          })}
        </div>
        {/* подпись */}
        {label && (
          <div style={{ marginTop: 40 }}>
            <Censored text={label} style={{ color: PALETTE.cream, fontSize: 48, fontWeight: 700, letterSpacing: 3, textTransform: "uppercase", display: "inline-block" }} />
          </div>
        )}
        {sub && <div style={{ marginTop: 12, color: accent, fontSize: 28, fontWeight: 600, letterSpacing: 4, textTransform: "uppercase" }}>{sub}</div>}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
