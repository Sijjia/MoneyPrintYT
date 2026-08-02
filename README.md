# 🧊 MoneyPrintYT — автоматизация YouTube-роликов «Айсберг»

Пайплайн производства русскоязычных документальных роликов формата **«айсберг»** (спуск по 4 уровням глубины темы) для канала [@WebikStudio](https://www.youtube.com/@WebikStudio). От идеи до готового монтажа в Adobe Premiere: сценарий → озвучка → сборка → медиа → графика → вставки → SFX → музыка.

> **Стек:** Python + Pymiere (управление Premiere) + Remotion (моушн-графика/оверлеи) + Lumean (TTS/SFX/музыка через ElevenLabs) + OpenRouter (LLM) + yt-dlp / Pexels / Pixabay / Wikimedia (медиа).

---

## 📂 Структура репозитория

```
automotization-youtube/
├── webik-pipeline(v2)/     ← АКТИВНАЯ версия (всё здесь)
│   ├── webik.py            — CLI, стадии 1-5 (концепт→сценарий→сцены→ассеты→сборка)
│   ├── core/               — config (.env), логи, исключения
│   ├── services/           — llm, tts (lumean), stocks (pexels/pixabay/youtube/wikimedia),
│   │                         overlays (render_bridge), premiere (overlay_placer), premiere_template
│   ├── stages/             — stage_01_concept … stage_05_assembly
│   ├── remotion/           — React-компоненты оверлеев (Timeline, Globe3D, IcebergRecap, …)
│   ├── tests/              — сценарии «премиум-финиша» (вставки, графика, музыка, gap-fill) ← см. ниже
│   ├── projects/<slug>/    — данные ролика: scenes.json, alignment, assets/, project_template.prproj
│   ├── templates/          — Apocalypse .prproj (шаблон таймлайна — КОПИРУЕТСЯ, оригинал не трогать)
│   └── ASSEMBLY.md         — порядок сборки конкретного ролика
├── webik-pipeline/         — старая v1 (архив)
├── WEBIK_PIPELINE.md       — исходное техзадание
└── docs/
```

---

## ⚙️ Установка

```bash
git clone https://github.com/Sijjia/MoneyPrintYT.git
cd MoneyPrintYT/"webik-pipeline(v2)"

python -m venv .venv
# Windows: .venv\Scripts\activate  |  macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cd remotion && npm install && cd ..        # Remotion для графики

cp .env.example .env                        # заполнить ключи (см. ниже)
python webik.py doctor                       # проверка окружения
```

**Ключи в `.env`** (файл в `.gitignore` — секреты НЕ коммитятся):
`OPENROUTER_API_KEY`, `LUMEAN_API_KEY`, `PEXELS_API_KEY`, `PIXABAY_API_KEY`, `YT_COOKIES_FILE`,
`LLM_MODEL=anthropic/claude-sonnet-4.5`, `LLM_MODEL_CHEAP=google/gemini-2.5-flash`,
`TTS_PROVIDER=lumean`, диктор Lumean `M1CSR3PJBsfWU6ZquG3C`.

Требуется установленный **Adobe Premiere Pro** с открытой панелью Pymiere (скрипты управляют живым Premiere).

---

## 🎬 Полный процесс производства ролика

### 0. Сценарий и озвучка
```bash
python webik.py run --topic "тема ролика"     # стадии 1-4: концепт → сценарий → сцены → ассеты
```
- Стиль сценария: чистый, без дешёвых вставок/манерных переходов/ложных концовок; чистый обрыв темы + `[пауза Nс]`. Между «Уровень N» и темой — БЕЗ подытога.
- LLM через OpenRouter: `sonnet-4.5` на outline+сценарий, `gemini-2.5-flash` на механику (~<$1/ролик).
- Озвучка — **Lumean** (`services/tts/lumean.py`, eleven_v3, текст целиком, паузы `[long pause]`, нативный alignment). Ударения — `services/tts/pronunciation.py`. **Паузы не переборщить.**

### 1. Сборка тела
```bash
python webik.py assemble                       # стадия 5: тело V3, плашки V4, машинка A4, голос A1
```
- Шаблон Apocalypse .prproj — всегда КОПИЯ (`project_template.prproj`), оригинал не трогать.
- **Сразу проверить чёрные дыры на V3** — тело собирается дырявым; начала тем и mid-body бывают пустыми.

### 2. Медиа (реальное, тематическое, РАЗНОЕ)
- Только реальное по теме: архив-фото/видео, фото лидеров (фейр-юз), реальные события. Никакого абстрактного стока.
- Для разнообразия — тематический **Pexels** с разными атмосферными запросами (собор/зима/Альпы/свечи…): `tests/tail_pexels_media.py`.
- Фото → зум ТОЛЬКО Remotion `PhotoZoom` (ffmpeg zoompan трясётся): `tests/photozoom_render.py` + `photozoom_swap.py`.

### 3. Графика (V8, Remotion) — реалистичная, оригинальная
- Детектор/режиссёр оверлеев → рендер (`services/overlays/render_bridge.py`) → расстановка (`services/premiere/overlay_placer.py`).
- Реалистичная моушн-графика (эталон `remotion/src/IcebergRecap.tsx`). Типы разнотипить, дубли не ставить. Рекап айсберга = `IcebergRecap`, страны = `Globe3D`.

### 4. Вставки кино/аниме/мультик (слой V7)
```bash
python tests/anime_director.py     # sonnet выбирает КУЛЬТОВЫЕ моменты по смыслу
python tests/v7_download.py        # скачивание + DNxHR по длине сцены
python tests/v7_place.py           # расстановка на V7 (тело V3 не трогаем)
```
- Узнаваемое (Breaking Bad/Wolf/Death Note/Midsommar/2001), 8-18с, **уникальные источники**, по СМЫСЛУ. Не реакшн-мемы.
- **Флор:** никогда над убийствами/трупами/пытками. Плавный переход в существующую анимацию — `tests/v7_scene011_transition.py` (кроссдиссолв).

### 5. SFX (A5/A6) + машинка (A4)
- Lumean SFX по описанию (вуш/тик/удар/ревил, без восходящего swoosh): `tests/lumean_sfx_pool.py` → `sfx_choreograph.py` (по битам, тихо 0.12, ротация).

### 6. Музыка (по явной просьбе)
```bash
bash tests/build_level_music.sh    # хор по 4 уровням + вшитый даккинг → A2
```
- Сакральный **церковный хор** «Ужасы религий» (Lumean music_v2), прогрессия L1→L4 (мрачнее ко дну), даккинг под голос (ffmpeg `sidechaincompress` от голоса), ~-20 LUFS. NCS-пак автора не трогать.

---

## ⚠️ Правила эксплуатации (грабли — соблюдать)

1. **НИКОГДА не запускать два Pymiere-скрипта параллельно** — гонка за Premiere ломает стейт. Всё, что трогает Premiere, — по очереди. Скачка/рендер (без Premiere) — можно параллельно.
2. **Один нетронутый бэкап** проекта; не жонглировать openDocument/save/cp. Спасение — авто-сейвы `<project>/Adobe Premiere Pro Auto-Save/*.prproj`.
3. **Кэш offline медиа**: при замене файла давать НОВОЕ имя (Premiere держит старый projectItem по имени).
4. **Вставки — на V7 (overlay)**, не врезать в V3 (удаление врезанного = чёрные дыры).
5. **yt-dlp**: `socket_timeout` (виснет на метаданных); использовать `fetch_robust`, не `auto_archive_clip`.
6. **DNxHR** для медиа/вставок (h264 long-GOP дёргается при композитинге); CFR.
7. **Реализм всегда**; уместность строго (числа/имена/места сверять с закадром).

---

## 🔒 Секреты и медиа
`.env`, все API-ключи, скачанные медиа, .prproj-проекты и рендеры — в `.gitignore`. В репозиторий идёт только код и документация.
