import React from "react";
import { AbsoluteFill, Easing, interpolate, OffthreadVideo, Sequence, staticFile, useCurrentFrame } from "remotion";
import { PALETTE, fontFamily } from "./theme";
import { IntroWorldMap } from "./IntroWorldMap";

// Кино-интро на РЕАЛЬНЫХ кадрах + грейд (Айдар: вектор = клипарт, нужно кино).
// Тёмный сток под каждый бит, единый грейд (зерно/красный тинт/виньетка), плавные
// диссолвы + Ken-Burns; вектор глобус/айсберг/улики поверх — только графичные биты.

const FPS = 30;

// один клип: грейд + медленный зум + кросс-диссолв по краям
const WARM = "linear-gradient(180deg, rgba(140,20,20,0.22), rgba(20,4,4,0.5))";
const COLD = "linear-gradient(180deg, rgba(60,90,130,0.20), rgba(6,12,22,0.55))";

const Clip: React.FC<{ src: string; dur: number; z0?: number; z1?: number; grade?: string; tint?: string; from?: number }> = ({
  src, dur, z0 = 1.06, z1 = 1.18, from = 0,
  grade = "grayscale(0.45) contrast(1.14) brightness(0.78) saturate(0.85)",
  tint = WARM,
}) => {
  const f = useCurrentFrame();
  const op = Math.min(
    interpolate(f, [0, 14], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
    interpolate(f, [dur - 16, dur], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })
  );
  const scale = interpolate(f, [0, dur], [z0, z1]);
  return (
    <AbsoluteFill style={{ opacity: op }}>
      <AbsoluteFill style={{ transform: `scale(${scale})` }}>
        <OffthreadVideo src={staticFile(`intro/${src}`)} muted startFrom={from} style={{ width: "100%", height: "100%", objectFit: "cover", filter: grade }} />
      </AbsoluteFill>
      <AbsoluteFill style={{ background: tint, mixBlendMode: "multiply" }} />
    </AbsoluteFill>
  );
};

// плёночное зерно (анимированный шум) + виньетка — общий грейд поверх всего
const Grade: React.FC = () => {
  const f = useCurrentFrame();
  return (
    <>
      <AbsoluteFill style={{ background: "radial-gradient(circle at 50% 48%, rgba(0,0,0,0) 42%, rgba(0,0,0,0.82) 100%)", pointerEvents: "none" }} />
      <svg width="1920" height="1080" style={{ position: "absolute", inset: 0, opacity: 0.08, mixBlendMode: "overlay", pointerEvents: "none" }}>
        <filter id="grain"><feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed={f % 50} stitchTiles="stitch" /></filter>
        <rect width="1920" height="1080" filter="url(#grain)" />
      </svg>
    </>
  );
};

// ── световые блики (light leaks): мягкие тёплые пятна дрейфуют, screen ──
const LightLeaks: React.FC<{ accent: string }> = ({ accent }) => {
  const f = useCurrentFrame();
  const leaks = [
    { c: accent, x: 12 + Math.sin(f / 90) * 6, y: 20, r: 60, o: 0.14 + 0.08 * Math.sin(f / 40) },
    { c: "#ff8a3a", x: 86 + Math.cos(f / 110) * 5, y: 78, r: 55, o: 0.1 + 0.06 * Math.sin(f / 55 + 2) },
    { c: accent, x: 50, y: 8 + Math.sin(f / 70) * 4, r: 70, o: 0.06 + 0.05 * Math.sin(f / 33 + 1) },
  ];
  return (
    <AbsoluteFill style={{ mixBlendMode: "screen", pointerEvents: "none" }}>
      {leaks.map((l, i) => (
        <div key={i} style={{ position: "absolute", left: `${l.x}%`, top: `${l.y}%`, width: `${l.r}%`, height: `${l.r}%`, transform: "translate(-50%,-50%)", background: `radial-gradient(circle, ${l.c} 0%, rgba(0,0,0,0) 68%)`, opacity: Math.max(0, l.o), filter: "blur(30px)" }} />
      ))}
    </AbsoluteFill>
  );
};

