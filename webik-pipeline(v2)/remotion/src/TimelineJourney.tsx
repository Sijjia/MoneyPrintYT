import React from "react";
import { AbsoluteFill, Easing, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { PALETTE, fontFamily } from "./theme";

// Путь через историю: камера едет вдоль светящейся линии времени, годы/события
// вырастают по мере проезда. Не статичные блоки, а движение сквозь хронологию.
export type TLEvent = { year: string | number; label: string };
export type TimelineProps = { events?: TLEvent[]; accent?: string; title?: string };

const GAP = 760;

export const TimelineJourney: React.FC<TimelineProps> = ({ events = [], accent = PALETTE.red, title = "" }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const n = Math.max(1, events.length);
  const xs = events.map((_, i) => i * GAP);
  const margin = 26;
  const span = Math.max(1, durationInFrames - 64);
  const tArr = events.map((_, i) => margin + span * (i / Math.max(1, n - 1)));
  const camX = n > 1
    ? interpolate(frame, tArr, xs, { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.inOut(Easing.cubic) })
    : 0;

  const exit = interpolate(frame, [durationInFrames - 20, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });
  const totalW = (n - 1) * GAP;
  // прогресс заливки линии (доехали докуда)
  const fillW = interpolate(camX, [0, Math.max(1, totalW)], [0, totalW], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ fontFamily: fontFamily("oswald"), background: "#05070c", opacity: exit, overflow: "hidden" }}>
      <AbsoluteFill style={{ background: "radial-gradient(circle at 50% 50%, rgba(217,40,40,0.08) 0%, rgba(0,0,0,0) 60%)" }} />
      {title && (
        <div style={{ position: "absolute", top: 90, width: "100%", textAlign: "center", color: PALETTE.cream, fontSize: 44, fontWeight: 800, letterSpacing: 6, textTransform: "uppercase", opacity: interpolate(frame, [6, 22], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) }}>
          {title}
        </div>
      )}
      {/* мир таймлайна, сдвинут так, что текущая точка — в центре экрана */}
      <AbsoluteFill>
        <div style={{ position: "absolute", left: 960 - camX, top: 540 }}>
          {/* базовая линия */}
          <div style={{ position: "absolute", left: -400, top: -2, width: totalW + 800, height: 4, background: "rgba(255,255,255,0.14)" }} />
          {/* пройденная (светящаяся) часть */}
          <div style={{ position: "absolute", left: 0, top: -3, width: fillW, height: 6, background: accent, boxShadow: `0 0 16px ${accent}`, borderRadius: 3 }} />

          {events.map((e, i) => {
            const rev = interpolate(frame, [tArr[i] - 16, tArr[i] + 4], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
            const passed = frame >= tArr[i] - 4;
            const up = i % 2 === 0;
            const pulse = 1 + 0.4 * Math.max(0, Math.sin((frame - tArr[i]) / 6)) * (Math.abs(frame - tArr[i]) < 20 ? 1 : 0);
            return (
              <div key={i} style={{ position: "absolute", left: xs[i], top: 0 }}>
                {/* узел */}
                <div style={{ position: "absolute", left: -13, top: -13, width: 26, height: 26, borderRadius: "50%", background: passed ? accent : "#1a2233", border: `3px solid ${passed ? accent : "rgba(255,255,255,0.3)"}`, boxShadow: passed ? `0 0 ${18 * pulse}px ${accent}` : "none", transform: `scale(${0.6 + 0.4 * rev})` }} />
                {/* год + событие (сверху/снизу поочерёдно) */}
                <div style={{ position: "absolute", left: "50%", top: up ? -110 : 60, transform: `translate(-50%, ${(up ? 24 : -24) * (1 - rev)}px)`, textAlign: "center", opacity: rev, width: 340 }}>
                  <div style={{ color: accent, fontSize: 68, fontWeight: 800, lineHeight: 1, textShadow: "0 6px 24px rgba(0,0,0,0.9)" }}>{e.year}</div>
                  <div style={{ color: PALETTE.cream, fontSize: 34, fontWeight: 600, letterSpacing: 2, textTransform: "uppercase", marginTop: 8, whiteSpace: "nowrap" }}>{e.label}</div>
                </div>
              </div>
            );
          })}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
