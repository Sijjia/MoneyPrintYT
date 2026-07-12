import { Composition } from "remotion";
import { StatPop } from "./StatPop";
import { NameLabel } from "./NameLabel";
import { KineticPhrase } from "./KineticPhrase";
import { EvidenceFrame } from "./EvidenceFrame";
import { CountUpBar } from "./CountUpBar";
import { BarCompare } from "./BarCompare";
import { Pictograph } from "./Pictograph";
import { DonutProportion } from "./DonutProportion";

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
    </>
  );
};