// ── парящие угольки/пыль (реалистичные, тёплые, поднимаются) ──
const Embers: React.FC<{ accent: string }> = ({ accent }) => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill style={{ pointerEvents: "none", mixBlendMode: "screen" }}>
      {Array.from({ length: 40 }).map((_, i) => {
        const speed = 0.05 + (i % 7) * 0.02;
        const x = (i * 173) % 100;
        const drift = Math.sin(f / 30 + i) * 2.5;
        const y = ((i * 61) % 120 - f * speed) % 120;
        const yy = (y + 120) % 120;
        const size = 1.5 + (i % 4);
        const tw = 0.3 + 0.5 * (0.5 + 0.5 * Math.sin(f / 12 + i));
        return <div key={i} style={{ position: "absolute", left: `${(x + drift + 100) % 100}%`, top: `${yy - 10}%`, width: size, height: size, borderRadius: "50%", background: i % 4 === 0 ? "#ffb26b" : accent, opacity: tw * 0.5, filter: "blur(1px)", boxShadow: `0 0 ${size * 2}px ${accent}` }} />;
      })}
    </AbsoluteFill>
  );
};

// ── акценты-переходы: короткая вспышка на стыках битов ──
const FlashCuts: React.FC<{ cuts: number[]; accent: string }> = ({ cuts, accent }) => {
  const f = useCurrentFrame();
  const op = cuts.reduce((a, c) => a + Math.max(0, 1 - Math.abs(f - c) / 4), 0);
  return <AbsoluteFill style={{ background: accent, opacity: Math.min(0.35, op * 0.35), mixBlendMode: "screen", pointerEvents: "none" }} />;
};

// ── ПРЕМИУМ-ГРАФИКА: символы разных вер загораются на «во имя веры» ──
const SYMBOLS = [
  // крест
  "M0 -30 L0 30 M-17 -11 L17 -11",
  // полумесяц
  "M9 -26 A26 26 0 1 0 9 26 A20 20 0 1 1 9 -26 Z",
  // звезда Давида
  "M0 -28 L24 14 L-24 14 Z M0 28 L24 -14 L-24 -14 Z",
  // колесо дхармы
  "M0 -26 A26 26 0 1 0 0 26 A26 26 0 1 0 0 -26 M0 -26 L0 26 M-26 0 L26 0 M-18 -18 L18 18 M-18 18 L18 -18",
];

// по два символа слева и справа от свечи — центр занят пламенем
const SYMBOL_POS = [
  [300, 400],
  [560, 610],
  [1360, 610],
  [1620, 400],
];

