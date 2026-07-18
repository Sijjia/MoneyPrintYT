import React from "react";
import { AbsoluteFill, Easing, interpolate, useCurrentFrame } from "remotion";
import { PALETTE, fontFamily } from "./theme";

// Цельное анимационное ВСТУПЛЕНИЕ на 3D-камере: образы (не текст) расставлены в
// пространстве по вертикали, камера ПЛАВНО СПУСКАЕТСЯ через них — кино-полёт,
// а не нарезка слайдов. Ложится на смысл: «чем глубже спускаемся, тем больше террор».

const lerp = (a: number, b: number, t: number) => a + (b - a) * t;
const lerpCol = (a: number[], b: number[], t: number) =>
  `rgb(${a.map((v, i) => Math.round(v + (b[i] - v) * t)).join(",")})`;

// силуэт человека, центр в (0,0)
const Figure: React.FC<{ s?: number; fill: string }> = ({ s = 1, fill }) => (
  <g transform={`scale(${s})`}>
    <circle cx="0" cy="-46" r="16" fill={fill} />
    <path d="M-24 34 C-24 2 -12 -14 0 -14 C12 -14 24 2 24 34 Z" fill={fill} />
  </g>
);

const NODE = 900; // размер бокса метафоры в мире
const Box: React.FC<{ x: number; y: number; children: React.ReactNode }> = ({ x, y, children }) => (
  <div style={{ position: "absolute", left: x, top: y, width: NODE, height: NODE, marginLeft: -NODE / 2, marginTop: -NODE / 2 }}>
    <svg width={NODE} height={NODE} viewBox={`${-NODE / 2} ${-NODE / 2} ${NODE} ${NODE}`}>{children}</svg>
  </div>
);

const flamePath = "M0 0 C-16 -34 14 -52 4 -96 C24 -66 30 -40 20 -14 C18 -6 10 0 0 0 Z";

// ── ГОЛОД ──
const Starve: React.FC<{ lf: number; accent: string }> = ({ lf, accent }) => {
  const w = interpolate(lf, [8, 62], [1, 0.6], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.inOut(Easing.cubic) });
  const sink = interpolate(lf, [8, 62], [0, 60], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const fade = interpolate(lf, [8, 62], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const fill = lerpCol([232, 226, 214], [78, 62, 58], fade);
  const bowl = interpolate(lf, [12, 28], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <g>
      <g transform={`translate(-120 ${sink})`}><Figure s={3.2 * w} fill={fill} /></g>
      <g opacity={bowl} transform="translate(150 70)">
        <path d="M-110 0 C-110 84 110 84 110 0 Z" fill="none" stroke="rgba(230,226,214,0.55)" strokeWidth="9" />
        <ellipse cx="0" cy="0" rx="110" ry="26" fill="none" stroke="rgba(230,226,214,0.55)" strokeWidth="9" />
      </g>
    </g>
  );
};

// ── КЛИНОК ──
const Blade: React.FC<{ lf: number; accent: string }> = ({ lf, accent }) => {
  const swipe = interpolate(lf, [8, 20], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.in(Easing.cubic) });
  const fall = interpolate(lf, [24, 60], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.in(Easing.cubic) });
  const rot = fall * 26, drop = fall * 130;
  const fill = lerpCol([232, 226, 214], [150, 26, 26], interpolate(lf, [24, 50], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }));
  const x2 = interpolate(swipe, [0, 1], [-360, 360]);
  const y2 = interpolate(swipe, [0, 1], [300, -300]);
  return (
    <g>
      <g transform={`rotate(${rot}) translate(0 ${drop})`}>
        <Figure s={3.6} fill={fill} />
        {lf >= 20 && <line x1={-140} y1={140} x2={140} y2={-100} stroke={accent} strokeWidth="8" strokeLinecap="round" opacity={Math.min(1, (lf - 20) / 6)} />}
      </g>
      {swipe < 1 && <line x1={-360} y1={300} x2={x2} y2={y2} stroke={accent} strokeWidth="10" strokeLinecap="round" style={{ filter: `drop-shadow(0 0 14px ${accent})` }} />}
    </g>
  );
};

