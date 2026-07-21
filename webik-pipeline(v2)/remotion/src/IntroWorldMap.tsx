import React, { useMemo } from "react";
import { AbsoluteFill, Easing, interpolate, useCurrentFrame } from "remotion";
import { geoCentroid, geoGraticule10, geoNaturalEarth1, geoPath } from "d3-geo";
import { feature } from "topojson-client";
import worldRaw from "world-atlas/countries-110m.json";

// Настоящая карта мира (Natural Earth 110m через world-atlas) — реальные границы стран,
// не рисованный вектор. Регионы загораются по очереди ровно на словах закадра.

const AFRICA = [
  "Algeria", "Angola", "Benin", "Botswana", "Burkina Faso", "Burundi", "Cameroon", "Central African Rep.",
  "Chad", "Congo", "Côte d'Ivoire", "Dem. Rep. Congo", "Djibouti", "Egypt", "Eq. Guinea", "Eritrea",
  "eSwatini", "Ethiopia", "Gabon", "Gambia", "Ghana", "Guinea", "Guinea-Bissau", "Kenya", "Lesotho",
  "Liberia", "Libya", "Madagascar", "Malawi", "Mali", "Mauritania", "Morocco", "Mozambique", "Namibia",
  "Niger", "Nigeria", "Rwanda", "S. Sudan", "Senegal", "Sierra Leone", "Somalia", "Somaliland",
  "South Africa", "Sudan", "Tanzania", "Togo", "Tunisia", "Uganda", "W. Sahara", "Zambia", "Zimbabwe",
];

const LATAM = [
  "Mexico", "Guatemala", "Belize", "Honduras", "El Salvador", "Nicaragua", "Costa Rica", "Panama",
  "Colombia", "Venezuela", "Ecuador", "Peru", "Bolivia", "Brazil", "Paraguay", "Uruguay", "Argentina",
  "Chile", "Guyana", "Suriname", "Cuba", "Dominican Rep.", "Haiti", "Jamaica", "Puerto Rico",
  "Trinidad and Tobago",
];

const EUROPE = [
  "France", "Germany", "Spain", "Portugal", "Italy", "Austria", "Switzerland", "Belgium", "Netherlands",
  "Luxembourg", "Denmark", "Norway", "Sweden", "Finland", "Ireland", "United Kingdom", "Poland", "Czechia",
  "Slovakia", "Hungary", "Slovenia", "Croatia", "Bosnia and Herz.", "Serbia", "Montenegro", "Kosovo",
  "Albania", "Macedonia", "Greece", "Bulgaria", "Romania", "Moldova", "Ukraine", "Belarus", "Lithuania",
  "Latvia", "Estonia", "Iceland",
];

const REGION_NAMES: string[][] = [["Russia"], AFRICA, LATAM, EUROPE];

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type Any = any;