const FaithSymbols: React.FC<{ accent: string; dur: number }> = ({ accent, dur }) => {
  const f = useCurrentFrame();
  const out = interpolate(f, [dur - 26, dur - 4], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ pointerEvents: "none", opacity: out }}>
      <svg width="1920" height="1080">
        {SYMBOLS.map((d, i) => {
          const t0 = 12 + i * 17;
          const on = interpolate(f, [t0, t0 + 16], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
          const rise = interpolate(f, [t0, t0 + 22], [16, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
          const breathe = 0.82 + 0.18 * Math.sin(f / 16 + i);
          const [x, y] = SYMBOL_POS[i];
          const halo = interpolate(f, [t0, t0 + 30], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
          return (
            <g key={i} transform={`translate(${x} ${y + rise}) scale(1.7)`} opacity={on * (0.6 + 0.4 * breathe)}>
              <circle r={46} fill="none" stroke={accent} strokeWidth={0.8} opacity={0.3 * halo} />
              <path d={d} fill="none" stroke="rgba(240,246,255,0.95)" strokeWidth={2.2} strokeLinecap="round" strokeLinejoin="round" style={{ filter: `drop-shadow(0 0 11px ${accent})` }} />
            </g>
          );
        })}
      </svg>
    </AbsoluteFill>
  );
};

// ── ПРЕМИУМ-ГРАФИКА: улики — приговоры судов / показания / фотографии с мест ──
const EvidenceCards: React.FC<{ accent: string; dur: number }> = ({ accent, dur }) => {
  const f = useCurrentFrame();
  const out = interpolate(f, [dur - 30, dur - 6], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const CARDS = [24, 66, 101]; // «приговоры судов» / «показания свидетелей» / «фотографии»
  return (
    <AbsoluteFill style={{ pointerEvents: "none", opacity: out }}>
      <svg width="1920" height="1080">
        {CARDS.map((t0, i) => {
          const on = interpolate(f, [t0, t0 + 15], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
          const sc = interpolate(f, [t0, t0 + 22], [0.9, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
          const drift = Math.sin((f - t0) / 40 + i) * 4;
          const cx = 480 + i * 480;
          const cy = 540 + drift;
          const W = 300, H = 210;
          return (
            <g key={i} opacity={on} transform={`translate(${cx} ${cy}) scale(${sc})`}>
              <rect x={-W / 2} y={-H / 2} width={W} height={H} fill="rgba(8,12,20,0.55)" stroke="rgba(215,232,255,0.35)" strokeWidth={1.2} />
              {/* уголки-скобки */}
              {[[-1, -1], [1, -1], [-1, 1], [1, 1]].map(([sx, sy], k) => (
                <path
                  key={k}
                  d={`M${(sx * W) / 2 - sx * 26} ${(sy * H) / 2} L${(sx * W) / 2} ${(sy * H) / 2} L${(sx * W) / 2} ${(sy * H) / 2 - sy * 26}`}
                  fill="none"
                  stroke={accent}
                  strokeWidth={2}
                  style={{ filter: `drop-shadow(0 0 6px ${accent})` }}
                />
              ))}
              {i === 0 && (
                // приговор: строки документа + печать
                <g>
                  {[0, 1, 2, 3, 4].map((r) => {
                    const w = [150, 190, 120, 200, 90][r];
                    const dr = interpolate(f, [t0 + 8 + r * 5, t0 + 20 + r * 5], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
                    return <line key={r} x1={-115} y1={-58 + r * 22} x2={-115 + w * dr} y2={-58 + r * 22} stroke="rgba(215,232,255,0.5)" strokeWidth={2} />;
                  })}
                  <circle cx={82} cy={56} r={26} fill="none" stroke={accent} strokeWidth={2} opacity={interpolate(f, [t0 + 30, t0 + 42], [0, 0.9], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })} />
                  <circle cx={82} cy={56} r={18} fill="none" stroke={accent} strokeWidth={1} opacity={interpolate(f, [t0 + 34, t0 + 46], [0, 0.7], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })} />
                </g>
              )}
              {i === 1 && (
                // показания: звуковая волна
                <g>
                  {Array.from({ length: 21 }).map((_, b) => {
                    const h = 12 + 52 * Math.abs(Math.sin(b * 1.7 + f / 7));
                    const dr = interpolate(f, [t0 + 6 + b * 2, t0 + 16 + b * 2], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
                    return <line key={b} x1={-120 + b * 12} y1={-h / 2} x2={-120 + b * 12} y2={h / 2} stroke="rgba(215,232,255,0.6)" strokeWidth={2.5} opacity={dr} strokeLinecap="round" />;
                  })}
                </g>
              )}
              {i === 2 && (
                // фотография с места: перекрестье и метки кадра
                <g opacity={interpolate(f, [t0 + 6, t0 + 20], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })}>
                  <line x1={-70} y1={0} x2={70} y2={0} stroke="rgba(215,232,255,0.4)" strokeWidth={1} />
                  <line x1={0} y1={-58} x2={0} y2={58} stroke="rgba(215,232,255,0.4)" strokeWidth={1} />
                  <circle cx={0} cy={0} r={40} fill="none" stroke={accent} strokeWidth={1.4} opacity={0.75} />
                  <circle cx={0} cy={0} r={6 + 30 * (((f - t0) % 40) / 40)} fill="none" stroke={accent} strokeWidth={1} opacity={0.5 * (1 - ((f - t0) % 40) / 40)} />
                  {[0, 1, 2, 3, 4, 5].map((s) => (
                    <line key={s} x1={-120 + s * 48} y1={-88} x2={-120 + s * 48} y2={-78} stroke="rgba(215,232,255,0.35)" strokeWidth={1.5} />
                  ))}
                </g>
              )}
            </g>
          );
        })}
      </svg>
    </AbsoluteFill>
  );
};

// ── ПРЕМИУМ-ГРАФИКА: тонкая шкала глубины поверх реального айсберга ──
const IcebergHUD: React.FC<{ accent: string }> = ({ accent }) => {
  const f = useCurrentFrame();
  const op = Math.min(interpolate(f, [14, 40], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }), interpolate(f, [100, 124], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }));
  const line = interpolate(f, [24, 60], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
  const lineY = 360;
  const ticks = [0, 1, 2, 3, 4, 5];
  return (
    <AbsoluteFill style={{ opacity: op, pointerEvents: "none" }}>
      <svg width="1920" height="1080">
        {/* ватерлиния */}
        <line x1={200} y1={lineY} x2={200 + 1520 * line} y2={lineY} stroke="rgba(230,240,255,0.7)" strokeWidth={1.5} strokeDasharray="2 8" />
        <circle cx={200} cy={lineY} r={4} fill={accent} opacity={line} />
        {/* вертикальная шкала глубины справа */}
        <line x1={1680} y1={lineY} x2={1680} y2={lineY + 560 * line} stroke="rgba(230,240,255,0.5)" strokeWidth={1.5} />
        {ticks.map((t, i) => {
          const yy = lineY + t * 112;
          const tap = interpolate(f, [40 + i * 8, 52 + i * 8], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
          return <g key={t} opacity={tap}><line x1={1668} y1={yy} x2={1680} y2={yy} stroke="rgba(230,240,255,0.6)" strokeWidth={1.5} /><text x={1660} y={yy + 5} textAnchor="end" fill="rgba(230,240,255,0.55)" fontSize={20} fontFamily="Oswald, sans-serif">{t * 200}</text></g>;
        })}
      </svg>
    </AbsoluteFill>
  );
};

// ── ПРЕМИУМ-ГРАФИКА: уровни уходят вглубь — на «чем глубже мы будем спускаться» ──
const IcebergLevels: React.FC<{ accent: string; dur: number }> = ({ accent, dur }) => {
  const f = useCurrentFrame();
  const out = interpolate(f, [dur - 24, dur - 2], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ pointerEvents: "none", opacity: out }}>
      <svg width="1920" height="1080">
        {[0, 1, 2, 3].map((i) => {
          const yy = 470 + i * 150;
          const t0 = 22 + i * 32;
          const g = interpolate(f, [t0, t0 + 44], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
          const w = 380 + i * 220; // глубже — шире
          const pulse = 0.5 + 0.5 * Math.max(0, Math.sin(f / 9 - i * 1.4));
          return (
            <g key={i} opacity={g}>
              <line x1={230} y1={yy} x2={230 + w * g} y2={yy} stroke="rgba(215,232,255,0.45)" strokeWidth={1.5} strokeDasharray="3 10" />
              <circle cx={230} cy={yy} r={3.5} fill="rgba(230,240,255,0.85)" />
              <circle cx={230 + w * g} cy={yy} r={4 + 2 * pulse} fill={accent} opacity={0.5 + 0.35 * pulse} style={{ filter: `drop-shadow(0 0 8px ${accent})` }} />
            </g>
          );
        })}
      </svg>
    </AbsoluteFill>
  );
};

// ── вектор ГЛОБУС (сетка + 4 пина) поверх тёмного кадра ──
const GlobeOverlay: React.FC<{ accent: string }> = ({ accent }) => {
  const f = useCurrentFrame();
  const draw = interpolate(f, [6, 34], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const op = Math.min(draw, interpolate(f, [180, 210], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }));
  const R = 250, cx = 960, cy = 540;
  const pins = [[-140, -110], [110, -55], [-80, 140], [155, 80]];
  return (
    <svg width="1920" height="1080" style={{ position: "absolute", inset: 0, opacity: op }}>
      <circle cx={cx} cy={cy} r={R} fill="none" stroke="rgba(150,175,215,0.4)" strokeWidth="2" />
      {[-150, -75, 0, 75, 150].map((yy, i) => <ellipse key={i} cx={cx} cy={cy + yy} rx={Math.sqrt(Math.max(0, R * R - yy * yy))} ry={20} fill="none" stroke="rgba(150,175,215,0.28)" strokeWidth="1.5" />)}
      {[-130, 0, 130].map((xx, i) => <ellipse key={i} cx={cx + xx} cy={cy} rx={26} ry={R * Math.sqrt(Math.max(0, 1 - (xx / R) ** 2))} fill="none" stroke="rgba(150,175,215,0.25)" strokeWidth="1.5" />)}
      {pins.map(([px, py], i) => {
        const on = interpolate(f, [40 + i * 14, 54 + i * 14], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.back(2)) });
        const pulse = 1 + 0.4 * Math.max(0, Math.sin(f / 7 - i));
        return <g key={i}><circle cx={cx + px} cy={cy + py} r={15 * pulse} fill={accent} opacity={0.25 * on} /><circle cx={cx + px} cy={cy + py} r={8 * on} fill={accent} style={{ filter: `drop-shadow(0 0 10px ${accent})` }} /></g>;
      })}
    </svg>
  );
};

// ── вектор АЙСБЕРГ + улики поверх тёмной воды ──
const IcebergOverlay: React.FC<{ accent: string }> = ({ accent }) => {
  const f = useCurrentFrame();
  const rise = interpolate(f, [8, 50], [180, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
  const op = Math.min(interpolate(f, [8, 30], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }), interpolate(f, [360, 400], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }));
  const ic = (i: number) => interpolate(f, [150 + i * 45, 168 + i * 45], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.back(2)) });
  return (
    <svg width="1920" height="1080" viewBox="0 0 1920 1080" style={{ position: "absolute", inset: 0, opacity: op }}>
      <g transform={`translate(960 ${380 + rise})`}>
        <line x1="-460" y1="0" x2="460" y2="0" stroke="rgba(150,180,220,0.35)" strokeWidth="2" strokeDasharray="12 12" />
        <path d="M-70 0 L-24 -120 L44 -120 L86 0 Z" fill="rgba(210,228,250,0.85)" />
        <path d="M-200 0 L-70 0 L86 0 L240 0 L130 320 L-24 470 L-160 270 Z" fill="rgba(70,100,140,0.5)" stroke="rgba(150,180,220,0.4)" strokeWidth="2" />
        <g opacity={ic(0)} transform="translate(-360 120)"><rect x="-30" y="14" width="60" height="16" rx="4" fill={accent} /><rect x="-8" y="-34" width="16" height="52" rx="4" fill={accent} transform="rotate(-35)" /></g>
        <g opacity={ic(1)} transform="translate(390 70)"><rect x="-34" y="-42" width="68" height="84" rx="6" fill="none" stroke={accent} strokeWidth="6" /><line x1="-20" y1="-20" x2="20" y2="-20" stroke={accent} strokeWidth="5" /><line x1="-20" y1="0" x2="20" y2="0" stroke={accent} strokeWidth="5" /><line x1="-20" y1="20" x2="8" y2="20" stroke={accent} strokeWidth="5" /></g>
        <g opacity={ic(2)} transform="translate(340 300)"><rect x="-40" y="-30" width="80" height="60" rx="6" fill="none" stroke={accent} strokeWidth="6" /><circle cx="-16" cy="-8" r="8" fill={accent} /><path d="M-40 30 L-6 -2 L14 18 L26 8 L40 24 L40 30 Z" fill={accent} /></g>
      </g>
    </svg>
  );
};

