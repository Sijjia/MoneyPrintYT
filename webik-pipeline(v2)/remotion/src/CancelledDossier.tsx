import React from "react";
import { AbsoluteFill, OffthreadVideo, Img, staticFile, interpolate, spring, useCurrentFrame, useVideoConfig, Loop } from "remotion";
import { fontFamily } from "./theme";

export type CancelledDossierProps = {
  videoSrc?: string;       // путь в public, напр. "videos/dw_boo.mp4"
  imageSrc?: string;       // фолбэк-картинка, если видео нет
  videoLoopFrames?: number;
  variant?: "monitor" | "fullbleed" | "sidebar";  // раскладка (против «близнецов»)
  caseNo?: string;
  title?: string;
  subtitle?: string;
  meta?: { k: string; v: string; redacted?: boolean }[];
  stamp?: string;
  accent?: string;
};

const rnd = (i: number, s = 1) => {
  const x = Math.sin(i * 42.13 + s * 17.7) * 43758.5453;
  return x - Math.floor(x);
};

// Архивное «досье уничтоженного фильма»: реальный футаж + кино-архив.
// 3 раскладки (variant), чтобы сцены не были близнецами. Ядро стиля DreamWorks.
export const CancelledDossier: React.FC<CancelledDossierProps> = ({
  videoSrc = "videos/dw_boo.mp4",
  imageSrc = "",
  videoLoopFrames = 150,
  variant = "monitor",
  caseNo = "ДЕЛО № 2015-BOO",
  title = "B.O.O.",
  subtitle = "BUREAU OF OTHERWORLDLY OPERATIONS",
  meta = [
    { k: "ГОД", v: "2013–2015" },
    { k: "ОЗВУЧКА", v: "СЕТ РОГЕН · БИЛЛ МЮРРЕЙ" },
    { k: "СТАТУС", v: "УНИЧТОЖЕН ЗА 6 МЕС ДО РЕЛИЗА", redacted: true },
  ],
  stamp = "УНИЧТОЖЕН",
  accent = "#d9282f",
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames, width, height, fps } = useVideoConfig();
  const intro = interpolate(frame, [0, 14], [0, 1], { extrapolateRight: "clamp" });
  const exit = interpolate(frame, [durationInFrames - 14, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });
  const power = spring({ frame, fps, config: { damping: 12, stiffness: 120 } });
  const flick = frame < 16 ? 0.5 + rnd(frame, 2) * 0.5 : 1;
  const st = spring({ frame: frame - 30, fps, config: { damping: 8, stiffness: 220 } });
  const stampScale = interpolate(st, [0, 1], [3.2, 1]);
  const shake = frame >= 30 && frame < 40 ? (rnd(frame, 5) - 0.5) * 10 * (1 - (frame - 30) / 10) : 0;

  const footFilter = "saturate(0.75) contrast(1.05) brightness(0.95)";
  const Footage: React.FC<{ scale?: boolean }> = ({ scale }) =>
    videoSrc ? (
      <Loop durationInFrames={Math.max(30, videoLoopFrames)}>
        <OffthreadVideo src={staticFile(videoSrc)} muted style={{ width: "100%", height: "100%", objectFit: "cover", filter: footFilter }} />
      </Loop>
    ) : imageSrc ? (
      <Img src={staticFile(imageSrc)} style={{ width: "100%", height: "100%", objectFit: "cover",
        transform: scale ? `scale(${1.04 + (frame / durationInFrames) * 0.12})` : undefined, filter: footFilter }} />
    ) : null;

  const Scan: React.FC<{ h: number }> = ({ h }) => (
    <>
      <AbsoluteFill style={{ opacity: 0.18, backgroundImage:
        "repeating-linear-gradient(0deg, #000 0, #000 1px, transparent 1px, transparent 3px)", pointerEvents: "none" }} />
      <div style={{ position: "absolute", left: 0, right: 0, top: (frame * 6) % h, height: 60,
        background: "linear-gradient(180deg, transparent, rgba(255,255,255,0.06), transparent)", pointerEvents: "none" }} />
      <AbsoluteFill style={{ boxShadow: "inset 0 0 90px rgba(0,0,0,0.85)", pointerEvents: "none" }} />
    </>
  );

  const Header = ({ light = false }: { light?: boolean }) => (
    <div style={{ display: "flex", gap: 14, alignItems: "center", letterSpacing: 4 }}>
      <span style={{ color: "#6b6b72", fontSize: light ? 18 : 22, fontWeight: 700 }}>АРХИВ DREAMWORKS</span>
      <span style={{ width: 8, height: 8, background: accent, borderRadius: "50%", boxShadow: `0 0 10px ${accent}` }} />
      <span style={{ color: "#9a9aa2", fontSize: light ? 18 : 22, fontWeight: 700 }}>{caseNo}</span>
    </div>
  );

  const Stamp = ({ rot = -13 }: { rot?: number }) => (stamp && frame > 30 ? (
    <div style={{ transform: `rotate(${rot}deg) scale(${stampScale})`, opacity: Math.min(0.95, st * 1.2),
      color: accent, border: `6px solid ${accent}`, borderRadius: 10, padding: "8px 26px",
      fontSize: 74, fontWeight: 800, letterSpacing: 6, boxShadow: `0 0 26px ${accent}66`,
      textShadow: `0 0 18px ${accent}88`, background: "rgba(10,10,12,0.15)", whiteSpace: "nowrap" }}>{stamp}</div>
  ) : null);

  const Dust = () => (
    <AbsoluteFill style={{ pointerEvents: "none", opacity: intro }}>
      {Array.from({ length: 30 }).map((_, i) => {
        const x = rnd(i, 1) * width, y = (rnd(i, 2) * height + frame * (0.3 + rnd(i, 3))) % height;
        return <div key={i} style={{ position: "absolute", left: x, top: y, width: 2, height: 2,
          background: "#fff", opacity: 0.06 + rnd(i, 4) * 0.12, borderRadius: "50%" }} />;
      })}
    </AbsoluteFill>
  );

  const bg = (
    <>
      <AbsoluteFill style={{ background: "radial-gradient(ellipse at 50% 40%, #16161a 0%, #0b0b0e 55%, #060608 100%)" }} />
      <AbsoluteFill style={{ opacity: 0.06, backgroundImage:
        "repeating-linear-gradient(0deg, #fff 0, #fff 1px, transparent 1px, transparent 3px)" }} />
    </>
  );

  // ── FULLBLEED: футаж на весь кадр, иммерсивно ──────────────────────────────
  if (variant === "fullbleed") {
    return (
      <AbsoluteFill style={{ fontFamily: fontFamily("oswald"), opacity: exit, background: "#000" }}>
        <AbsoluteFill style={{ opacity: intro * flick }}><Footage scale /></AbsoluteFill>
        <Scan h={height} />
        <AbsoluteFill style={{ boxShadow: "inset 0 0 300px rgba(0,0,0,0.9)", background:
          "linear-gradient(180deg, rgba(0,0,0,0.55) 0%, transparent 30%, transparent 55%, rgba(0,0,0,0.8) 100%)", pointerEvents: "none" }} />
        <div style={{ position: "absolute", top: 40, left: 54, opacity: intro }}><Header /></div>
        <div style={{ position: "absolute", left: 54, bottom: 150, opacity: intro }}>
          <div style={{ color: accent, fontSize: 20, fontWeight: 800, letterSpacing: 5, marginBottom: 6 }}>▮ АРХИВНАЯ ЗАПИСЬ</div>
          <div style={{ color: "#fff", fontSize: 104, fontWeight: 800, letterSpacing: 4, lineHeight: 0.9,
            textShadow: "0 6px 30px rgba(0,0,0,0.8)" }}>{title}</div>
          <div style={{ color: "#c9c9cf", fontSize: 26, fontWeight: 700, letterSpacing: 5, marginTop: 4 }}>{subtitle}</div>
        </div>
        <div style={{ position: "absolute", left: 54, bottom: 54, display: "flex", gap: 34, opacity: intro }}>
          {meta.map((m, i) => (
            <div key={i}>
              <div style={{ color: "#8a8a90", fontSize: 15, fontWeight: 700, letterSpacing: 3 }}>{m.k}</div>
              <div style={{ color: m.redacted ? accent : "#e6e6ea", fontSize: 20, fontWeight: 800,
                borderBottom: m.redacted ? `2px solid ${accent}` : "none" }}>{m.v}</div>
            </div>
          ))}
        </div>
        <AbsoluteFill style={{ justifyContent: "center", alignItems: "flex-end", paddingRight: 70, pointerEvents: "none" }}><Stamp rot={-8} /></AbsoluteFill>
        <Dust />
      </AbsoluteFill>
    );
  }

  // ── SIDEBAR: футаж слева, досье-панель справа ──────────────────────────────
  if (variant === "sidebar") {
    const FW = width * 0.60;
    return (
      <AbsoluteFill style={{ fontFamily: fontFamily("oswald"), opacity: exit, background: "#0a0a0c" }}>
        {bg}
        <div style={{ position: "absolute", left: 0, top: 0, width: FW, height: height,
          transform: `translateX(${shake}px)`, opacity: intro * flick, overflow: "hidden",
          borderRight: `3px solid ${accent}`, boxShadow: "24px 0 60px rgba(0,0,0,0.7)" }}>
          <Footage scale />
          <Scan h={height} />
        </div>
        <div style={{ position: "absolute", left: FW + 44, top: 0, width: width - FW - 88, height, opacity: intro,
          display: "flex", flexDirection: "column", justifyContent: "center", gap: 22 }}>
          <Header light />
          <div>
            <div style={{ color: "#f2f2f4", fontSize: 74, fontWeight: 800, letterSpacing: 3, lineHeight: 0.92 }}>{title}</div>
            <div style={{ color: "#8a8a92", fontSize: 22, fontWeight: 700, letterSpacing: 4, marginTop: 4 }}>{subtitle}</div>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            {meta.map((m, i) => {
              const show = interpolate(frame, [18 + i * 6, 26 + i * 6], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
              return (
                <div key={i} style={{ opacity: show, borderLeft: `3px solid ${m.redacted ? accent : "#33333a"}`, paddingLeft: 14 }}>
                  <div style={{ color: "#63636b", fontSize: 16, fontWeight: 700, letterSpacing: 3 }}>{m.k}</div>
                  <div style={{ color: m.redacted ? accent : "#d6d6da", fontSize: 24, fontWeight: 800 }}>{m.v}</div>
                </div>
              );
            })}
          </div>
          {stamp && frame > 30 && <div style={{ marginTop: 6 }}><Stamp rot={-6} /></div>}
        </div>
        <Dust />
      </AbsoluteFill>
    );
  }

  // ── MONITOR (по умолчанию): центральный кино-монитор ───────────────────────
  const MW = width * 0.6, MH = MW * 9 / 16;
  const MX = width * 0.5 - MW / 2, MY = height * 0.16;
  return (
    <AbsoluteFill style={{ fontFamily: fontFamily("oswald"), opacity: exit, background: "#0a0a0c" }}>
      {bg}
      <AbsoluteFill style={{ justifyContent: "flex-start", alignItems: "center", paddingTop: 34, opacity: intro }}><Header /></AbsoluteFill>
      <div style={{ position: "absolute", left: MX, top: MY, width: MW, height: MH,
        transform: `translateX(${shake}px) scale(${0.96 + 0.04 * power})`, opacity: intro * flick,
        borderRadius: 12, background: "#000", border: "3px solid #23232a",
        boxShadow: "0 24px 70px rgba(0,0,0,0.7), inset 0 0 60px rgba(0,0,0,0.8)", overflow: "hidden" }}>
        <Footage scale />
        <Scan h={MH} />
      </div>
      {[MX - 26, MX + MW + 8].map((x, si) => (
        <div key={si} style={{ position: "absolute", left: x, top: MY, width: 18, height: MH, opacity: intro * 0.9 }}>
          {Array.from({ length: Math.floor(MH / 26) }).map((_, i) => (
            <div key={i} style={{ position: "absolute", top: 6 + i * 26, left: 2, width: 14, height: 16,
              background: "#1b1b20", border: "1px solid #2c2c34", borderRadius: 3 }} />
          ))}
        </div>
      ))}
      <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: 150, opacity: intro }}>
        <div style={{ textAlign: "center" }}>
          <div style={{ color: "#f2f2f4", fontSize: 96, fontWeight: 800, letterSpacing: 6, lineHeight: 0.95 }}>{title}</div>
          <div style={{ color: "#8a8a92", fontSize: 26, fontWeight: 700, letterSpacing: 6 }}>{subtitle}</div>
        </div>
      </AbsoluteFill>
      <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: 46, opacity: intro }}>
        <div style={{ display: "flex", gap: 40 }}>
          {meta.map((m, i) => {
            const show = interpolate(frame, [18 + i * 6, 26 + i * 6], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
            return (
              <div key={i} style={{ textAlign: "left", opacity: show }}>
                <div style={{ color: "#63636b", fontSize: 17, fontWeight: 700, letterSpacing: 3 }}>{m.k}</div>
                {m.redacted
                  ? <div style={{ marginTop: 3, color: accent, fontSize: 22, fontWeight: 800, letterSpacing: 1, borderBottom: `2px solid ${accent}` }}>{m.v}</div>
                  : <div style={{ marginTop: 3, color: "#d6d6da", fontSize: 22, fontWeight: 700 }}>{m.v}</div>}
              </div>
            );
          })}
        </div>
      </AbsoluteFill>
      {stamp && frame > 30 && (
        <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", pointerEvents: "none" }}><Stamp /></AbsoluteFill>
      )}
      <Dust />
      <AbsoluteFill style={{ boxShadow: "inset 0 0 260px rgba(0,0,0,0.7)", pointerEvents: "none" }} />
    </AbsoluteFill>
  );
};
