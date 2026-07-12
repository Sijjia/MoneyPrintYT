import { loadFont as loadMontserrat } from "@remotion/google-fonts/Montserrat";
import { loadFont as loadOswald } from "@remotion/google-fonts/Oswald";

// Кириллица + латиница, нужные веса.
export const montserrat = loadMontserrat("normal", {
  weights: ["600", "700", "800"],
  subsets: ["cyrillic", "latin"],
}).fontFamily;

export const oswald = loadOswald("normal", {
  weights: ["500", "600", "700"],
  subsets: ["cyrillic", "latin"],
}).fontFamily;

export type FontName = "montserrat" | "oswald" | "system";

export const fontFamily = (f: FontName): string => {
  if (f === "montserrat") return `${montserrat}, 'Segoe UI', sans-serif`;
  if (f === "oswald") return `${oswald}, 'Segoe UI', sans-serif`;
  return "'Segoe UI', 'Arial', system-ui, sans-serif";
};

export const PALETTE = {
  cream: "#f4f1ea",
  gold: "#c8a24a",
  red: "#d92828",
  redDeep: "#b81f24",
};