export const IntroWorldMap: React.FC<{ accent?: string; beats?: number[]; dur?: number }> = ({
  accent = "#d92828",
  // локальные кадры зажигания: Россия / Африка / Латинская Америка / Европа
  beats = [35, 56, 73, 127],
  dur = 192,
}) => {
  const f = useCurrentFrame();

  const geo = useMemo(() => {
    const world = worldRaw as Any;
    const fcAll = feature(world, world.objects.countries) as Any;
    // Антарктида только зря тянет кадр вниз
    const fc = {
      type: "FeatureCollection",
      features: fcAll.features.filter((ft: Any) => !["Antarctica", "Fr. S. Antarctic Lands"].includes(ft.properties.name)),
    } as Any;
    const proj = geoNaturalEarth1().fitExtent(
      [
        [60, 150],
        [1860, 930],
      ],
      fc
    );
    const path = geoPath(proj);
    const countries: string[] = fc.features.map((ft: Any) => path(ft) || "");
    const grat = path(geoGraticule10()) || "";
    const regions = REGION_NAMES.map((names) => {
      const feats = fc.features.filter((ft: Any) => names.includes(ft.properties.name));
      const d = feats.map((ft: Any) => path(ft) || "").join(" ");
      const c = proj(geoCentroid({ type: "FeatureCollection", features: feats } as Any)) || [960, 540];
      return { d, c: c as [number, number] };
    });
    return { countries, grat, regions };
  }, []);

  const appear = interpolate(f, [0, 26], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
  // общий фейд: карта проявляется из предыдущего кадра и уходит в следующий
  const out = Math.min(
    interpolate(f, [0, 16], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
    interpolate(f, [dur - 26, dur], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })
  );
  // медленный «облёт»: лёгкий наезд + дрейф
  const zoom = interpolate(f, [0, dur], [1.02, 1.09]);
  const panX = Math.sin(f / 120) * 14;
  const panY = interpolate(f, [0, dur], [8, -8]);

  const lit = (i: number) =>
    interpolate(f, [beats[i], beats[i] + 20], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });

  return (
    <AbsoluteFill style={{ background: "radial-gradient(circle at 50% 45%, #0c1420 0%, #05080e 70%)", opacity: out }}>
      <svg width="1920" height="1080">
        <g transform={`translate(${960 + panX} ${540 + panY}) scale(${zoom}) translate(-960 -540)`}>
          {/* сетка параллелей/меридианов — почти незаметная */}
          <path d={geo.grat} fill="none" stroke="rgba(140,170,215,0.10)" strokeWidth={0.7} opacity={appear} />
          {/* все страны: тонкий контур */}
          <g opacity={appear}>
            {geo.countries.map((d, i) => (
              <path key={i} d={d} fill="rgba(120,150,195,0.09)" stroke="rgba(150,182,228,0.30)" strokeWidth={0.7} />
            ))}
          </g>
          {/* дуги между регионами — появляются, когда оба уже горят */}
          {[0, 1, 2].map((i) => {
            const p = interpolate(f, [beats[i + 1], beats[i + 1] + 26], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.inOut(Easing.cubic) });
            const [x1, y1] = geo.regions[i].c;
            const [x2, y2] = geo.regions[i + 1].c;
            const mx = (x1 + x2) / 2;
            const my = (y1 + y2) / 2 - Math.abs(x2 - x1) * 0.28 - 40;
            return (
              <path
                key={i}
                d={`M${x1} ${y1} Q ${mx} ${my} ${x2} ${y2}`}
                fill="none"
                stroke={accent}
                strokeWidth={1.6}
                opacity={0.7 * p}
                strokeDasharray={2600}
                strokeDashoffset={2600 * (1 - p)}
                style={{ filter: `drop-shadow(0 0 6px ${accent})` }}
              />
            );
          })}
          {/* сами регионы: заливка + свечение контура */}
          {geo.regions.map((r, i) => {
            const on = lit(i);
            const glow = 0.5 + 0.5 * Math.max(0, Math.sin((f - beats[i]) / 11));
            return (
              <g key={i} opacity={on}>
                <path d={r.d} fill={accent} opacity={0.16 + 0.1 * glow} />
                <path d={r.d} fill="none" stroke={accent} strokeWidth={1.4} opacity={0.85} style={{ filter: `drop-shadow(0 0 7px ${accent})` }} />
              </g>
            );
          })}
          {/* маркеры-пульсары в центрах регионов */}
          {geo.regions.map((r, i) => {
            const on = lit(i);
            const ring = ((f - beats[i]) % 34) / 34;
            const [x, y] = r.c;
            return (
              <g key={i} opacity={on}>
                <circle cx={x} cy={y} r={6 + 26 * ring} fill="none" stroke={accent} strokeWidth={1.2} opacity={(1 - ring) * 0.55} />
                <circle cx={x} cy={y} r={4.5} fill="#fff" style={{ filter: `drop-shadow(0 0 8px ${accent})` }} />
              </g>
            );
          })}
        </g>
      </svg>
    </AbsoluteFill>
  );
};