// ── ОГОНЬ ──
const Burn: React.FC<{ lf: number; accent: string }> = ({ lf, accent }) => {
  const rise = interpolate(lf, [4, 50], [0.15, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
  const char = interpolate(lf, [14, 60], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const fill = lerpCol([236, 228, 214], [150, 40, 26], char);
  const N = 15;
  return (
    <g>
      <ellipse cx="0" cy="-40" rx={220 * rise} ry={280 * rise} fill={accent} opacity={0.14 * rise} style={{ filter: "blur(34px)" }} />
      <Figure s={3.7} fill={fill} />
      <g transform="translate(0 150)">
        {Array.from({ length: N }).map((_, i) => {
          const bx = (i - (N - 1) / 2) * 34;
          const flick = 0.7 + 0.5 * Math.sin(lf / 2.4 + i * 1.7);
          const h = rise * (2.8 + 1.4 * flick) * (1 - Math.abs(bx) / 300);
          const sway = Math.sin(lf / 4 + i) * 8;
          const col = i % 3 === 0 ? "#ffcc33" : i % 3 === 1 ? "#ff6a1a" : accent;
          return <path key={i} d={flamePath} transform={`translate(${bx + sway} 0) scale(${2.2 + 0.6 * flick} ${Math.max(0.1, h)})`} fill={col} opacity={0.4 + 0.28 * flick} style={{ filter: `drop-shadow(0 0 14px ${accent}aa)` }} />;
        })}
      </g>
    </g>
  );
};

// ── КРЕСТ ──
const Cross: React.FC<{ lf: number; accent: string }> = ({ lf, accent }) => {
  const draw = interpolate(lf, [4, 38], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
  const crack = interpolate(lf, [44, 66], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const red = interpolate(lf, [48, 72], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const col = lerpCol([244, 241, 234], [217, 40, 40], red);
  return (
    <g style={{ filter: `drop-shadow(0 0 ${18 * red}px ${accent})` }}>
      <line x1="0" y1="-320" x2="0" y2="360" stroke={col} strokeWidth="30" strokeLinecap="round" strokeDasharray={700} strokeDashoffset={700 * (1 - draw)} />
      <line x1="-190" y1="-120" x2="190" y2="-120" stroke={col} strokeWidth="30" strokeLinecap="round" strokeDasharray={400} strokeDashoffset={400 * (1 - Math.max(0, draw * 1.4 - 0.4))} />
      <polyline points="-14,-300 30,-90 -30,90 40,260 -10,380" fill="none" stroke={accent} strokeWidth={5} strokeDasharray={1100} strokeDashoffset={1100 * (1 - crack)} opacity={crack} />
    </g>
  );
};

// пыль в 3D-мире — камера пролетает сквозь неё, даёт глубину и «спуск в темноту»
const Dust: React.FC<{ accent: string }> = ({ accent }) => {
  const frame = useCurrentFrame();
  return (
    <>
      {Array.from({ length: 320 }).map((_, i) => {
        const x = (i * 137) % 2100 - 50;
        const y = (i * 331) % 10400 - 100;
        const size = 2 + (i % 4);
        const tw = 0.25 + 0.35 * (0.5 + 0.5 * Math.sin(frame / 18 + i));
        return <div key={i} style={{ position: "absolute", left: x, top: y, width: size, height: size, borderRadius: "50%", background: i % 6 === 0 ? accent : "#dfe4ee", opacity: tw * 0.32, filter: "blur(0.5px)" }} />;
      })}
    </>
  );
};

// ── ВРЕМЯ: песочные часы, песок пересыпается (не в прошлом — сейчас) ──
const Hourglass: React.FC<{ lf: number; accent: string }> = ({ lf, accent }) => {
  const ap = interpolate(lf, [4, 20], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const drain = interpolate(lf, [10, 70], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.inOut(Easing.cubic) });
  const st = "rgba(230,226,214,0.7)";
  return (
    <g opacity={ap}>
      <path d="M-150 -220 L150 -220 L20 0 L150 220 L-150 220 L-20 0 Z" fill="none" stroke={st} strokeWidth="10" />
      {/* верхний песок убывает */}
      <path d={`M-130 -200 L130 -200 L${18 + 100 * drain} ${-40 - 60 * (1 - drain)} L${-18 - 100 * drain} ${-40 - 60 * (1 - drain)} Z`} fill={accent} opacity={0.85 * (1 - drain)} />
      {/* нижний растёт */}
      <path d={`M-${20 + 120 * drain} 200 L${20 + 120 * drain} 200 L18 ${40 + 60 * (1 - drain)} L-18 ${40 + 60 * (1 - drain)} Z`} fill={accent} opacity={0.85 * drain} />
      {/* струйка */}
      {drain > 0.02 && drain < 0.98 && <rect x="-3" y="-40" width="6" height="80" fill={accent} />}
    </g>
  );
};

// ── ГЛОБУС: круг с сеткой, 4 региона загораются красным ──
const GlobeFlat: React.FC<{ lf: number; accent: string }> = ({ lf, accent }) => {
  const draw = interpolate(lf, [4, 30], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const R = 280;
  const pins = [[-150, -120], [120, -60], [-90, 150], [170, 90]];
  return (
    <g>
      <circle cx="0" cy="0" r={R} fill="none" stroke="rgba(120,150,200,0.35)" strokeWidth="3" opacity={draw} />
      {[-160, -80, 0, 80, 160].map((yy, i) => <ellipse key={i} cx="0" cy={yy} rx={Math.sqrt(Math.max(0, R * R - yy * yy))} ry={22} fill="none" stroke="rgba(120,150,200,0.25)" strokeWidth="2" opacity={draw} />)}
      {[-140, 0, 140].map((xx, i) => <ellipse key={i} cx={xx} cy="0" rx={30} ry={R * Math.sqrt(Math.max(0, 1 - (xx / R) ** 2))} fill="none" stroke="rgba(120,150,200,0.22)" strokeWidth="2" opacity={draw} />)}
      {pins.map(([px, py], i) => {
        const on = interpolate(lf, [30 + i * 12, 42 + i * 12], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.back(2)) });
        const pulse = 1 + 0.4 * Math.max(0, Math.sin(lf / 7 - i));
        return <g key={i}><circle cx={px} cy={py} r={16 * pulse} fill={accent} opacity={0.25 * on} /><circle cx={px} cy={py} r={9 * on} fill={accent} style={{ filter: `drop-shadow(0 0 10px ${accent})` }} /></g>;
      })}
    </g>
  );
};

// ── АЙСБЕРГ: всплывает из тьмы, малая вершина / огромная масса; 3 иконки-улики ──
const Iceberg: React.FC<{ lf: number; accent: string }> = ({ lf, accent }) => {
  const rise = interpolate(lf, [6, 44], [140, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
  const line = "rgba(150,180,220,0.5)";
  // иконки-улики появляются позже (приговоры/показания/фото) — как штампы
  const ic = (i: number) => interpolate(lf, [150 + i * 40, 168 + i * 40], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.back(2)) });
  return (
    <g transform={`translate(0 ${rise})`}>
      <line x1="-420" y1="-60" x2="420" y2="-60" stroke="rgba(120,150,200,0.3)" strokeWidth="2" strokeDasharray="10 10" />
      <path d="M-70 -60 L-20 -170 L40 -170 L80 -60 Z" fill="rgba(200,220,245,0.9)" />
      <path d="M-190 -60 L-70 -60 L80 -60 L230 -60 L120 240 L-30 380 L-150 200 Z" fill="rgba(90,120,160,0.55)" stroke={line} strokeWidth="2" />
      {/* улики: молоток / документ / фото (иконки, без текста) */}
      <g opacity={ic(0)} transform="translate(-340 40)"><rect x="-30" y="14" width="60" height="16" rx="4" fill={accent} /><rect x="-8" y="-34" width="16" height="52" rx="4" fill={accent} transform="rotate(-35)" /></g>
      <g opacity={ic(1)} transform="translate(360 -10)"><rect x="-34" y="-42" width="68" height="84" rx="6" fill="none" stroke={accent} strokeWidth="6" /><line x1="-20" y1="-20" x2="20" y2="-20" stroke={accent} strokeWidth="5" /><line x1="-20" y1="0" x2="20" y2="0" stroke={accent} strokeWidth="5" /><line x1="-20" y1="20" x2="8" y2="20" stroke={accent} strokeWidth="5" /></g>
      <g opacity={ic(2)} transform="translate(300 220)"><rect x="-40" y="-30" width="80" height="60" rx="6" fill="none" stroke={accent} strokeWidth="6" /><circle cx="-16" cy="-8" r="8" fill={accent} /><path d="M-40 30 L-6 -2 L14 18 L26 8 L40 24 L40 30 Z" fill={accent} /></g>
    </g>
  );
};

// ── ВЕРА⟶ТЕРРОР: крест снизу превращается в пламя ──
const CrossToFire: React.FC<{ lf: number; accent: string }> = ({ lf, accent }) => {
  const morph = interpolate(lf, [20, 70], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.inOut(Easing.cubic) });
  const N = 11;
  return (
    <g>
      {/* верх креста остаётся */}
      <line x1="0" y1="-320" x2="0" y2={-40 - 200 * morph} stroke={lerpCol([244, 241, 234], [217, 40, 40], morph)} strokeWidth="30" strokeLinecap="round" />
      <line x1="-190" y1="-120" x2="190" y2="-120" stroke={lerpCol([244, 241, 234], [217, 40, 40], morph)} strokeWidth="30" strokeLinecap="round" opacity={1 - 0.4 * morph} />
      {/* низ превращается в пламя */}
      <g transform="translate(0 40)">
        {Array.from({ length: N }).map((_, i) => {
          const bx = (i - (N - 1) / 2) * 30;
          const flick = 0.7 + 0.5 * Math.sin(lf / 2.4 + i * 1.7);
          const h = morph * (2.6 + 1.3 * flick) * (1 - Math.abs(bx) / 220);
          const col = i % 3 === 0 ? "#ffcc33" : i % 3 === 1 ? "#ff6a1a" : accent;
          return <path key={i} d={flamePath} transform={`translate(${bx + Math.sin(lf / 4 + i) * 8} ${300}) scale(${2 + 0.6 * flick} ${Math.max(0.1, h)})`} fill={col} opacity={(0.4 + 0.28 * flick) * morph} />;
        })}
      </g>
    </g>
  );
};

// ── ГЛАЗ: раскрывается, красная радужка (невозможно развидеть) ──
const Eye: React.FC<{ lf: number; accent: string }> = ({ lf, accent }) => {
  const open = interpolate(lf, [6, 40], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
  const iris = interpolate(lf, [30, 55], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const h = 150 * open;
  return (
    <g>
      <path d={`M-300 0 Q 0 ${-h} 300 0 Q 0 ${h} -300 0 Z`} fill="#0a0d14" stroke="rgba(230,226,214,0.8)" strokeWidth="6" />
      <g style={{ clipPath: "ellipse(300px 150px at 50% 50%)" }}>
        <circle cx="0" cy="0" r={90 * iris} fill={accent} opacity={0.85} style={{ filter: `drop-shadow(0 0 20px ${accent})` }} />
        <circle cx="0" cy="0" r={42 * iris} fill="#0a0d14" />
      </g>
    </g>
  );
};

// позиции образов в мире (спуск вниз) + кадр «прибытия» камеры
const NODES = [
  { key: "starve", x: 960, y: 540, at: 14, ry: 5, C: Starve },
  { key: "blade", x: 1440, y: 1520, at: 76, ry: -7, C: Blade },
  { key: "burn", x: 560, y: 2560, at: 142, ry: 7, C: Burn },
  { key: "cross", x: 1080, y: 3620, at: 250, ry: 0, C: Cross },
  { key: "hour", x: 700, y: 4760, at: 470, ry: 6, C: Hourglass },
  { key: "globe", x: 1160, y: 5900, at: 680, ry: -6, C: GlobeFlat },
  { key: "iceberg", x: 860, y: 7160, at: 900, ry: 4, C: Iceberg },
  { key: "morph", x: 1180, y: 8560, at: 1380, ry: -5, C: CrossToFire },
  { key: "eye", x: 960, y: 9640, at: 1540, ry: 0, C: Eye },
];

export const IntroSequence: React.FC<{ accent?: string }> = ({ accent = PALETTE.red }) => {
  const frame = useCurrentFrame();
  const ts = NODES.map((n) => n.at);
  const camX = interpolate(frame, ts, NODES.map((n) => n.x), { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.inOut(Easing.cubic) });
  const camY = interpolate(frame, ts, NODES.map((n) => n.y), { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.inOut(Easing.cubic) });
  const rotY = interpolate(frame, ts, NODES.map((n) => n.ry), { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.inOut(Easing.cubic) });
  // лёгкий зум-пульс на прибытии + постоянный наклон вниз (спуск)
  const zoom = 1.12 + 0.06 * Math.sin(frame / 30);
  const rotX = 7;
  const driftX = Math.cos(frame / 52) * 9;
  const driftY = Math.sin(frame / 44) * 7;
  const world =
    `translate(${960 + driftX}px, ${540 + driftY}px) ` +
    `rotateX(${rotX}deg) rotateY(${rotY}deg) scale(${zoom}) ` +
    `translate(${-camX}px, ${-camY}px)`;

  return (
    <AbsoluteFill style={{ background: "#04060c", fontFamily: fontFamily("oswald"), overflow: "hidden" }}>
      <AbsoluteFill style={{ perspective: 1700, overflow: "hidden" }}>
        <div style={{ position: "absolute", left: 0, top: 0, transformStyle: "preserve-3d", transform: world, transformOrigin: "0 0" }}>
          <Dust accent={accent} />
          {NODES.map((n) => {
            const lf = frame - (n.at - 20);
            const N = n.C;
            return (
              <Box key={n.key} x={n.x} y={n.y}>
                <N lf={lf} accent={accent} />
              </Box>
            );
          })}
        </div>
      </AbsoluteFill>
      <AbsoluteFill style={{ background: "radial-gradient(circle at 50% 50%, rgba(0,0,0,0) 42%, rgba(0,0,0,0.8) 100%)", pointerEvents: "none" }} />
    </AbsoluteFill>
  );
};
