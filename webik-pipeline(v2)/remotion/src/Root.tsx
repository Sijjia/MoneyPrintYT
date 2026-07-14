import { Composition } from "remotion";
import { StatPop } from "./StatPop";
import { NameLabel } from "./NameLabel";
import { KineticPhrase } from "./KineticPhrase";
import { EvidenceFrame } from "./EvidenceFrame";
import { CountUpBar } from "./CountUpBar";
import { BarCompare } from "./BarCompare";
import { Pictograph } from "./Pictograph";
import { DonutProportion } from "./DonutProportion";
import { Timeline } from "./Timeline";
import { MapPins } from "./MapPins";
import { QuoteCard } from "./QuoteCard";
import { Spotlight } from "./Spotlight";
import { CinematicStat } from "./CinematicStat";
import { CinematicScene } from "./CinematicScene";
import { Scene } from "./Scene";
import { Globe3D } from "./Globe3D";

const W = 1920;
const H = 1080;

// 1920x1080 @ 30fps. Оверлеи для конкретных моментов ролика.
// Стиль утверждён: красный-акцент + Oswald + лёгкий блюр чувствительных слов
// (задан дефолтами в компонентах). bgImage — только для превью в Studio;
// в проде рендер-мост передаёт bgImage:null → прозрачный фон (альфа).
export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="StatPop"
        component={StatPop}
        durationInFrames={110}
        fps={30}
        width={W}
        height={H}
        defaultProps={{
          value: "307",
          label: "массовых убийств · Кадуна",
          suffix: "",
          countUp: true,
          bgImage: "preview_bg.jpg" as string | null,
        }}
      />

      <Composition
        id="NameLabel"
        component={NameLabel}
        durationInFrames={110}
        fps={30}
        width={W}
        height={H}
        defaultProps={{
          name: "Колония Дигнидад",
          sub: "Чили · 1961",
          bgImage: "preview_bg2.jpg" as string | null,
        }}
      />

      <Composition
        id="KineticPhrase"
        component={KineticPhrase}
        durationInFrames={120}
        fps={30}
        width={W}
        height={H}
        defaultProps={{
          phrase: "Триста семь жертв за одну ночь",
          highlight: [0, 1],
          bgImage: "preview_bg3.jpg" as string | null,
        }}
      />

      <Composition
        id="EvidenceFrame"
        component={EvidenceFrame}
        durationInFrames={130}
        fps={30}
        width={W}
        height={H}
        defaultProps={{
          label: "АРХИВ",
          sub: "1978 · Джонстаун",
          bgImage: "preview_bg2.jpg" as string | null,
        }}
      />

      <Composition
        id="CountUpBar"
        component={CountUpBar}
        durationInFrames={110}
        fps={30}
        width={W}
        height={H}
        defaultProps={{
          value: "307",
          label: "жертв за одну ночь",
          suffix: "",
          max: null as number | null,
          bgImage: "preview_bg.jpg" as string | null,
        }}
      />

      <Composition
        id="BarCompare"
        component={BarCompare}
        durationInFrames={130}
        fps={30}
        width={W}
        height={H}
        defaultProps={{
          title: "Жертвы культов",
          items: [
            { label: "Джонстаун", value: 918 },
            { label: "Орден Храма Солнца", value: 74 },
            { label: "Уэйко", value: 82 },
            { label: "Хевенс-Гейт", value: 39 },
          ],
          bgImage: "preview_bg2.jpg" as string | null,
        }}
      />

      <Composition
        id="Pictograph"
        component={Pictograph}
        durationInFrames={120}
        fps={30}
        width={W}
        height={H}
        defaultProps={{
          filled: 9,
          total: 10,
          label: "не выжили",
          bgImage: "preview_bg3.jpg" as string | null,
        }}
      />

      <Composition
        id="DonutProportion"
        component={DonutProportion}
        durationInFrames={120}
        fps={30}
        width={W}
        height={H}
        defaultProps={{
          percent: 87,
          label: "не вернулись домой",
          bgImage: "preview_bg2.jpg" as string | null,
        }}
      />

      <Composition
        id="Timeline"
        component={Timeline}
        durationInFrames={150}
        fps={30}
        width={W}
        height={H}
        defaultProps={{
          title: "Крупнейшие трагедии культов",
          events: [
            { year: "1978", label: "Джонстаун" },
            { year: "1993", label: "Уэйко" },
            { year: "1997", label: "Хевенс-Гейт" },
            { year: "2000", label: "Уганда" },
          ],
          bgImage: "preview_bg2.jpg" as string | null,
        }}
      />

      <Composition
        id="MapPins"
        component={MapPins}
        durationInFrames={160}
        fps={30}
        width={W}
        height={H}
        defaultProps={{
          title: "География культов",
          places: [
            { label: "Джонстаун", lat: 4.9, lon: -58.9 },
            { label: "Колония Дигнидад", lat: -36.4, lon: -71.9 },
            { label: "Шакахола", lat: -3.0, lon: 39.9 },
            { label: "Уэйко", lat: 31.5, lon: -97.2 },
            { label: "Кадуна", lat: 10.5, lon: 7.4 },
          ],
          bgImage: null as string | null,
        }}
      />

      <Composition
        id="QuoteCard"
        component={QuoteCard}
        durationInFrames={140}
        fps={30}
        width={W}
        height={H}
        defaultProps={{
          text: "Я — реинкарнация Иисуса Христа",
          author: "Анна Хэмилтон-Бирн",
          bgImage: "preview_bg2.jpg" as string | null,
        }}
      />

      <Composition
        id="Spotlight"
        component={Spotlight}
        durationInFrames={120}
        fps={30}
        width={W}
        height={H}
        defaultProps={{
          label: "Обратите внимание",
          x: 50,
          y: 48,
          bgImage: "preview_bg3.jpg" as string | null,
        }}
      />

      <Composition
        id="CinematicStat"
        component={CinematicStat}
        durationInFrames={300}
        fps={30}
        width={W}
        height={H}
        defaultProps={{
          value: "307",
          label: "жертв за одну ночь",
          suffix: "",
          sub: "Кадуна · Нигерия",
          bgImage: "preview_bg.jpg" as string | null,
        }}
      />

      <Composition
        id="CinematicScene"
        component={CinematicScene}
        durationInFrames={400}
        fps={30}
        width={W}
        height={H}
        defaultProps={{
          headline: "Кадуна · 2019",
          a: { value: "307", label: "погибших", suffix: "" },
          b: { value: "300", label: "освобождено", suffix: "" },
          bgImage: "preview_bg.jpg" as string | null,
        }}
      />

      <Composition
        id="Scene"
        component={Scene}
        durationInFrames={600}
        fps={30}
        width={W}
        height={H}
        calculateMetadata={({ props }: any) => {
          const shots = (props?.shots || []) as Array<{ move: number; hold: number }>;
          const total = shots.reduce((a, s) => a + (s.move || 0) + (s.hold || 0), 0) + 24;
          return { durationInFrames: Math.max(60, total) };
        }}
        defaultProps={{
          bgImage: "preview_bg2.jpg" as string | null,
          blocks: [
            { id: "a", kind: "stat" as const, x: 700, y: 640, value: "918", label: "Джонстаун" },
            { id: "b", kind: "bars" as const, x: 1500, y: 640, items: [{ label: "Взрослые", value: 12 }, { label: "Дети", value: 22 }] },
            { id: "c", kind: "ratio" as const, x: 2300, y: 640, filled: 9, total: 10, label: "не выжили" },
            { id: "h", kind: "headline" as const, x: 1500, y: 300, text: "Массовые трагедии культов" },
          ],
          shots: [
            { focus: "a", zoom: 1.55, move: 0, hold: 80 },
            { focus: "b", zoom: 1.55, move: 60, hold: 80 },
            { focus: "c", zoom: 1.55, move: 60, hold: 80 },
            { focus: "h", zoom: 0.7, move: 95, hold: 110 },
          ],
        }}
      />

      <Composition
        id="Globe3D"
        component={Globe3D}
        durationInFrames={300}
        fps={30}
        width={W}
        height={H}
        defaultProps={{
          accent: "#d92828",
          places: [
            { lat: 4.9, lon: -58.9, label: "Джонстаун" },
            { lat: -36.4, lon: -71.9, label: "Колония Дигнидад" },
            { lat: -3.0, lon: 39.9, label: "Шакахола" },
            { lat: 10.5, lon: 7.4, label: "Кадуна" },
            { lat: 25.9, lon: -97.5, label: "Матаморос" },
            { lat: -37.0, lon: 144.5, label: "Виктория" },
            { lat: 35.7, lon: 139.7, label: "Токио" },
          ],
        }}
      />
    </>
  );
};
