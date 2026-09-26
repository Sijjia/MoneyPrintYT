import React from "react";
import { AbsoluteFill, Img, staticFile, interpolate, spring, useCurrentFrame, useVideoConfig, Easing } from "remotion";
import { fontFamily } from "./theme";

type Companion = { src: string; x: number; y: number; w: number; from: number; to: number };

export type MascotProps = {
  mouth?: number[];                       // липсинк: на кадр 0=закрыт / 1=открыт (из громкости голоса)
  position?: "left" | "center" | "right";
  scale?: number;                          // доля высоты кадра (0.9 = 90%)
  bust?: boolean;                          // «по пояс»: крупно снизу, сверху место под графику
  jitter?: number;                         // сила покачивания (0 = статичный)
  flip?: boolean;                          // отзеркалить (смотрит в другую сторону)
  companions?: Companion[];                // маленькие картинки-улики (fade-in по opacity)
  caption?: string;                        // подпись снизу (опц.)
  // РЯДОМ с маскотом (на противоположной стороне) — один из:
  stat?: { value: number; prefix?: string; suffix?: string; label?: string; sub?: string };  // счётчик-цифра
  bars?: { label: string; value: number }[];                                                  // бар-чарт
  portrait?: { photo: string; name: string; role?: string; quote: string };                   // портрет+цитата
  accent?: string;
  bg?: string;
  durationInFrames?: number;
};

const rnd = (i: number, s = 1) => {
  const x = Math.sin(i * 12.9898 + s * 78.233) * 43758.5453;
  return x - Math.floor(x);
};

