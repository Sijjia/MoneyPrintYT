import React from "react";

// Чувствительные для YouTube корни (RU). Лёгкий блюр → слово читается человеком,
// но модерация/OCR спотыкается, и монетизация не страдает.
const SENSITIVE: RegExp[] = [
  /уб(и|ий|ьё|ью)/, // убийство, убил, убьёт
  /пыт(к|а|о)/, // пытки, пытал
  /изнасил/, // изнасилование
  /насил/, // насилие
  /педофил/,
  /растлен/,
  /самоуб/, // самоубийство
  /суицид/,
  /расстрел/,
  /казн(ь|и|ён)/,
  /труп/,
  /расчлен/,
  /линчева/,
  /резн(я|и)/,
  /теракт/,
  /каннибал/,
  /людоед/,
  /кровь|кровав/,
  /смерт(ь|и|ель)/,
  /мёртв|мертв/,
  /жертв/,
  /наркот/,
  /повеси/,
  /утоп/,
  /сожг|сожж|сгоре/,
  /обезглав/,
  /жесток/,
];

export const isSensitive = (word: string): boolean => {
  const w = word.toLowerCase().replace(/[^a-zа-яё]/gi, "");
  return w.length > 2 && SENSITIVE.some((re) => re.test(w));
};

/**
 * Текст со словами, где чувствительные слегка замазаны блюром.
 * Пробелы сохраняются как есть.
 */
export const Censored: React.FC<{
  text: string;
  blurPx?: number;
  style?: React.CSSProperties;
}> = ({ text, blurPx = 7, style }) => {
  return (
    <span style={style}>
      {text.split(/(\s+)/).map((tok, i) => {
        if (/^\s+$/.test(tok) || tok === "") return tok;
        return (
          <span
            key={i}
            style={{
              display: "inline-block",
              filter: isSensitive(tok) ? `blur(${blurPx}px)` : undefined,
            }}
          >
            {tok}
          </span>
        );
      })}
    </span>
  );
};
