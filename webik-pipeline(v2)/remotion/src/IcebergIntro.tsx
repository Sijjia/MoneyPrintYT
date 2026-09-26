import React from "react";
import {
  AbsoluteFill,
  Easing,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { PALETTE, fontFamily } from "./theme";

export type IcebergIntroProps = {
  title?: string;
  sub?: string;
  accent?: string;
  tags?: string[];        // опц.: имена сабреддитов/феноменов, медленно всплывающие в глубине (Reddit-тема)
  levelWord?: string;     // «УРОВЕНЬ» / «LEVEL»
  levels?: { n: string; t: string }[];   // подписи 4 уровней (n=номер, t=название)
  durationInFrames?: number;              // чтобы длина бралась из props (calculateMetadata)
};

const rnd = (i: number, s = 1) => {
  const x = Math.sin(i * 37.7 + s * 91.3) * 43758.5453;
  return x - Math.floor(x);
};

// Интро: реалистичный айсберг (над/под водой) + 4 уровня в глубине, камера ныряет к красной бездне.
export const IcebergIntro: React.FC<IcebergIntroProps> = ({
  title = "АЙСБЕРГ",
  sub = "СЕВЕРНОЙ КОРЕИ",
  accent = PALETTE.red,
  tags = [],
  levelWord = "УРОВЕНЬ",
  levels: levelsProp,
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  const intro = interpolate(frame, [0, 20], [0, 1], { extrapolateRight: "clamp" });
  const exit = interpolate(frame, [durationInFrames - 18, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });
  // камера медленно опускается (пан вниз по айсбергу к бездне)
  const dive = interpolate(frame, [0, durationInFrames], [0, 520], { easing: Easing.inOut(Easing.cubic) });
  const zoom = interpolate(frame, [0, durationInFrames], [1.0, 1.12]);
  const titleIn = interpolate(frame, [10, 30], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  // рваный силуэт айсберга (над водой)
  const topPts = "700,470 740,300 800,340 850,210 910,300 970,150 1030,290 1090,250 1160,360 1230,300 1300,470";
  // подводная часть
  const botPts = "700,470 1300,470 1250,640 1180,760 1210,900 1120,1030 980,1140 900,1030 830,900 860,760 780,640 700,470";

  const LVL_Y = [640, 800, 960, 1120];
  const DEF_LEVELS = [{ n: "1", t: "ВЕРХУШКА" }, { n: "2", t: "ВОДНАЯ ГЛАДЬ" },
                      { n: "3", t: "ПОГРУЖЕНИЕ" }, { n: "4", t: "БЕЗДНА" }];
  const levels = ((levelsProp && levelsProp.length ? levelsProp : DEF_LEVELS).slice(0, 4)
    ).map((lv, i) => ({ y: LVL_Y[i], n: lv.n, t: lv.t }));
  const _unused_levels = [
    { y: 640, n: "1", t: "ВЕРХУШКА" },
    { y: 800, n: "2", t: "ВОДНАЯ ГЛАДЬ" },
    { y: 960, n: "3", t: "ПОГРУЖЕНИЕ" },
    { y: 1120, n: "4", t: "БЕЗДНА" },
  ];

  return (
    <AbsoluteFill style={{ fontFamily: fontFamily("oswald"), opacity: exit }}>
      {/* небо + вода */}
      <AbsoluteFill style={{ background: "linear-gradient(180deg, #0a1420 0%, #0c1b2a 30%, #0a2030 42%, #071726 55%, #0a0d16 74%, #2a0808 92%, #5a0d0d 100%)" }} />
      {/* звёзды над водой */}
      <AbsoluteFill style={{ opacity: intro }}>
        {Array.from({ length: 40 }).map((_, i) => <div key={i} style={{ position: "absolute", left: `${rnd(i, 1) * 100}%`, top: `${rnd(i, 2) * 30}%`, width: 2, height: 2, borderRadius: "50%", background: "#cfe0ff", opacity: 0.5 }} />)}
      </AbsoluteFill>

      <AbsoluteFill style={{ transform: `translateY(${-dive}px) scale(${zoom})`, opacity: intro }}>
        <svg width={1920} height={1200} viewBox="0 0 1920 1200" style={{ position: "absolute", left: 0, top: 30 }}>
          <defs>
            <linearGradient id="iceTop" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#eaf6ff" /><stop offset="1" stopColor="#a9d4ec" /></linearGradient>
            <linearGradient id="iceBot" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#3f83a8" /><stop offset="0.55" stopColor="#1c4f6e" /><stop offset="1" stopColor="#3a1414" /></linearGradient>
          </defs>
          {/* подводная часть */}
          <polygon points={botPts} fill="url(#iceBot)" opacity="0.92" />
          <polygon points={botPts} fill="none" stroke="#6fb4d6" strokeWidth="2" opacity="0.4" />
          {/* линия воды */}
          <rect x="0" y="468" width="1920" height="6" fill="#bfe4f5" opacity="0.5" />
          {/* верхушка */}
          <polygon points={topPts} fill="url(#iceTop)" />
          <polygon points="800,340 850,210 910,300 850,470 800,340" fill="#ffffff" opacity="0.5" />
        </svg>

        {/* маркеры уровней в глубине */}
        <svg width={1920} height={1200} viewBox="0 0 1920 1200" style={{ position: "absolute", left: 0, top: 30 }}>
          {levels.map((lv, i) => {
            const on = interpolate(frame, [24 + i * 10, 40 + i * 10], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
            return (
              <g key={i} opacity={on}>
                <line x1="1120" y1={lv.y} x2="1560" y2={lv.y} stroke={accent} strokeWidth="2" strokeDasharray="8 6" />
                <circle cx="1120" cy={lv.y} r="10" fill={accent} style={{ filter: `drop-shadow(0 0 8px ${accent})` }} />
                <text x="1580" y={lv.y - 8} fill={PALETTE.cream} fontSize="30" fontWeight="800" style={{ fontFamily: fontFamily("oswald") }}>{levelWord} {lv.n}</text>
                <text x="1580" y={lv.y + 24} fill={accent} fontSize="22" letterSpacing="2" style={{ fontFamily: fontFamily("oswald") }}>{lv.t}</text>
              </g>
            );
          })}
        </svg>

        {/* Reddit-тема: имена сабреддитов/феноменов, тускло всплывают в подводной глубине */}
        {tags.map((tg, i) => {
          // держим имена в теле подводного айсберга и ЛЕВЕЕ маркеров уровней (те начинаются ~x1120)
          const col = i % 2;
          const bx = col ? 940 : 730;
          const by = 560 + (i / Math.max(1, tags.length)) * 570 + rnd(i, 5) * 26;
          const app = interpolate(frame, [30 + i * 7, 60 + i * 7], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
          const fl = Math.sin((frame + i * 20) / 40) * 6;   // лёгкое всплывание
          return (
            <div key={`tg${i}`} style={{ position: "absolute", left: bx + rnd(i, 3) * 40, top: by + fl,
              color: PALETTE.cream, fontSize: 25, fontWeight: 700, letterSpacing: 1, opacity: app * 0.42,
              textShadow: `0 0 12px ${accent}88`, whiteSpace: "nowrap" }}>{tg}</div>
          );
        })}
      </AbsoluteFill>

      {/* дрейф частиц (планктон/пузыри) — «движение медиа» на всю глубину */}
      <AbsoluteFill style={{ opacity: intro * 0.6, pointerEvents: "none" }}>
        {Array.from({ length: 34 }).map((_, i) => {
          const x = rnd(i, 7) * 100;
          const baseY = rnd(i, 8) * 100;
          const rise = (baseY - (frame * (0.6 + rnd(i, 9) * 0.7)) / 10) % 100;
          const y = (rise + 100) % 100;
          const sz = 2 + rnd(i, 10) * 4;
          return <div key={`p${i}`} style={{ position: "absolute", left: `${x}%`, top: `${y}%`, width: sz, height: sz,
            borderRadius: "50%", background: i % 5 === 0 ? accent : "#bfe0f0", opacity: 0.18 + rnd(i, 11) * 0.22,
            filter: "blur(0.5px)" }} />;
        })}
      </AbsoluteFill>

      {/* туман у воды + виньетка */}
      <AbsoluteFill style={{ background: "radial-gradient(ellipse at 50% 44%, rgba(150,200,230,0.14), transparent 40%)", pointerEvents: "none" }} />
      <AbsoluteFill style={{ boxShadow: "inset 0 0 300px rgba(0,0,0,0.7)", pointerEvents: "none" }} />

      {/* заголовок */}
      <AbsoluteFill style={{ justifyContent: "flex-start", alignItems: "flex-start", padding: 90, opacity: titleIn * exit }}>
        <div>
          <div style={{ color: PALETTE.cream, fontSize: 130, fontWeight: 800, lineHeight: 0.9, letterSpacing: 2, textShadow: "0 8px 40px rgba(0,0,0,0.8)" }}>{title}</div>
          <div style={{ color: accent, fontSize: 92, fontWeight: 800, lineHeight: 0.95, letterSpacing: 2, textShadow: `0 0 40px ${accent}` }}>{sub}</div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