// клипы по битам — ВСЁ реальные кадры (айсберг/Земля тоже настоящие, не вектор).
// лёгкий overlap соседних для кросс-диссолва.
// Биты синхронизированы по словам из assets/alignment.json (кадр = слово * 30 - 14,
// чтобы клип успел проявиться ровно к произнесению якоря).
const CLIPS = [
  // «морят голодом собственных детей / режут соседей» (4.82 / 6.96)
  { src: "figure.mp4", at: 0, dur: 264, grade: "grayscale(0.5) contrast(1.2) brightness(0.9) saturate(0.8)" },
  { src: "embers.mp4", at: 248, dur: 99 },   // «сжигают друг друга заживо» 8.74
  // «во имя веры» 11.92 — свеча в исходнике зажигается на ~130 кадре: смещаем, чтобы
  // вспышка зажигания пришлась ровно на слово
  { src: "candle.mp4", at: 331, dur: 140, from: 104 },
  // «остался в средневековье» 15.62 → «в наше время» 26.26
  { src: "clouds.mp4", at: 455, dur: 341, grade: "grayscale(0.55) contrast(1.22) brightness(1.15) saturate(0.7)", tint: COLD },
  // 780–972 — карта мира (графика, без стока): «в России, Африке, Латинской Америке, в Европе»
  // «в этом айсберге» 32.32 — общий план лагуны + ватерлиния и шкала
  { src: "iceberg.mp4", at: 956, dur: 126, grade: "grayscale(0.62) contrast(1.32) brightness(0.66) saturate(0.6)", tint: COLD },
  // «о которых почти никто не знает / нет фантастики» 35.6–39.6 — погружение в темноту
  { src: "water.mp4", at: 1066, dur: 140, grade: "grayscale(0.55) contrast(1.3) brightness(0.8) saturate(0.7)", tint: COLD },
  // «только приговоры судов, показания свидетелей и фотографии с мест» 40.1–44.2 — улики
  { src: "smoke.mp4", at: 1190, dur: 163, from: 40, grade: "grayscale(0.7) contrast(1.25) brightness(0.6) saturate(0.6)", tint: COLD },
  // «чем глубже мы будем спускаться» 45.02 — крупный айсберг + уровни вглубь
  { src: "iceberg2.mp4", at: 1337, dur: 165, grade: "grayscale(0.6) contrast(1.3) brightness(0.7) saturate(0.62)", tint: COLD },
  { src: "fire.mp4", at: 1486, dur: 100 },   // «тем больше — на террор» 50.56
  { src: "eye.mp4", at: 1570, dur: 95, grade: "grayscale(0.55) contrast(1.25) brightness(0.7) saturate(0.75)" }, // «невозможно развидеть» 53.94
];