export const Mascot: React.FC<MascotProps> = ({
  mouth = [], position = "left", scale = 0.9, bust = false, jitter = 1, flip = false,
  companions = [], caption = "", stat, bars, portrait, accent = "#e2080d", bg = "#08080b",
}) => {
  const frame = useCurrentFrame();
  const { width, height, durationInFrames, fps } = useVideoConfig();

  // вход (пружиной сбоку) + выход
  const inn = spring({ frame, fps, config: { damping: 14, stiffness: 90 } });
  const exit = interpolate(frame, [durationInFrames - 12, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });

  // геометрия маскота (высокий: 1370×3068). bust = крупно снизу (видно ~по пояс)
  const mh = bust ? height * 1.55 * scale : height * scale;
  const mw = mh * (1370 / 3068);
  const cx = position === "left" ? width * 0.20 : position === "right" ? width * 0.80 : width * 0.5;
  const enterFrom = position === "right" ? 120 : position === "center" ? 0 : -120;
  const ex = interpolate(inn, [0, 1], [enterFrom, 0]);

  // «жизнь»: ТОЛЬКО плавное, без дрожи — тихое дыхание + медленное покачивание + лёгкий наклон
  const breathe = 1 + Math.sin(frame / 24) * 0.004;                     // масштаб-дыхание (медленно)
  const bob = Math.sin(frame / 52) * 4 * jitter;                        // медленное вертикальное покачивание
  const sway = Math.sin(frame / 78) * 0.45 * jitter;                    // очень медленный наклон

  const doFlip = flip || position === "right";        // справа — всегда лицом в кадр
  const open = (mouth[frame] ?? 0) > 0.5;
  const openOpacity = interpolate(mouth[frame] ?? 0, [0, 1], [0, 1]);   // мягкий блендинг рта

  const left = cx - mw / 2 + ex;
  // bust: опускаем так, чтобы талия была у нижнего края (видно голову+торс)
  const top = bust ? (height - mh * 0.56 + bob) : (height - mh + bob - height * 0.02);

  return (
    <AbsoluteFill style={{ background: bg, fontFamily: fontFamily("oswald"), opacity: exit }}>
      {/* мягкое пятно света под маскотом */}
      <div style={{ position: "absolute", left: cx - mw * 0.4, top: height - mh * 0.28, width: mw * 0.8, height: mh * 0.22,
        background: `radial-gradient(ellipse at center, ${accent}22 0%, transparent 70%)`, filter: "blur(20px)" }} />

      {/* картинки-улики (fade-in по opacity) */}
      {companions.map((c, i) => {
        const op = interpolate(frame, [c.from, c.from + 8, c.to - 8, c.to], [0, 1, 1, 0],
          { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
        const pop = spring({ frame: frame - c.from, fps, config: { damping: 12, stiffness: 140 } });
        const life = Math.max(1, c.to - c.from);
        const prog = interpolate(frame, [c.from, c.to], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
        const kb = 1.0 + prog * 0.12;                       // медленный Ken-Burns зум
        const drift = Math.sin(prog * Math.PI) * (i % 2 ? -8 : 8); // лёгкий дрейф
        return (
          <div key={i} style={{ position: "absolute", left: c.x * width + drift, top: c.y * height, width: c.w,
            transform: `translate(-50%,-50%) scale(${0.92 + pop * 0.08})`, opacity: op,
            borderRadius: 14, overflow: "hidden",
            boxShadow: `0 18px 55px rgba(0,0,0,0.78), 0 0 0 3px ${accent}cc, 0 0 0 8px rgba(0,0,0,0.5)` }}>
            <Img src={staticFile(c.src)} style={{ width: "100%", display: "block",
              transform: `scale(${kb})`, transformOrigin: "50% 45%" }} />
            {/* кино-градиент снизу для читаемости */}
            <div style={{ position: "absolute", inset: 0, background: "linear-gradient(180deg, transparent 55%, rgba(0,0,0,0.35) 100%)" }} />
          </div>
        );
      })}

      {/* маскот: обе картинки стопкой, переключаем рот по громкости. Справа — всегда отзеркал. */}
      <div style={{ position: "absolute", left, top, width: mw, height: mh,
        transform: `rotate(${sway}deg) scale(${breathe})`, transformOrigin: "50% 100%", opacity: inn }}>
        <Img src={staticFile("mascot/closed.png")} style={{ width: "100%", position: "absolute", top: 0, left: 0,
          transform: doFlip ? "scaleX(-1)" : undefined }} />
        <Img src={staticFile("mascot/open.png")} style={{ width: "100%", position: "absolute", top: 0, left: 0,
          transform: doFlip ? "scaleX(-1)" : undefined, opacity: open ? 1 : openOpacity }} />
      </div>

      {/* РЯДОМ (противоположная сторона): счётчик / бары / портрет+цитата */}
      {(stat || bars || portrait) && (() => {
        const SL = width * 0.50, SW = width * 0.44;
        const rev = spring({ frame: frame - 8, fps, config: { damping: 18, stiffness: 90 } });
        if (stat) {
          // ease-out: резко в начале, замедляется к концу (тот самый «ахуенный момент»)
          const prog = interpolate(frame, [8, 8 + Math.round(durationInFrames * 0.42)], [0, 1],
            { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
          const cur = Math.round(prog * stat.value);
          return (
            <div style={{ position: "absolute", left: SL, top: 0, width: SW, height, display: "flex",
              flexDirection: "column", justifyContent: "center", opacity: rev }}>
              <div style={{ color: accent, fontSize: 190, fontWeight: 800, lineHeight: 0.9, letterSpacing: -2,
                textShadow: `0 0 40px ${accent}66` }}>
                {stat.prefix || ""}{cur.toLocaleString("ru-RU")}{stat.suffix || ""}</div>
              <div style={{ color: "#fff", fontSize: 44, fontWeight: 800, letterSpacing: 2, marginTop: 6 }}>{stat.label}</div>
              {stat.sub && <div style={{ color: "#8a8a92", fontSize: 26, fontWeight: 600, marginTop: 4 }}>{stat.sub}</div>}
            </div>
          );
        }
        if (bars) {
          const mx = Math.max(...bars.map((b) => b.value)) || 1;
          return (
            <div style={{ position: "absolute", left: SL, top: 0, width: SW, height, display: "flex",
              flexDirection: "column", justifyContent: "center", gap: 26, paddingRight: 40, opacity: inn }}>
              {bars.map((b, i) => {
                const r = spring({ frame: frame - 10 - i * 6, fps, config: { damping: 16, stiffness: 90 } });
                return (
                  <div key={i}>
                    <div style={{ display: "flex", justifyContent: "space-between", color: "#e6e6ea",
                      fontSize: 28, fontWeight: 700, marginBottom: 6 }}>
                      <span>{b.label}</span><span style={{ color: accent }}>{b.value.toLocaleString("ru-RU")}</span></div>
                    <div style={{ height: 30, background: "#1c1c22", borderRadius: 6, overflow: "hidden" }}>
                      <div style={{ height: "100%", width: `${interpolate(r, [0, 1], [0, (b.value / mx) * 100])}%`,
                        background: `linear-gradient(90deg, ${accent}, ${accent}bb)`, borderRadius: 6 }} /></div>
                  </div>
                );
              })}
            </div>
          );
        }
        // portrait + quote
        const PW = SW * 0.42, PH = PW * 1.22;
        const words = portrait!.quote.split(" ");
        const per = Math.max(1.6, (durationInFrames * 0.5) / Math.max(1, words.length));
        return (
          <div style={{ position: "absolute", left: SL, top: 0, width: SW, height, display: "flex",
            alignItems: "center", gap: 30, opacity: inn }}>
            <div style={{ width: PW, height: PH, flexShrink: 0, borderRadius: 14, overflow: "hidden",
              transform: `translateY(${interpolate(rev, [0, 1], [30, 0])}px)`, opacity: rev,
              boxShadow: `0 20px 55px rgba(0,0,0,0.7), 0 0 0 3px ${accent}` }}>
              <Img src={staticFile(portrait!.photo)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
            </div>
            <div>
              <div style={{ color: accent, fontSize: 90, fontWeight: 800, lineHeight: 0.5, height: 40 }}>“</div>
              <div style={{ color: "#f2f2f4", fontSize: 38, fontWeight: 700, lineHeight: 1.3 }}>
                {words.map((w, i) => {
                  const o = interpolate(frame, [12 + i * per, 12 + i * per + 8], [0.12, 1],
                    { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
                  return <span key={i} style={{ opacity: o }}>{w} </span>;
                })}
              </div>
              <div style={{ color: "#fff", fontSize: 28, fontWeight: 800, letterSpacing: 1, marginTop: 18 }}>
                <span style={{ color: accent }}>— </span>{portrait!.name}</div>
              {portrait!.role && <div style={{ color: "#8a8a92", fontSize: 20, fontWeight: 600 }}>{portrait!.role}</div>}
            </div>
          </div>
        );
      })()}

      {caption && (
        <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: 40, opacity: inn }}>
          <div style={{ color: "#fff", fontSize: 40, fontWeight: 800, letterSpacing: 2, textAlign: "center",
            textShadow: "0 3px 14px rgba(0,0,0,0.8)", maxWidth: "80%" }}>{caption}</div>
        </AbsoluteFill>
      )}
    </AbsoluteFill>
  );
};
