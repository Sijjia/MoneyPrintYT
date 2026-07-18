import React from "react";
import { AbsoluteFill, Easing, interpolate, OffthreadVideo, Sequence, staticFile, useCurrentFrame } from "remotion";
import { PALETTE, fontFamily } from "./theme";

// Кино-интро на РЕАЛЬНЫХ кадрах + грейд (Айдар: вектор = клипарт, нужно кино).
// Тёмный сток под каждый бит, единый грейд (зерно/красный тинт/виньетка), плавные
// диссолвы + Ken-Burns; вектор глобус/айсберг/улики поверх — только графичные биты.

const FPS = 30;

// один клип: грейд + медленный зум + кросс-диссолв по краям
const Clip: React.FC<{ src: string; dur: number; z0?: number; z1?: number }> = ({ src, dur, z0 = 1.06, z1 = 1.18 }) => {
  const f = useCurrentFrame();
  const op = Math.min(
    interpolate(f, [0, 14], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
    interpolate(f, [dur - 16, dur], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })
  );
  const scale = interpolate(f, [0, dur], [z0, z1]);
  return (
    <AbsoluteFill style={{ opacity: op }}>
      <AbsoluteFill style={{ transform: `scale(${scale})` }}>
        <OffthreadVideo src={staticFile(`intro/${src}`)} muted style={{ width: "100%", height: "100%", objectFit: "cover", filter: "grayscale(0.55) contrast(1.22) brightness(0.62) saturate(0.8)" }} />
      </AbsoluteFill>
      {/* красный тинт */}
      <AbsoluteFill style={{ background: "linear-gradient(180deg, rgba(140,20,20,0.22), rgba(20,4,4,0.5))", mixBlendMode: "multiply" }} />
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

// клипы по битам (кадр начала, длина; лёгкий overlap для диссолва)
const CLIPS = [
  { src: "figure.mp4", at: 0, dur: 120 },
  { src: "embers.mp4", at: 105, dur: 130 },
  { src: "candle.mp4", at: 220, dur: 230 },
  { src: "clouds.mp4", at: 435, dur: 230 },
  { src: "smoke.mp4", at: 650, dur: 250 },
  { src: "water.mp4", at: 885, dur: 470 },
  { src: "fire.mp4", at: 1340, dur: 190 },
  { src: "eye.mp4", at: 1515, dur: 120 },
];

export const IntroFootage: React.FC<{ accent?: string }> = ({ accent = PALETTE.red }) => {
  return (
    <AbsoluteFill style={{ background: "#04060c", fontFamily: fontFamily("oswald") }}>
      {CLIPS.map((c, i) => (
        <Sequence key={i} from={c.at} durationInFrames={c.dur}>
          <Clip src={c.src} dur={c.dur} />
        </Sequence>
      ))}
      {/* графичные оверлеи */}
      <Sequence from={650} durationInFrames={250}><GlobeOverlay accent={accent} /></Sequence>
      <Sequence from={885} durationInFrames={470}><IcebergOverlay accent={accent} /></Sequence>
      <Grade />
    </AbsoluteFill>
  );
};
