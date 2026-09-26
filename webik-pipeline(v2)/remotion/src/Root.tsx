import { Composition } from "remotion";
import { StatPop } from "./StatPop";
import { IcebergRecap } from "./IcebergRecap";
import { DNAHelix3D } from "./DNAHelix3D";
import { HomininTree } from "./HomininTree";
import { PopulationCollapse } from "./PopulationCollapse";
import { ParasitePuppet } from "./ParasitePuppet";
import { VirusGenome } from "./VirusGenome";
import { CRISPRCut } from "./CRISPRCut";
import { CordycepsTakeover3D } from "./CordycepsTakeover3D";
import { PhotoMontage } from "./PhotoMontage";
import { EugenicsRegistry } from "./EugenicsRegistry";
import { TuskErosion } from "./TuskErosion";
import { RatioViz17 } from "./RatioViz17";
import { PrionBrain } from "./PrionBrain";
import { LastHuman } from "./LastHuman";
import { CancelledDossier } from "./CancelledDossier";
import { FilmStrip } from "./FilmStrip";
import { DramaFreeze } from "./DramaFreeze";
import { MoneyCounter } from "./MoneyCounter";
import { NewsHeadline } from "./NewsHeadline";
import { QuoteCardDW } from "./QuoteCardDW";
import { UncannyCGI } from "./UncannyCGI";
import { SplitCompare } from "./SplitCompare";
import { StudioTimeline } from "./StudioTimeline";
import { GlitchLeak } from "./GlitchLeak";
import { Mascot } from "./Mascot";
import { GTARecordsStage } from "./GTARecordsStage";
import { BigfootHunt } from "./BigfootHunt";
import { UFOScene } from "./UFOScene";
import { KurtajHack } from "./KurtajHack";
import { MascotOutro } from "./MascotOutro";
import { PortraitQuote } from "./PortraitQuote";
import { NameLabel } from "./NameLabel";
import { KineticPhrase } from "./KineticPhrase";
import { EvidenceFrame } from "./EvidenceFrame";
import { CountUpBar } from "./CountUpBar";
import { BarCompare } from "./BarCompare";
import { PropagandaPoster } from "./PropagandaPoster";
import { SurveillanceTerminal } from "./SurveillanceTerminal";
import { ARGSignal } from "./ARGSignal";
import { BreakingAlert } from "./BreakingAlert";
import { AccountHijack } from "./AccountHijack";
import { StolenCounter } from "./StolenCounter";
import { BeamingTrade } from "./BeamingTrade";
import { NewsAlert } from "./NewsAlert";
import { LaunderFlow } from "./LaunderFlow";
import { RobloxTimeline } from "./RobloxTimeline";
import { MythReveal } from "./MythReveal";
import { RedactedDossier } from "./RedactedDossier";
import { PropagandaHall } from "./PropagandaHall";
import { SurveillanceGrid } from "./SurveillanceGrid";
import { PrisonCamp } from "./PrisonCamp";
import { NightSatellite } from "./NightSatellite";
import { CastePyramid } from "./CastePyramid";
import { BureauVault } from "./BureauVault";
import { AbyssDescent } from "./AbyssDescent";
import { CyberIntrusion } from "./CyberIntrusion";
import { ForcedMourning } from "./ForcedMourning";
import { IronCells } from "./IronCells";
import { RedditThread } from "./RedditThread";
import { GangesGhats } from "./GangesGhats";
import { NagaUnderworld } from "./NagaUnderworld";
import { SkeletonLake } from "./SkeletonLake";
import { FortCurse } from "./FortCurse";
import { VaultDoorB } from "./VaultDoorB";
import { ThugStrangler } from "./ThugStrangler";
import { KumbhaMela } from "./KumbhaMela";
import { RatTemple } from "./RatTemple";
import { TwinVillage } from "./TwinVillage";
import { BirdFall } from "./BirdFall";
import { GuruDossier } from "./GuruDossier";
import { KarniCurse } from "./KarniCurse";
import { SentinelIsland } from "./SentinelIsland";
import { CrowdSilhouette } from "./CrowdSilhouette";
import { EnumShowcase } from "./EnumShowcase";
import { HexCipher } from "./HexCipher";
import { LiminalSpace } from "./LiminalSpace";
import { DocuFrame } from "./DocuFrame";
import { RationHunger } from "./RationHunger";
import { Abduction } from "./Abduction";
import { TheftRoutes } from "./TheftRoutes";
import { CollapseBurst } from "./CollapseBurst";
import { IcebergIntro } from "./IcebergIntro";
import { OutroReflection } from "./OutroReflection";
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
import { CrowdPictograph } from "./CrowdPictograph";
import { KineticType } from "./KineticType";
import { TimelineJourney } from "./TimelineJourney";
import { ProportionFill } from "./ProportionFill";
import { DossierCard } from "./DossierCard";
import { PhotoAnnotate } from "./PhotoAnnotate";
import { ShockCounter } from "./ShockCounter";
import { MapSpread } from "./MapSpread";
import { NetworkGraph } from "./NetworkGraph";
import { IntroSequence } from "./IntroSequence";
import { IntroFootage } from "./IntroFootage";
import { PhotoZoom } from "./PhotoZoom";

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
        id="PropagandaPoster"
        component={PropagandaPoster}
        durationInFrames={110}
        fps={30}
        width={W}
        height={H}
        defaultProps={{ value: "51", label: "каста", suffix: "" }}
      />
      <Composition
        id="SurveillanceTerminal"
        component={SurveillanceTerminal}
        durationInFrames={110}
        fps={30}
        width={W}
        height={H}
        defaultProps={{ value: "81000000", label: "украдено", suffix: " $" }}
      />
      <Composition
        id="BreakingAlert"
        component={BreakingAlert}
        durationInFrames={150}
        fps={30}
        width={W}
        height={H}
        defaultProps={{ kicker: "СРОЧНО", headline: "БОСТОН ПАРАЛИЗОВАН: ПОДОЗРИТЕЛЬНЫЕ УСТРОЙСТВА В 10 ГОРОДАХ", cities: 10, reveal: "Это была реклама мультфильма про говорящую котлету.", stamp: "ЭТО БЫЛА РЕКЛАМА", showMooninite: true }}
      />
      <Composition
        id="AccountHijack"
        component={AccountHijack}
        durationInFrames={150}
        fps={30}
        width={W}
        height={H}
        defaultProps={{ caption: "Украденный cookie даёт вход в обход пароля и 2FA.", target: "victim_2007", mode: "hijack" }}
      />
      <Composition
        id="StolenCounter"
        component={StolenCounter}
        durationInFrames={140}
        fps={30}
        width={W}
        height={H}
        defaultProps={{ value: 610000, prefix: "", suffix: "", label: "УГНАНО АККАУНТОВ", sub: "за три месяца", caption: "Прибыль хакеров — около двухсот двадцати пяти тысяч долларов." }}
      />
      <Composition
        id="BeamingTrade"
        component={BeamingTrade}
        durationInFrames={140}
        fps={30}
        width={W}
        height={H}
        defaultProps={{ itemName: "Sparkle Time Fedora", itemSub: "LIMITED · MIDNIGHT BLUE", price: "$13 605", caption: "Один краденый предмет — тринадцать тысяч долларов реальных денег." }}
      />
      <Composition
        id="NewsAlert"
        component={NewsAlert}
        durationInFrames={140}
        fps={30}
        width={W}
        height={H}
        defaultProps={{ kicker: "АРЕСТ", headline: "ПОЛИЦИЯ ЛЬВОВА ЗАДЕРЖАЛА ТРОИХ ХАКЕРОВ ROBLOX", outlet: "BleepingComputer", location: "Львов, Украина", caption: "Скомпрометировано 610 000 аккаунтов, прибыль ~$225 000." }}
      />
      <Composition
        id="LaunderFlow"
        component={LaunderFlow}
        durationInFrames={150}
        fps={30}
        width={W}
        height={H}
        defaultProps={{ caption: "Roblox зарабатывает свои тридцать процентов на каждой транзакции в цепочке." }}
      />
      <Composition
        id="RobloxTimeline"
        component={RobloxTimeline}
        durationInFrames={160}
        fps={30}
        width={W}
        height={H}
        defaultProps={{ caption: "От DynaBlocks до платформы с миллиардом пользователей." }}
      />
      <Composition
        id="MythReveal"
        component={MythReveal}
        durationInFrames={150}
        fps={30}
        width={W}
        height={H}
        defaultProps={{ subject: "Bigfoot", myth: "В San Andreas якобы спрятан снежный человек — его искали годами.", truth: "Его там никогда не было. Все скриншоты — моды и фотошоп.", caption: "Rockstar подтвердила: Bigfoot в игре нет." }}
      />
      <Composition
        id="ARGSignal"
        component={ARGSignal}
        durationInFrames={150}
        fps={30}
        width={W}
        height={H}
        defaultProps={{ mode: "signal", caption: "Скрытые сайты, коды, послания в эфире.", code: "as://hidden/delilah" }}
      />
      <Composition
        id="RedactedDossier"
        component={RedactedDossier}
        durationInFrames={110}
        fps={30}
        width={W}
        height={H}
        defaultProps={{ value: "200000", label: "исчезли", suffix: "" }}
      />
      <Composition
        id="PropagandaHall"
        component={PropagandaHall}
        durationInFrames={450}
        fps={30}
        width={W}
        height={H}
        defaultProps={{ title: "КУЛЬТ ЛИЧНОСТИ" }}
      />
      <Composition
        id="SurveillanceGrid"
        component={SurveillanceGrid}
        durationInFrames={450}
        fps={30}
        width={W}
        height={H}
        defaultProps={{ title: "ТОТАЛЬНАЯ СЛЕЖКА" }}
      />
      <Composition
        id="PrisonCamp"
        component={PrisonCamp}
        durationInFrames={450}
        fps={30}
        width={W}
        height={H}
        defaultProps={{ title: "ЛАГЕРЯ" }}
      />
      <Composition
        id="NightSatellite"
        component={NightSatellite}
        durationInFrames={450}
        fps={30}
        width={W}
        height={H}
        defaultProps={{ title: "СТРАНА-ПРИЗРАК" }}
      />
      <Composition
        id="CastePyramid"
        component={CastePyramid}
        durationInFrames={450}
        fps={30}
        width={W}
        height={H}
        defaultProps={{ title: "СОНБУН" }}
      />
      <Composition
        id="BureauVault"
        component={BureauVault}
        durationInFrames={450}
        fps={30}
        width={W}
        height={H}
        defaultProps={{ title: "БЮРО 39" }}
      />
      <Composition
        id="AbyssDescent"
        component={AbyssDescent}
        durationInFrames={450}
        fps={30}
        width={W}
        height={H}
        defaultProps={{ title: "БЕЗДНА" }}
      />
      <Composition
        id="CyberIntrusion"
        component={CyberIntrusion}
        durationInFrames={450}
        fps={30}
        width={W}
        height={H}
        defaultProps={{ title: "КИБЕР-АРМИЯ" }}
      />
      <Composition
        id="ForcedMourning"
        component={ForcedMourning}
        durationInFrames={450}
        fps={30}
        width={W}
        height={H}
        defaultProps={{ title: "СЛЁЗЫ ПОД НАДЗОРОМ" }}
      />
      <Composition
        id="IronCells"
        component={IronCells}
        durationInFrames={450}
        fps={30}
        width={W}
        height={H}
        defaultProps={{ title: "ЛАГЕРЬ 22" }}
      />
      <Composition
        id="RationHunger"
        component={RationHunger}
        durationInFrames={450}
        fps={30}
        width={W}
        height={H}
        defaultProps={{ title: "ИЕРАРХИЯ ГОЛОДА" }}
      />
      <Composition
        id="Abduction"
        component={Abduction}
        durationInFrames={450}
        fps={30}
        width={W}
        height={H}
        defaultProps={{ title: "ПОХИЩЕНИЯ" }}
      />
      <Composition
        id="TheftRoutes"
        component={TheftRoutes}
        durationInFrames={180}
        fps={30}
        width={W}
        height={H}
        defaultProps={{ title: "МАРШРУТЫ КРАЖ" }}
      />
      <Composition
        id="CollapseBurst"
        component={CollapseBurst}
        durationInFrames={108}
        fps={30}
        width={W}
        height={H}
        defaultProps={{ title: "" }}
      />
      <Composition
        id="IcebergIntro"
        component={IcebergIntro}
        durationInFrames={450}
        fps={30}
        width={W}
        height={H}
        defaultProps={{ title: "АЙСБЕРГ", sub: "СЕВЕРНОЙ КОРЕИ" }}
        calculateMetadata={({ props }) => ({
          durationInFrames: (props as { durationInFrames?: number }).durationInFrames ?? 450,
        })}
      />
      <Composition
        id="OutroReflection"
        component={OutroReflection}
        durationInFrames={2037}
        fps={30}
        width={W}
        height={H}
        defaultProps={{ shots: [], accent: "#ff4500", brand: "REDDIT", riseFrom: 440 }}
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

      <Composition
        id="CrowdPictograph"
        component={CrowdPictograph}
        durationInFrames={160}
        fps={30}
        width={W}
        height={H}
        defaultProps={{ total: 920, filled: 918, label: "погибли", sub: "Джонстаун · 1978", accent: "#d92828" }}
      />

      <Composition
        id="KineticType"
        component={KineticType}
        durationInFrames={150}
        fps={30}
        width={W}
        height={H}
        calculateMetadata={({ props }: any) => {
          const words = (props?.lines || []).reduce((a: number, l: string) => a + l.split(/\s+/).filter(Boolean).length, 0);
          return { durationInFrames: Math.max(90, 40 + words * 7 + 60) };
        }}
        defaultProps={{ lines: ["Убийство", "во имя веры"], highlight: "Убийство", stat: "", statLabel: "", accent: "#d92828" }}
      />

      <Composition
        id="TimelineJourney"
        component={TimelineJourney}
        durationInFrames={240}
        fps={30}
        width={W}
        height={H}
        calculateMetadata={({ props }: any) => {
          if (props?.durationInFrames) return { durationInFrames: props.durationInFrames };
          const n = (props?.events || []).length || 1;
          return { durationInFrames: Math.max(120, 50 + n * 55) };
        }}
        defaultProps={{
          title: "Хроника террора",
          events: [
            { year: 1978, label: "Джонстаун" },
            { year: 1993, label: "Уэйко" },
            { year: 2000, label: "Канунгу" },
            { year: 2023, label: "Шакахола" },
          ],
          accent: "#d92828",
        }}
      />

      <Composition
        id="IcebergRecap"
        component={IcebergRecap}
        durationInFrames={534}
        fps={30}
        width={W}
        height={H}
        calculateMetadata={({ props }: any) => {
          if (props?.durationInFrames) return { durationInFrames: props.durationInFrames };
          return { durationInFrames: 534 };
        }}
        defaultProps={{
          title: "Мы прошли весь айсберг",
          levels: [
            { n: "1", label: "Мошенники в рясах" },
            { n: "2", label: "Секты и затворники" },
            { n: "3", label: "Культы-убийцы" },
            { n: "4", label: "Массовые убийства" },
          ],
          accent: "#d92828",
        }}
      />

      <Composition
        id="ProportionFill"
        component={ProportionFill}
        durationInFrames={150}
        fps={30}
        width={W}
        height={H}
        defaultProps={{ percent: 87, label: "не вернулись", sub: "из тех, кто вошёл", accent: "#d92828" }}
      />

      <Composition
        id="DossierCard"
        component={DossierCard}
        durationInFrames={170}
        fps={30}
        width={W}
        height={H}
        defaultProps={{
          name: "Джим Джонс",
          role: "Основатель «Храма народов»",
          fields: [
            { k: "Секта", v: "Храм народов" },
            { k: "Жертв", v: "918" },
            { k: "Страна · год", v: "Гайана · 1978" },
          ],
          stamp: "погиб",
          photo: null,
          accent: "#d92828",
        }}
      />

      <Composition
        id="PhotoAnnotate"
        component={PhotoAnnotate}
        durationInFrames={170}
        fps={30}
        width={W}
        height={H}
        defaultProps={{
          photo: null,
          title: "Место массового захоронения",
          annotations: [
            { x: 38, y: 44, r: 90, label: "следы борьбы" },
            { x: 64, y: 58, r: 64, label: "личные вещи" },
          ],
          accent: "#d92828",
        }}
      />

      <Composition
        id="ShockCounter"
        component={ShockCounter}
        durationInFrames={150}
        fps={30}
        width={W}
        height={H}
        defaultProps={{ from: 0, to: 778, label: "погибших", sub: "Канунгу · 2000", accent: "#d92828" }}
      />

      <Composition
        id="MapSpread"
        component={MapSpread}
        durationInFrames={160}
        fps={30}
        calculateMetadata={({ props }: any) => (props?.durationInFrames ? { durationInFrames: props.durationInFrames } : {})}
        width={W}
        height={H}
        defaultProps={{
          title: "Как расползалась секта",
          label: "1955 → 1978",
          origins: [
            { x: 22, y: 42, grow: 260, label: "Индианаполис" },
            { x: 17, y: 60, grow: 360, label: "Гайана" },
          ],
          accent: "#d92828",
        }}
      />

      <Composition
        id="NetworkGraph"
        component={NetworkGraph}
        durationInFrames={170}
        fps={30}
        width={W}
        height={H}
        calculateMetadata={({ props }: any) => {
          if (props?.durationInFrames) return { durationInFrames: props.durationInFrames };
          return {};
        }}
        defaultProps={{
          title: "Структура культа",
          nodes: [
            { label: "Лидер", x: 50, y: 42, hot: true },
            { label: "«Стража»", x: 28, y: 30 },
            { label: "Финансы", x: 72, y: 30 },
            { label: "Вербовка", x: 30, y: 66 },
            { label: "Изоляция", x: 70, y: 66 },
          ],
          edges: [[0, 1], [0, 2], [0, 3], [0, 4], [1, 3], [2, 4]],
          accent: "#d92828",
        }}
      />

      <Composition
        id="IntroSequence"
        component={IntroSequence}
        durationInFrames={1620}
        fps={30}
        width={W}
        height={H}
        defaultProps={{ accent: "#d92828" }}
      />

      <Composition
        id="IntroFootage"
        component={IntroFootage}
        durationInFrames={1790}
        fps={30}
        width={W}
        height={H}
        defaultProps={{ accent: "#d92828" }}
      />

      <Composition
        id="PhotoZoom"
        component={PhotoZoom}
        durationInFrames={300}
        fps={30}
        width={W}
        height={H}
        calculateMetadata={({ props }: any) => (props?.durationInFrames ? { durationInFrames: props.durationInFrames } : {})}
        defaultProps={{ img: "", dir: "in" }}
      />
      <Composition
        id="DNAHelix3D"
        component={DNAHelix3D}
        durationInFrames={300}
        fps={30}
        width={W}
        height={H}
        calculateMetadata={({ props }: any) => (props?.durationInFrames ? { durationInFrames: props.durationInFrames } : {})}
        defaultProps={{ title: "ДНК", sub: "код жизни", accent: "#1fa48a" }}
      />
      <Composition id="HomininTree" component={HomininTree} durationInFrames={300} fps={30} width={W} height={H}
        calculateMetadata={({ props }: any) => (props?.durationInFrames ? { durationInFrames: props.durationInFrames } : {})}
        defaultProps={{ title: "ДЕРЕВО ЛЮДЕЙ", accent: "#1fa48a" }} />
      <Composition id="PopulationCollapse" component={PopulationCollapse} durationInFrames={300} fps={30} width={W} height={H}
        calculateMetadata={({ props }: any) => (props?.durationInFrames ? { durationInFrames: props.durationInFrames } : {})}
        defaultProps={{ title: "КРАХ ЧЕЛОВЕЧЕСТВА", bigNumber: "1 280", sub: "99% предков исчезло", accent: "#1fa48a" }} />
      <Composition id="ParasitePuppet" component={ParasitePuppet} durationInFrames={300} fps={30} width={W} height={H}
        calculateMetadata={({ props }: any) => (props?.durationInFrames ? { durationInFrames: props.durationInFrames } : {})}
        defaultProps={{ title: "КУКЛОВОД", sub: "гриб управляет телом", accent: "#8fd14f" }} />
      <Composition id="VirusGenome" component={VirusGenome} durationInFrames={300} fps={30} width={W} height={H}
        calculateMetadata={({ props }: any) => (props?.durationInFrames ? { durationInFrames: props.durationInFrames } : {})}
        defaultProps={{ title: "8% ТЫ — ВИРУС", sub: "древние ретровирусы в ДНК", accent: "#1fa48a" }} />
      <Composition id="CRISPRCut" component={CRISPRCut} durationInFrames={300} fps={30} width={W} height={H}
        calculateMetadata={({ props }: any) => (props?.durationInFrames ? { durationInFrames: props.durationInFrames } : {})}
        defaultProps={{ title: "CRISPR", sub: "редактирование гена", accent: "#1fa48a" }} />
      <Composition id="CordycepsTakeover3D" component={CordycepsTakeover3D} durationInFrames={540} fps={30} width={W} height={H}
        calculateMetadata={({ props }: any) => (props?.durationInFrames ? { durationInFrames: props.durationInFrames } : {})}
        defaultProps={{ title: "ЗАХВАТ ТЕЛА", sub: "гриб-кордицепс превращает муравья в зомби", accent: "#8fd14f" }} />
      <Composition id="PhotoMontage" component={PhotoMontage} durationInFrames={180} fps={30} width={W} height={H}
        calculateMetadata={({ props }: any) => (props?.durationInFrames ? { durationInFrames: props.durationInFrames } : {})}
        defaultProps={{ images: [], caption: "", accent: "#1fa48a" }} />
      <Composition id="EugenicsRegistry" component={EugenicsRegistry} durationInFrames={300} fps={30} width={W} height={H}
        calculateMetadata={({ props }: any) => (props?.durationInFrames ? { durationInFrames: props.durationInFrames } : {})}
        defaultProps={{ title: "ПРИНУДИТЕЛЬНАЯ СТЕРИЛИЗАЦИЯ", counter: "63 000", stamp: "СТЕРИЛИЗОВАН", accent: "#d92828" }} />
      <Composition id="TuskErosion" component={TuskErosion} durationInFrames={300} fps={30} width={W} height={H}
        calculateMetadata={({ props }: any) => (props?.durationInFrames ? { durationInFrames: props.durationInFrames } : {})}
        defaultProps={{ title: "БИВНИ ИСЧЕЗАЮТ", sub: "трофейная охота → обратная эволюция", accent: "#1fa48a" }} />
      <Composition id="RatioViz17" component={RatioViz17} durationInFrames={270} fps={30} width={W} height={H}
        calculateMetadata={({ props }: any) => (props?.durationInFrames ? { durationInFrames: props.durationInFrames } : {})}
        defaultProps={{ title: "17 ЖЕНЩИН НА 1 МУЖЧИНУ", ratio: "17 : 1", women: 17, accent: "#1fa48a" }} />
      <Composition id="PrionBrain" component={PrionBrain} durationInFrames={270} fps={30} width={W} height={H}
        calculateMetadata={({ props }: any) => (props?.durationInFrames ? { durationInFrames: props.durationInFrames } : {})}
        defaultProps={{ title: "КУРУ", sub: "прионы превращают мозг в губку", accent: "#1fa48a" }} />
      <Composition id="LastHuman" component={LastHuman} durationInFrames={270} fps={30} width={W} height={H}
        calculateMetadata={({ props }: any) => (props?.durationInFrames ? { durationInFrames: props.durationInFrames } : {})}
        defaultProps={{ title: "МЫ ОСТАЛИСЬ ОДНИ", sub: "потому что были опаснее", accent: "#1fa48a" }} />
      <Composition id="Mascot" component={Mascot} durationInFrames={180} fps={30} width={W} height={H}
        calculateMetadata={({ props }: any) => (props?.durationInFrames ? { durationInFrames: props.durationInFrames } : {})}
        defaultProps={{ position: "left", scale: 0.9, jitter: 1, accent: "#e2080d" }} />
      <Composition id="GTARecordsStage" component={GTARecordsStage} durationInFrames={1600} fps={30} width={W} height={H}
        calculateMetadata={({ props }: any) => (props?.durationInFrames ? { durationInFrames: props.durationInFrames } : {})}
        defaultProps={{ accent: "#ff2d78", accent2: "#25e0c8", segments: [] }} />
      <Composition id="BigfootHunt" component={BigfootHunt} durationInFrames={2300} fps={30} width={W} height={H}
        calculateMetadata={({ props }: any) => (props?.durationInFrames ? { durationInFrames: props.durationInFrames } : {})}
        defaultProps={{ accent: "#8be04e", segments: [] }} />
      <Composition id="UFOScene" component={UFOScene} durationInFrames={1900} fps={30} width={W} height={H}
        calculateMetadata={({ props }: any) => (props?.durationInFrames ? { durationInFrames: props.durationInFrames } : {})}
        defaultProps={{ accent: "#5ef0c8", segments: [] }} />
      <Composition id="KurtajHack" component={KurtajHack} durationInFrames={2250} fps={30} width={W} height={H}
        calculateMetadata={({ props }: any) => (props?.durationInFrames ? { durationInFrames: props.durationInFrames } : {})}
        defaultProps={{ accent: "#37e0a0", segments: [] }} />
      <Composition id="MascotOutro" component={MascotOutro} durationInFrames={640} fps={30} width={W} height={H}
        calculateMetadata={({ props }: any) => (props?.durationInFrames ? { durationInFrames: props.durationInFrames } : {})}
        defaultProps={{ accent: "#ff2d55", segments: [] }} />
      <Composition id="PortraitQuote" component={PortraitQuote} durationInFrames={180} fps={30} width={W} height={H}
        calculateMetadata={({ props }: any) => (props?.durationInFrames ? { durationInFrames: props.durationInFrames } : {})}
        defaultProps={{ photo: "portrait/katzenberg.jpg", accent: "#d9282f" }} />
      <Composition id="CancelledDossier" component={CancelledDossier} durationInFrames={240} fps={30} width={W} height={H}
        calculateMetadata={({ props }: any) => (props?.durationInFrames ? { durationInFrames: props.durationInFrames } : {})}
        defaultProps={{ videoSrc: "videos/dw_boo.mp4", accent: "#d9282f" }} />
      <Composition id="FilmStrip" component={FilmStrip} durationInFrames={210} fps={30} width={W} height={H}
        calculateMetadata={({ props }: any) => (props?.durationInFrames ? { durationInFrames: props.durationInFrames } : {})}
        defaultProps={{ videoSrc: "videos/dw_boo.mp4", accent: "#d9282f" }} />
      <Composition id="DramaFreeze" component={DramaFreeze} durationInFrames={180} fps={30} width={W} height={H}
        calculateMetadata={({ props }: any) => (props?.durationInFrames ? { durationInFrames: props.durationInFrames } : {})}
        defaultProps={{ videoSrc: "videos/dw_boo.mp4", accent: "#d9282f" }} />
      <Composition id="MoneyCounter" component={MoneyCounter} durationInFrames={210} fps={30} width={W} height={H}
        calculateMetadata={({ props }: any) => (props?.durationInFrames ? { durationInFrames: props.durationInFrames } : {})}
        defaultProps={{ accent: "#d9282f" }} />
      <Composition id="NewsHeadline" component={NewsHeadline} durationInFrames={210} fps={30} width={W} height={H}
        calculateMetadata={({ props }: any) => (props?.durationInFrames ? { durationInFrames: props.durationInFrames } : {})}
        defaultProps={{ accent: "#d9282f" }} />
      <Composition id="QuoteCardDW" component={QuoteCardDW} durationInFrames={210} fps={30} width={W} height={H}
        calculateMetadata={({ props }: any) => (props?.durationInFrames ? { durationInFrames: props.durationInFrames } : {})}
        defaultProps={{ accent: "#d9282f" }} />
      <Composition id="UncannyCGI" component={UncannyCGI} durationInFrames={180} fps={30} width={W} height={H}
        calculateMetadata={({ props }: any) => (props?.durationInFrames ? { durationInFrames: props.durationInFrames } : {})}
        defaultProps={{ videoSrc: "videos/dw_boo.mp4", accent: "#7fd14f" }} />
      <Composition id="SplitCompare" component={SplitCompare} durationInFrames={200} fps={30} width={W} height={H}
        calculateMetadata={({ props }: any) => (props?.durationInFrames ? { durationInFrames: props.durationInFrames } : {})}
        defaultProps={{ videoSrc: "videos/dw_boo.mp4", accent: "#d9282f" }} />
      <Composition id="StudioTimeline" component={StudioTimeline} durationInFrames={240} fps={30} width={W} height={H}
        calculateMetadata={({ props }: any) => (props?.durationInFrames ? { durationInFrames: props.durationInFrames } : {})}
        defaultProps={{ accent: "#d9282f" }} />
      <Composition id="GlitchLeak" component={GlitchLeak} durationInFrames={180} fps={30} width={W} height={H}
        calculateMetadata={({ props }: any) => (props?.durationInFrames ? { durationInFrames: props.durationInFrames } : {})}
        defaultProps={{ videoSrc: "videos/dw_boo.mp4", accent: "#d9282f" }} />
      <Composition id="RedditThread" component={RedditThread} durationInFrames={160} fps={30} width={W} height={H}
        calculateMetadata={({ props }: any) => (props?.durationInFrames ? { durationInFrames: props.durationInFrames } : {})}
        defaultProps={{ subreddit: "r/nosleep", title: "Здесь всё правда. Не нарушайте правило.", author: "u/anonymous", upvotes: 48200, comments: "10.6k", awardText: "ХУДОЖКА", accent: "#ff4500", caption: "Сабреддит, где каждую историю читают как реальную." }} />
      <Composition id="HexCipher" component={HexCipher} durationInFrames={170} fps={30} width={W} height={H}
        calculateMetadata={({ props }: any) => (props?.durationInFrames ? { durationInFrames: props.durationInFrames } : {})}
        defaultProps={{ subreddit: "r/A858DE45F56D9BC9", decoded: "WE CANNOT DISCLOSE THE PURPOSE", label: "ФРАГМЕНТ ДЕКОДИРОВАН", status: "Проект A858 завершён.", caption: "Тысячи блоков кода. Расшифрована — горстка." }} />
      <Composition id="LiminalSpace" component={LiminalSpace} durationInFrames={160} fps={30} width={W} height={H}
        calculateMetadata={({ props }: any) => (props?.durationInFrames ? { durationInFrames: props.durationInFrames } : {})}
        defaultProps={{ title: "BACKROOMS", sub: "УРОВЕНЬ 0", caption: "Одна фотография, ставшая целой мифологией." }} />
      <Composition id="DocuFrame" component={DocuFrame} durationInFrames={150} fps={30} width={W} height={H}
        calculateMetadata={({ props }: any) => (props?.durationInFrames ? { durationInFrames: props.durationInFrames } : {})}
        defaultProps={{ imgSrc: "real/scene_019.jpg", kicker: "АРХИВ", title: "Камера Нельсона Манделы, Роббен-Айленд", source: "Wikimedia Commons" }} />
      <Composition id="GangesGhats" component={GangesGhats} durationInFrames={170} fps={30} width={W} height={H}
        calculateMetadata={({ props }: any) => (props?.durationInFrames ? { durationInFrames: props.durationInFrames } : {})}
        defaultProps={{ kicker: "ВАРАНАСИ", title: "ГОРОД, ГДЕ ГОРЯТ КОСТРЫ", accent: "#ff8a2a", caption: "Древнейший живой город планеты, где смерть — это бизнес." }} />
      <Composition id="NagaUnderworld" component={NagaUnderworld} durationInFrames={190} fps={30} width={W} height={H}
        calculateMetadata={({ props }: any) => (props?.durationInFrames ? { durationInFrames: props.durationInFrames } : {})}
        defaultProps={{ kicker: "ПАТАЛА", title: "ПОДЗЕМНЫЙ МИР ЗМЕЕЛЮДЕЙ", accent: "#e8b84a", caption: "Семь миров под землёй, где правят наги." }} />
      <Composition id="SkeletonLake" component={SkeletonLake} durationInFrames={180} fps={30} width={W} height={H}
        calculateMetadata={({ props }: any) => (props?.durationInFrames ? { durationInFrames: props.durationInFrames } : {})}
        defaultProps={{ kicker: "РУПКУНД", title: "ОЗЕРО ИЗ СОТЕН СКЕЛЕТОВ", accent: "#8fd3e6", caption: "ДНК показала: скелеты — из трёх разных эпох." }} />
      <Composition id="FortCurse" component={FortCurse} durationInFrames={180} fps={30} width={W} height={H}
        calculateMetadata={({ props }: any) => (props?.durationInFrames ? { durationInFrames: props.durationInFrames } : {})}
        defaultProps={{ kicker: "ФОРТ БХАНГАРХ", title: "ОФИЦИАЛЬНО ПРОКЛЯТОЕ МЕСТО", accent: "#d98a3a", caption: "Единственный памятник Индии с запретом входа после заката." }} />
      <Composition id="VaultDoorB" component={VaultDoorB} durationInFrames={185} fps={30} width={W} height={H}
        calculateMetadata={({ props }: any) => (props?.durationInFrames ? { durationInFrames: props.durationInFrames } : {})}
        defaultProps={{ kicker: "ПАДМАНАБХАСВАМИ", title: "ДВЕРЬ, КОТОРУЮ НЕЛЬЗЯ ОТКРЫВАТЬ", accent: "#e3b23c", caption: "Пять комнат — 22 миллиарда. Шестая осталась закрытой." }} />
      <Composition id="ThugStrangler" component={ThugStrangler} durationInFrames={185} fps={30} width={W} height={H}
        calculateMetadata={({ props }: any) => (props?.durationInFrames ? { durationInFrames: props.durationInFrames } : {})}
        defaultProps={{ kicker: "ТХАГИ", title: "КУЛЬТ ДУШИТЕЛЕЙ БОГИНИ КАЛИ", accent: "#e5c53a", caption: "Убивали не ради денег — ради богини." }} />
      <Composition id="KumbhaMela" component={KumbhaMela} durationInFrames={185} fps={30} width={W} height={H}
        calculateMetadata={({ props }: any) => (props?.durationInFrames ? { durationInFrames: props.durationInFrames } : {})}
        defaultProps={{ kicker: "КУМБХА-МЕЛА", title: "КРУПНЕЙШЕЕ СОБРАНИЕ ЛЮДЕЙ НА ЗЕМЛЕ", countText: "120 000 000", countLabel: "паломников в одном месте", accent: "#ffb44a", caption: "Событие такого масштаба, что его видно из космоса." }} />
      <Composition id="RatTemple" component={RatTemple} durationInFrames={180} fps={30} width={W} height={H}
        calculateMetadata={({ props }: any) => (props?.durationInFrames ? { durationInFrames: props.durationInFrames } : {})}
        defaultProps={{ kicker: "ХРАМ КАРНИ МАТА", title: "25 ТЫСЯЧ СВЯЩЕННЫХ КРЫС", countText: "25 000", countLabel: "священных крыс в храме", accent: "#c9a24a", caption: "Увидеть белую крысу — величайшая удача." }} />
      <Composition id="TwinVillage" component={TwinVillage} durationInFrames={180} fps={30} width={W} height={H}
        calculateMetadata={({ props }: any) => (props?.durationInFrames ? { durationInFrames: props.durationInFrames } : {})}
        defaultProps={{ kicker: "КОДИНХИ", title: "ДЕРЕВНЯ БЛИЗНЕЦОВ", countText: "400", countLabel: "пар близнецов", multiplier: "×6 среднемировой нормы", accent: "#6fd0c8", caption: "Генетики не нашли объяснения." }} />
      <Composition id="BirdFall" component={BirdFall} durationInFrames={180} fps={30} width={W} height={H}
        calculateMetadata={({ props }: any) => (props?.durationInFrames ? { durationInFrames: props.durationInFrames } : {})}
        defaultProps={{ kicker: "ДЖАТИНГА", title: "ДЕРЕВНЯ, ГДЕ ПТИЦЫ ПАДАЮТ С НЕБА", strip: "полоса 1,5 км × 200 м", accent: "#7fa8d8", caption: "Огни деревни сбивают птицам природный компас." }} />
      <Composition id="GuruDossier" component={GuruDossier} durationInFrames={185} fps={30} width={W} height={H}
        calculateMetadata={({ props }: any) => (props?.durationInFrames ? { durationInFrames: props.durationInFrames } : {})}
        defaultProps={{ kicker: "ГУРУ-ПРЕСТУПНИКИ", name: "«БОГОЧЕЛОВЕК» ПОД СУДОМ", followers: "миллионы последователей", verdict: "ПОЖИЗНЕННОЕ ЗАКЛЮЧЕНИЕ", charge: "насилие · мошенничество", accent: "#d24a3a", caption: "За белыми одеждами — бездна насилия." }} />
      <Composition id="KarniCurse" component={KarniCurse} durationInFrames={478} fps={30} width={W} height={H}
        calculateMetadata={({ props }: any) => (props?.durationInFrames ? { durationInFrames: props.durationInFrames } : {})}
        defaultProps={{ kicker: "ЛЕГЕНДА КАРНИ МАТЫ", title: "ПРОКЛЯТИЕ БОГА СМЕРТИ", caption: "Род Карни после смерти рождается крысами — минуя власть Ямы, а потом снова людьми" }} />
      <Composition id="SentinelIsland" component={SentinelIsland} durationInFrames={185} fps={30} width={W} height={H}
        calculateMetadata={({ props }: any) => (props?.durationInFrames ? { durationInFrames: props.durationInFrames } : {})}
        defaultProps={{ kicker: "СЕВЕРНЫЙ СЕНТИНЕЛ", title: "ОСТРОВ, КУДА НЕЛЬЗЯ СТУПАТЬ", bufferText: "запретная зона · 5 км буфер", accent: "#e0483a", caption: "Последнее неконтактное племя планеты." }} />
      <Composition id="CrowdSilhouette" component={CrowdSilhouette} durationInFrames={190} fps={30} width={W} height={H}
        calculateMetadata={({ props }: any) => (props?.durationInFrames ? { durationInFrames: props.durationInFrames } : {})}
        defaultProps={{ kicker: "ИНДИЯ", title: "1,4 МИЛЛИАРДА ЧЕЛОВЕК", countText: "1 400 000 000", countLabel: "человек", stats: [{ value: "22", label: "официальных языка" }, { value: "29", label: "штатов-«стран»" }], accent: "#d24a2a", light: true, caption: "Каждый штат — по сути отдельная страна." }} />
      <Composition id="EnumShowcase" component={EnumShowcase} durationInFrames={180} fps={30} width={W} height={H}
        calculateMetadata={({ props }: any) => (props?.durationInFrames ? { durationInFrames: props.durationInFrames } : {})}
        defaultProps={{ kicker: "АЮРВЕДА", title: "ТЫСЯЧЕЛЕТНИЕ ЗНАНИЯ О РАСТЕНИЯХ", items: [{ img: "enum/turmeric.jpg", label: "КУРКУМА", sub: "противовоспалительное" }, { img: "enum/neem.jpg", label: "НИМ", sub: "антисептик" }, { img: "enum/ashwagandha.jpg", label: "АШВАГАНДА", sub: "адаптоген" }], accent: "#e0a52a", caption: "Многие подтверждены современной фармакологией." }} />
    </>
  );
};
