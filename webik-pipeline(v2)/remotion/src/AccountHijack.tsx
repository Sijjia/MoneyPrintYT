import React from "react";
import {
  AbsoluteFill,
  Easing,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
  random,
} from "remotion";
import { fontFamily } from "./theme";

export type AccountHijackProps = {
  caption: string;          // короткая RU-фраза внизу
  target?: string;          // «жертва»/аккаунт
  mode?: "hijack" | "cookie" | "phish"; // акцент: угон / кража cookie / фишинг
  accent?: string;
};

const MONO = "'Consolas', 'Courier New', monospace";
const HEX = "0123456789abcdef";
const rnd = (s: string, n: number) =>
  Array.from({ length: n }, (_, i) => HEX[Math.floor(random(`${s}${i}`) * 16)]).join("");

// Экран угона аккаунта Roblox: бегущие креды, кража cookie .ROBLOSECURITY, обход 2FA, ACCESS GRANTED.
export const AccountHijack: React.FC<AccountHijackProps> = ({
  caption, target = "victim_2007", mode = "hijack", accent = "#39d98a",
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames, width, height } = useVideoConfig();
  const boot = interpolate(frame, [0, 12], [0, 1], { extrapolateRight: "clamp" });
  const exit = interpolate(frame, [durationInFrames - 12, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });
  const flicker = 0.92 + 0.08 * Math.sin(frame * 1.7);
  const scanY = (frame * 8) % 100;

  const grantAt = Math.round(durationInFrames * 0.62);
  const granted = frame >= grantAt;
  const glitch = frame >= grantAt - 5 && frame < grantAt + 7;
  const gx = glitch ? (random(`gx${frame}`) - 0.5) * 30 : 0;

  // строки «перебора» кредов
  const rows = 9;
  const cred = Array.from({ length: rows }, (_, r) => {
    const solved = granted || frame > 14 + r * 5;
    return { r, user: `${target}`, pass: solved ? "••••••••✓" : rnd(`p${r}${Math.floor(frame / 2)}`, 10), solved };
  });

  const cookie = ".ROBLOSECURITY=_|WARNING:-DO-NOT-SHARE|_" + rnd(`ck${Math.floor(frame / 3)}`, 40);
  const pct = Math.min(100, Math.floor(interpolate(frame, [10, grantAt], [0, 100], { extrapolateRight: "clamp" })));
  const header = mode === "cookie" ? "КРАЖА COOKIE" : mode === "phish" ? "ФИШИНГ" : "УГОН АККАУНТА";

  return (
    <AbsoluteFill style={{ background: "#050608", fontFamily: MONO, opacity: exit }}>
      {/* центральное окно терминала */}
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", opacity: boot * flicker }}>
        <div style={{
          width: 1420, background: "linear-gradient(180deg, rgba(6,12,10,0.9), rgba(4,6,8,0.92))",
          border: `2px solid ${accent}`, boxShadow: `0 0 60px ${accent}44, inset 0 0 90px rgba(0,0,0,0.6)`,
          padding: "40px 54px 48px", position: "relative", transform: `translateX(${gx}px)`,
        }}>
          {[["left", "top"], ["right", "top"], ["left", "bottom"], ["right", "bottom"]].map(([x, y], i) => (
            <div key={i} style={{ position: "absolute", [x]: 12, [y]: 12, width: 38, height: 38, borderTop: y === "top" ? `3px solid ${accent}` : "none", borderBottom: y === "bottom" ? `3px solid ${accent}` : "none", borderLeft: x === "left" ? `3px solid ${accent}` : "none", borderRight: x === "right" ? `3px solid ${accent}` : "none" }} />
          ))}
          {/* хедер */}
          <div style={{ display: "flex", alignItems: "center", gap: 14, color: accent, fontSize: 30, letterSpacing: 5, fontWeight: 700 }}>
            <span style={{ opacity: Math.sin(frame * 0.5) > 0 ? 1 : 0.3 }}>●</span> {header}
            <span style={{ marginLeft: "auto", fontSize: 22, opacity: 0.7 }}>ROBLOX · target: {target}</span>
          </div>
          {/* строки перебора */}
          <div style={{ marginTop: 22, fontSize: 26, lineHeight: "38px", color: "#cfe" }}>
            {cred.map((c) => (
              <div key={c.r} style={{ opacity: c.solved ? 1 : 0.5, color: c.solved ? accent : "#8aa" }}>
                <span style={{ color: accent }}>&gt;</span> login: {c.user} &nbsp; pass: {c.pass} {c.solved && <span style={{ color: accent }}> OK</span>}
              </div>
            ))}
          </div>
          {/* украденный cookie */}
          <div style={{ marginTop: 18, padding: "10px 14px", border: `1px dashed ${accent}66`, color: "#9fd", fontSize: 18, letterSpacing: 1, whiteSpace: "nowrap", overflow: "hidden" }}>
            {cookie.slice(0, 96)}
          </div>
          {/* прогресс / статус */}
          {!granted ? (
            <div style={{ marginTop: 22 }}>
              <div style={{ color: accent, fontSize: 24, letterSpacing: 3 }}>ПОДБОР… обход 2FA: {pct}%</div>
              <div style={{ marginTop: 8, height: 8, background: "rgba(255,255,255,0.08)" }}>
                <div style={{ height: 8, width: `${pct}%`, background: accent, boxShadow: `0 0 14px ${accent}` }} />
              </div>
            </div>
          ) : (
            <div style={{ marginTop: 26, textAlign: "center" }}>
              <div style={{ display: "inline-block", color: "#eafff4", background: accent, fontSize: 54, fontWeight: 800, letterSpacing: 6, padding: "10px 40px", transform: `translateX(${gx}px) rotate(-1deg)`, boxShadow: `0 0 40px ${accent}` }}>
                ACCESS GRANTED
              </div>
              <div style={{ marginTop: 14, color: accent, fontSize: 26, letterSpacing: 3 }}>2FA ОБОЙДЕНА · ПРЕДМЕТЫ ВЫВЕДЕНЫ</div>
            </div>
          )}
        </div>
      </AbsoluteFill>

      {/* подпись снизу */}
      <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: 90,
        opacity: interpolate(frame, [16, 32], [0, 1], { extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) }) * exit }}>
        <div style={{ maxWidth: 1500, textAlign: "center", color: "#f4f1ea", fontFamily: fontFamily("oswald"), fontSize: 50, fontWeight: 600, textShadow: "0 4px 24px rgba(0,0,0,0.9)", lineHeight: 1.15, borderLeft: `4px solid ${accent}`, borderRight: `4px solid ${accent}`, padding: "6px 34px" }}>
          {caption}
        </div>
      </AbsoluteFill>

      {/* скан-лайны + развёртка + виньетка */}
      <AbsoluteFill style={{ background: "repeating-linear-gradient(0deg, rgba(0,0,0,0.32) 0px, rgba(0,0,0,0.32) 1px, transparent 3px, transparent 5px)", pointerEvents: "none" }} />
      <div style={{ position: "absolute", left: 0, right: 0, top: `${scanY}%`, height: 110, background: `linear-gradient(180deg, transparent, ${accent}12, transparent)`, pointerEvents: "none" }} />
      <AbsoluteFill style={{ boxShadow: "inset 0 0 280px rgba(0,0,0,0.92)", pointerEvents: "none" }} />
      {glitch && <div style={{ position: "absolute", left: 0, right: 0, top: `${random(`gy${frame}`) * 70 + 12}%`, height: 8 + random(`gh${frame}`) * 26, background: accent, opacity: 0.28, mixBlendMode: "screen", transform: `translateX(${gx * 2}px)` }} />}
    </AbsoluteFill>
  );
};