export const IntroFootage: React.FC<{ accent?: string }> = ({ accent = PALETTE.red }) => {
  const cuts = CLIPS.slice(1).map((c) => c.at + 8); // стыки диссолвов
  return (
    <AbsoluteFill style={{ background: "#04060c", fontFamily: fontFamily("oswald") }}>
      {CLIPS.map((c, i) => (
        <Sequence key={i} from={c.at} durationInFrames={c.dur}>
          <Clip src={c.src} dur={c.dur} grade={c.grade} tint={c.tint} from={c.from} />
        </Sequence>
      ))}
      {/* премиум-графика на уместных битах */}
      <Sequence from={780} durationInFrames={192}><IntroWorldMap accent={accent} dur={192} /></Sequence>
      <Sequence from={331} durationInFrames={140}><FaithSymbols accent={accent} dur={140} /></Sequence>
      <Sequence from={956} durationInFrames={126}><IcebergHUD accent={accent} /></Sequence>
      <Sequence from={1190} durationInFrames={163}><EvidenceCards accent={accent} dur={163} /></Sequence>
      <Sequence from={1337} durationInFrames={165}><IcebergLevels accent={accent} dur={165} /></Sequence>
      <LightLeaks accent={accent} />
      <Embers accent={accent} />
      <FlashCuts cuts={cuts} accent={accent} />
      <Grade />
    </AbsoluteFill>
  );
};
