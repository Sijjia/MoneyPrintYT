# 🧊 WEBIK PIPELINE — Техническое задание

**Версия:** 1.0
**Дата:** 2026-04-26
**Автор ТЗ:** Webik (владелец канала) + AI assistant
**Цель документа:** Полностью описать систему автоматизированного производства YouTube-видео в формате «айсберг» для канала [@WebikStudio](https://www.youtube.com/@WebikStudio). По этому документу разработчик (или сам владелец через Claude Code / Cursor) может реализовать пайплайн с нуля.

---

## 📑 Содержание

1. [О канале и контексте](#1-о-канале-и-контексте)
2. [Формат контента: что такое «айсберг-видео»](#2-формат-контента)
3. [Стилевые пресеты под жанры](#3-стилевые-пресеты)
4. [Общая архитектура пайплайна](#4-общая-архитектура)
5. [7 контрольных точек (CHECKPOINTS)](#5-контрольные-точки)
6. [Стек технологий и API](#6-стек-технологий)
7. [Структура проекта](#7-структура-проекта)
8. [Этапы разработки (по неделям)](#8-этапы-разработки)
9. [Подробное описание каждого STAGE](#9-описание-stages)
10. [Установка и запуск](#10-установка-и-запуск)
11. [CLI-команды](#11-cli-команды)
12. [Telegram-бот](#12-telegram-бот)
13. [Список плагинов Premiere](#13-плагины-premiere)
14. [.mogrt шаблоны](#14-mogrt-шаблоны)
15. [Бюджет и стоимость](#15-бюджет)
16. [Чек-лист готовности](#16-чек-лист)

---

## 1. О канале и контексте

### Канал
- **Название:** Webik
- **Хэндл:** @WebikStudio
- **URL:** https://www.youtube.com/@WebikStudio
- **Channel ID:** UCRN8D83V59kE9GAVFU1P3Bg
- **Язык:** русский
- **Целевая аудитория:** русскоязычная, 14-35 лет, любители тёмного контента, конспирологии, истории, мистики
- **Маскот:** капибара (используется в брендинге и интро/аутро)
- **Основной соц-канал:** Telegram (CTA в каждом видео)

### Авторы
- **Webik** — диктор, продюсер, владелец канала
- **Брат Webik'а** — монтажёр (планируется заменить пайплайном на 80%, оставить ему финальный QA)

### Референсы (по убыванию важности)
1. **NetCore** (https://www.youtube.com/@netcore) — главный референс. Русскоязычный, формат «айсберг», тёмная эстетика, мужской диктор, минимум AI-видео, максимум статичных картинок с движением камеры.
2. **The Why Files** (англоязычный) — структура повествования
3. **Wendigoon** (англоязычный) — глубина погружения в темы

### Цель
Делать видео **минимум на уровне NetCore**, в идеале — превзойти их за счёт:
- Скорости (2-3 дня вместо 1-2 недель)
- Качества картинки (3D-камера на каждом фото, AI-генерация уникальных кадров)
- Стилевой вариативности (разные пресеты под разные темы)
- Постоянства бренда (фирменные переходы, шрифты, голос)

---

## 2. Формат контента

### Что такое «айсберг-видео»

Структурированное видео 12-20 минут, разделённое на **4 уровня** по метафоре айсберга:

```
🧊 УРОВЕНЬ 1 — Верхушка айсберга      (общеизвестные факты, но интересные детали)
🌊 УРОВЕНЬ 2 — Водная гладь            (уже менее известное, любопытное)
🕳️ УРОВЕНЬ 3 — Погружение              (шокирующее, малоизвестное)
🕯️ УРОВЕНЬ 4 — Бездна                  (самое тёмное, секретное, страшное)
```

Каждый уровень содержит **3-5 тем**. Каждая тема — отдельный мини-сюжет на 1-3 минуты с заголовком.

### Темы канала (примеры реальных сценариев Webik'а)

Канал делает айсберги на широкий спектр тем — это важно, потому что **визуальный стиль должен меняться** под тему:

| Сценарий | Тематика | Подходящий пресет |
|----------|----------|-------------------|
| Корея | мистика, шаманизм, K-pop, секты, призраки | **MYSTIC** |
| Эксперименты на людях | MK-Ultra, Менгеле, Отряд 731, радиация | **ARCHIVE** |
| Китай | Foxconn, гуаньси, цифровое рабство, TikTok | **CIPHER** |
| Апокалиптические пророчества | Йеллоустоун, Кэррингтон, парадокс Ферми | **COSMIC** |
| История секса | Камасутра, Средневековье, евгеника, культы | **MYSTIC + ARCHIVE** |
| Эпштейн (планируется) | расследования, документы, заговоры | **ARCHIVE + SHADOW** |

### Структура каждого видео

```
[ИНТРО]                     0:00 — 0:30   (хук + анонс темы)
[ОТКРЫВАЮЩИЙ STING]         0:30 — 0:35   (логотип Webik с капибарой)
[УРОВЕНЬ 1 КАРТОЧКА]        0:35 — 0:42
  [Тема 1.1]                0:42 — 2:30
  [Тема 1.2]                2:30 — 4:00
  ...
[ПЕРЕХОД "ПОГРУЖЕНИЕ"]      4:00 — 4:05   (фирменный dive transition)
[УРОВЕНЬ 2 КАРТОЧКА]        4:05 — 4:12
  ...
[УРОВЕНЬ 4: БЕЗДНА]         12:00 — 18:00 (самые тёмные темы, SHADOW мод)
[ЗАКЛЮЧЕНИЕ]                18:00 — 19:00 (философская "затяжка")
[CTA + AUTRO]               19:00 — 19:30 (Telegram, лайк, подписка)
```

### Голос диктора (Webik)

- Голос мужской, ровный, мистический
- Озвучивается через **ElevenLabs Multilingual v2** (у Webik'а есть API-ключ)
- Один и тот же `voice_id` во ВСЕХ роликах — это узнаваемость канала
- Post-processing: лёгкий EQ (+2dB на 80-120 Hz, +1dB на 3kHz), reverb на ключевых драматических фразах
- Поддержка маркеров пауз: `[пауза 1.5с]` в сценарии → ElevenLabs делает паузу

---

## 3. Стилевые пресеты

Пайплайн поддерживает **5 пресетов**, которые применяются автоматически в зависимости от темы. LLM на этапе scenes.json определяет нужный пресет, дальше ассеты генерятся в этом стиле, плагины Premiere накладываются автоматически.

### 🌫️ MYSTIC — мистика, паранормальное, секты, призраки
- **Палитра:** глубокий фиолетовый (#2D1B4E), холодный синий (#1B3A5C), туманный серый (#7A8C99)
- **AI-картинки теги:** `dark folklore, fog, candle light, occult atmosphere, oriental mystery, low key lighting`
- **Переходы:** дым, чернильные кляксы, fade-to-black + reverb tail
- **Музыка:** этнические инструменты (эрху, тайко, гусли) + low drone
- **SFX:** колокола, шёпот, скрип дерева
- **Шрифт:** с засечками (Cormorant Garamond, EB Garamond)
- **LUT:** «Mystic Cold» (синие тени, золотистые мидтоны, низкая насыщенность)
- **Применимо к:** Корея, секты, шаманизм, городские легенды, паранормальное

### 📜 ARCHIVE — эксперименты, история, рассекреченное, война
- **Палитра:** сепия (#704214), выцветший зелёный (#52614A), тёмно-коричневый (#3D2817)
- **AI-картинки теги:** `1950s declassified document, vintage photograph, film grain, faded archive, kodak ektachrome`
- **Переходы:** киноплёнка с царапинами, проектор, 8mm light leaks, перфорация плёнки
- **Музыка:** аналоговые записи с шорохами, военные радиопередачи, печатная машинка
- **SFX:** проектор, печатная машинка, радиопомехи, штамп «TOP SECRET»
- **Шрифт:** Courier New, IBM Plex Mono, машинописный
- **LUT:** «Vintage 8mm» (FilmConvert Nitrate)
- **Применимо к:** MK-Ultra, эксперименты, Отряд 731, исторические события, война, рассекреченные документы, **Эпштейн**

### 💻 CIPHER — современный мир, IT, цифровая антиутопия
- **Палитра:** холодный neon-cyan (#00F0FF), красные акценты (#FF003C), чёрный (#0A0A0A)
- **AI-картинки теги:** `cyberpunk surveillance, neon dystopia, data center, oppressive megacity, cctv aesthetic`
- **Переходы:** глитчи, datamosh, scanline, RGB-сдвиг, code-rain, pixel sort
- **Музыка:** индустриальный гул, modular synth, IDM, dark techno
- **SFX:** цифровые помехи, error-beep, dial-up, keyboard typing
- **Шрифт:** моноширинный Inter Tight, JetBrains Mono
- **LUT:** «Neon Dystopia» (теал-оранж экстремальный)
- **Применимо к:** Китай, TikTok, цифровое рабство, AI, корпорации, слежка

### 🌌 COSMIC — наука, физика, апокалипсис, экзистенция
- **Палитра:** глубокий чёрный (#000000), точечные белые звёзды, индиго (#1A0E3D)
- **AI-картинки теги:** `cosmic horror, deep space, quantum, scientific diagram, blackboard physics, hubble photography`
- **Переходы:** zoom-out до бесконечности, парсек-варп, частицы, гравитационная линза
- **Музыка:** суб-бас, white noise, протяжные хоралы (gregorian-style без слов), drone
- **SFX:** sub-drop, гул вселенной, помехи Voyager
- **Шрифт:** математический тонкий sans-serif (Inter Light, Geist)
- **LUT:** «Deep Space» (синие тени, контраст +30, dehaze)
- **Применимо к:** парадокс Ферми, ложный вакуум, апокалипсис, нанотехнологии, теории физики

### 🩸 SHADOW — модификатор для самых тёмных частей (4-й уровень)
**Не отдельный пресет, а оверлей** который накладывается поверх любого основного пресета на 4-м уровне айсберга или на самых драматических темах.
- **Дополнительная палитра:** аварийно-красный (#8B0000), один источник света
- **Переходы:** heartbeat-cut (резкий с ударом сердца), полицейская мигалка
- **SFX:** bass-drop, тишина 2 секунды после ключевой фразы
- **Эффект:** Vignette x2, легкий desaturate, contrast +15
- **Применимо к:** 4-й уровень любого айсберга, темы с убийствами/насилием/исчезновениями

### Логика выбора пресета (для LLM)

```
ЕСЛИ тема содержит [мистика, призраки, секты, шаманы, пророчества, паранормальное]:
    → MYSTIC

ЕСЛИ тема содержит [эксперимент, рассекречено, война, ЦРУ, КГБ, исторические документы]:
    → ARCHIVE

ЕСЛИ тема содержит [технологии, AI, корпорации, цифровое, slежка, интернет]:
    → CIPHER

ЕСЛИ тема содержит [физика, космос, наука, теория, гипотеза, апокалипсис]:
    → COSMIC

ЕСЛИ уровень == 4 ИЛИ тема содержит [убийство, исчезновение, насилие, культ, бездна]:
    → ДОБАВИТЬ SHADOW поверх основного

КОМБИНАЦИИ допустимы:
    - История секса → MYSTIC (древность) + ARCHIVE (новое время) + SHADOW (4 уровень)
    - Эпштейн → ARCHIVE + SHADOW
    - Корея → MYSTIC, 4 уровень MYSTIC + SHADOW
```

---

## 4. Общая архитектура

```
┌────────────────────────────────────────────────────────────────┐
│  webik.py  (CLI orchestrator + State Machine)                  │
│  - читает projects/<n>/state.json                           │
│  - запускает следующий нужный stage                            │
│  - после каждого stage → Telegram bot шлёт уведомление         │
│  - ждёт /approve или /revise <feedback>                        │
└─────────────────┬──────────────────────────────────────────────┘
                  │
   ┌──────────────┴──────────────┐
   │                             │
   ▼                             ▼
[State Machine]            [Telegram Bot]
   │                             │
   │   Для каждого checkpoint:
   │   - state.json: {stage, status, awaiting_approval, last_feedback}
   │   - Telegram пуш: «Stage 3 готов, посмотри scenes.json»
   │   - команды: /approve, /revise <текст>, /regen, /status
   │
   ▼
[7 STAGES — Python модули]
   │
   ├── stages/01_concept.py    → outline.json     (Claude API)
   ├── stages/02_script.py     → script.md        (Claude API)
   ├── stages/03_scenes.py     → scenes.json      (Claude API)
   ├── stages/04_assets.py     → assets/*         (parallel async)
   │     ├── voice (ElevenLabs)
   │     ├── words (WhisperX local)
   │     ├── images (Pexels/Unsplash + Flux fallback)
   │     ├── 3d_clips (Immersity AI / Depth Anything local)
   │     ├── ai_videos (Kling/Veo через fal.ai, только критичные)
   │     ├── music (Suno API)
   │     └── sfx (ElevenLabs SFX + Freesound)
   ├── stages/05_assemble.py   → project.prproj   (Pymiere → Premiere)
   ├── stages/06_export.py     → final.mp4 + thumb.jpg + meta.json
   └── stages/07_upload.py     → YouTube unlisted
```

### Принципы

1. **Каждый stage — отдельный скрипт.** Можно запустить отдельно: `python webik.py run-stage 4 --project epstein`
2. **Состояние — в `state.json`.** При сбое можно продолжить с последнего успешного шага.
3. **Все ассеты кэшируются.** Перегенерация только того что попросил пользователь.
4. **Параллелизм на 4-м stage.** Озвучка + картинки + музыка идут одновременно через `asyncio`.
5. **Telegram = главный UX.** Через бот можно одобрять, отправлять фидбек, смотреть прогресс.

---

## 5. Контрольные точки

Пайплайн останавливается **на 7 контрольных точках**. На каждой Webik получает уведомление в Telegram и должен либо одобрить (`/approve`), либо запросить переделку (`/revise <фидбек>`).

| # | Stage | Что готово | Файлы для проверки | Время выполнения |
|---|-------|------------|-------------------|------------------|
| 1 | Концепция | Структура айсберга (4 уровня × темы) | `outline.json` | ~30 сек |
| 2 | Сценарий | Полный текст видео | `script.md` | ~2-3 мин |
| 3 | Сцены | JSON с разбивкой + промтами + переходами | `scenes.json` | ~1-2 мин |
| 4 | Ассеты | Озвучка + картинки + 3D-клипы + музыка + SFX | HTML-галерея | ~20-40 мин |
| 5 | Сборка | Открытый Premiere-проект | `project.prproj` | ~5-10 мин |
| 6 | Экспорт | Финальный mp4 + превью + описание | `final.mp4`, `thumb.jpg` | ~10-15 мин |
| 7 | Загрузка | Видео на YouTube как unlisted | URL | ~5 мин |

### Поток на каждом checkpoint

```
[STAGE завершён]
    ↓
[state.json]: status = "awaiting_approval"
    ↓
[Telegram bot]: 
   "🧊 Stage 3 готов!
    ━━━━━━━━━━━━━━━
    Проект: epstein-iceberg
    Сгенерировано сцен: 87
    Пресет: ARCHIVE + SHADOW
    
    📁 Файлы:
    • scenes.json (открыть)
    • preview.html (превью)
    
    Команды:
    /approve — продолжить
    /revise <текст> — переделать с фидбеком
    /regen — перегенерировать без фидбека"
    ↓
[ОЖИДАНИЕ ОТВЕТА]
    ↓
   ┌──────────┬──────────┐
   │          │          │
[/approve] [/revise]  [/regen]
   ↓          ↓          ↓
   │      [то же stage] [то же stage]
   │       с feedback    без feedback
   │          ↓             ↓
   ▼      [возврат к ожиданию]
[следующий stage]
```

### Где Webik участвует руками (рекомендуется)

- **CHECKPOINT 1 (концепция):** обязательно проверить — это «скелет» видео, исправлять потом дорого
- **CHECKPOINT 2 (сценарий):** обязательно проверить — текст слышит зритель, ошибки тут видны на экране
- **CHECKPOINT 3 (scenes.json):** беглый просмотр, обычно одобряется сразу
- **CHECKPOINT 4 (ассеты):** проверить превью-галерею, отметить плохие картинки
- **CHECKPOINT 5 (Premiere):** **главный человеческий этап** — ритм, акценты, микро-правки. Тут ИИ автоматически собирает базу, но докручивать нужно руками.
- **CHECKPOINT 6 (превью):** одобрить/перегенерить — превью решает CTR
- **CHECKPOINT 7 (загрузка):** последняя проверка перед публикацией

---

## 6. Стек технологий

### LLM
- **Claude Sonnet 4.5** (Anthropic API) — основной мозг для сценариев, JSON-разбивки
  - Модель: `claude-sonnet-4-5`
  - Использование: stages 1, 2, 3, 6 (метаданные)
  - Эндпоинт: `https://api.anthropic.com/v1/messages`

### TTS (озвучка)
- **ElevenLabs Multilingual v2** — основной TTS
  - Модель: `eleven_multilingual_v2`
  - Voice ID: индивидуальный для Webik (склонировать или выбрать готовый)
  - Эндпоинт: `https://api.elevenlabs.io/v1/text-to-speech/{voice_id}`

### Транскрипция (для тайм-кодов)
- **WhisperX** (локально, GPU) — word-level timestamps
  - GitHub: https://github.com/m-bain/whisperX
  - Модель: `large-v3`

### Поиск стоковых изображений
- **Pexels API** (бесплатно) — https://www.pexels.com/api/
- **Unsplash API** (бесплатно) — https://unsplash.com/developers
- **Pixabay API** (бесплатно) — https://pixabay.com/api/docs/
- **Wikimedia Commons API** — для исторических фото (бесплатно)

### Поиск стоковых видео
- **Pexels Videos API** (бесплатно)
- **Pixabay Videos API** (бесплатно)

### AI-генерация изображений
- **Flux 1.1 Pro** через fal.ai — основной (~$0.04/картинка)
  - Эндпоинт: `https://fal.run/fal-ai/flux-pro/v1.1`
- **Midjourney v7** через useapi.net — резерв для атмосферных кадров

### AI-генерация видео (только критичные сцены)
- **Kling 3.0** через fal.ai (~$0.10/сек)
- **Veo 3.1** через fal.ai (~$0.40/сек, для hero-моментов)

### 3D-камера на статике
- **Immersity AI API** (платно, ~$0.05/клип) — основной
- **Depth Anything V2** (локально, бесплатно) — резерв
  - GitHub: https://github.com/DepthAnything/Depth-Anything-V2

### Музыка
- **Suno API** через sunoapi.com или suno-api (~$0.10/трек)
- **Mubert API** (резерв)

### SFX
- **ElevenLabs Sound Effects API** (~$0.01/эффект)
- **Freesound.org API** (бесплатно)

### Релевантность изображений
- **CLIP** (локально, через `transformers`) — оценивает соответствие картинки промту
  - Модель: `openai/clip-vit-large-patch14`

### Adobe Premiere автоматизация
- **Pymiere** — Python обёртка для ExtendScript Premiere
  - GitHub: https://github.com/qmasingarbe/pymiere
- **Adobe Premiere Pro 2024+** — приложение должно быть открыто
- **UXP API** (для будущих миграций) — https://developer.adobe.com/premiere-pro/uxp/

### Превью (thumbnails)
- **Flux 1.1 Pro** — фоновая генерация
- **Photopea API** или **Pillow** (локально) — наложение текста и элементов

### YouTube
- **YouTube Data API v3** — загрузка
  - https://developers.google.com/youtube/v3
- **OAuth 2.0** для аутентификации

### Уведомления
- **Telegram Bot API** через `python-telegram-bot`

### Видеообработка
- **FFmpeg** — обработка аудио/видео, монтаж
- **MoviePy** — резервный вариант для простых операций

---

## 7. Структура проекта

```
webik-pipeline/
│
├── webik.py                       # 🎯 Главный CLI
├── README.md                      # Инструкции
├── WEBIK_PIPELINE.md              # Это техническое задание
├── requirements.txt               # Python-зависимости
├── .env.example                   # Пример с API-ключами
├── .env                           # 🔒 Реальные ключи (в .gitignore)
├── .gitignore
│
├── core/                          # Ядро системы
│   ├── __init__.py
│   ├── state.py                   # State machine
│   ├── config.py                  # Загрузка конфигов
│   ├── logger.py                  # Логирование
│   ├── telegram_bot.py            # Telegram-уведомления
│   └── exceptions.py              # Кастомные исключения
│
├── stages/                        # 7 этапов пайплайна
│   ├── __init__.py
│   ├── stage_01_concept.py        # Идея → структура айсберга
│   ├── stage_02_script.py         # Структура → сценарий
│   ├── stage_03_scenes.py         # Сценарий → scenes.json
│   ├── stage_04_assets.py         # JSON → ассеты (parallel)
│   ├── stage_05_assemble.py       # Pymiere → .prproj
│   ├── stage_06_export.py         # Экспорт + превью + метаданные
│   └── stage_07_upload.py         # YouTube
│
├── services/                      # Обёртки над API
│   ├── __init__.py
│   ├── llm/
│   │   ├── claude.py              # Anthropic API
│   │   └── prompts/               # Промт-шаблоны
│   │       ├── concept.txt
│   │       ├── script.txt
│   │       ├── scenes.txt
│   │       ├── thumbnail.txt
│   │       └── style_examples/    # Примеры сценариев Webik для few-shot
│   │           ├── korea.md
│   │           ├── experiments.md
│   │           ├── china.md
│   │           ├── apocalypse.md
│   │           └── sex.md
│   ├── tts/
│   │   ├── elevenlabs.py          # ElevenLabs TTS
│   │   └── post_processing.py     # EQ, reverb для голоса
│   ├── stt/
│   │   └── whisperx_runner.py     # WhisperX локально
│   ├── images/
│   │   ├── pexels.py
│   │   ├── unsplash.py
│   │   ├── pixabay.py
│   │   ├── wikimedia.py
│   │   ├── flux.py                # Flux 1.1 Pro через fal.ai
│   │   ├── midjourney.py          # MJ v7 через useapi
│   │   └── clip_scorer.py         # CLIP relevance scoring
│   ├── video/
│   │   ├── kling.py
│   │   ├── veo.py
│   │   ├── pexels_videos.py
│   │   └── pixabay_videos.py
│   ├── depth/
│   │   ├── immersity.py           # Immersity AI API
│   │   └── depth_anything.py      # Локально через PyTorch
│   ├── music/
│   │   ├── suno.py
│   │   └── mubert.py
│   ├── sfx/
│   │   ├── elevenlabs_sfx.py
│   │   └── freesound.py
│   ├── premiere/
│   │   ├── pymiere_wrapper.py     # Высокоуровневая обёртка
│   │   ├── timeline_builder.py    # Сборка таймлайна
│   │   ├── effects_applier.py     # Применение плагинов
│   │   └── mogrt_loader.py        # Загрузка шаблонов
│   ├── youtube/
│   │   ├── uploader.py
│   │   └── thumbnail_generator.py
│   └── ffmpeg/
│       └── audio_processor.py     # EQ, ducking, нормализация
│
├── presets/                       # 5 стилевых пресетов
│   ├── mystic.json
│   ├── archive.json
│   ├── cipher.json
│   ├── cosmic.json
│   └── shadow.json                # Модификатор
│
├── templates/                     # .mogrt шаблоны Premiere
│   ├── intro_sting.mogrt          # Открывающий лого с капибарой
│   ├── level_card_1.mogrt         # «УРОВЕНЬ 1: ВЕРХУШКА АЙСБЕРГА»
│   ├── level_card_2.mogrt
│   ├── level_card_3.mogrt
│   ├── level_card_4.mogrt
│   ├── topic_card.mogrt           # Карточка темы (с подставляемым текстом)
│   ├── dive_transition.mogrt      # Фирменный переход «погружение»
│   ├── subtitle_template.mogrt    # Стиль субтитров
│   └── outro_card.mogrt           # Финальная заставка с CTA
│
├── luts/                          # Look Up Tables для цветокора
│   ├── mystic_cold.cube
│   ├── vintage_8mm.cube
│   ├── neon_dystopia.cube
│   ├── deep_space.cube
│   └── shadow_overlay.cube
│
├── overlays/                      # Видео-оверлеи (light leaks, grain, dust)
│   ├── film_grain_8mm.mp4
│   ├── light_leak_warm.mp4
│   ├── dust_overlay.mp4
│   ├── glitch_rgb.mp4
│   └── code_rain.mp4
│
├── fonts/                         # Шрифты
│   ├── CormorantGaramond-*.ttf    # MYSTIC
│   ├── CourierPrime-*.ttf         # ARCHIVE
│   ├── JetBrainsMono-*.ttf        # CIPHER
│   └── Geist-*.ttf                # COSMIC
│
├── projects/                      # Рабочие проекты
│   └── 2026-04-26_epstein/
│       ├── state.json             # Состояние пайплайна
│       ├── outline.json           # Stage 1
│       ├── script.md              # Stage 2
│       ├── scenes.json            # Stage 3
│       ├── assets/                # Stage 4
│       │   ├── voice/
│       │   │   ├── full.mp3
│       │   │   └── words.json     # WhisperX timestamps
│       │   ├── images/
│       │   │   ├── scene_001.jpg
│       │   │   ├── scene_002.jpg
│       │   │   └── manifest.json
│       │   ├── clips_3d/
│       │   │   ├── scene_001.mp4  # 3D-облёт камеры
│       │   │   └── scene_002.mp4
│       │   ├── videos_ai/
│       │   │   ├── scene_023.mp4  # Kling/Veo
│       │   │   └── scene_067.mp4
│       │   ├── stocks_video/      # Скачанные стоковые видео
│       │   ├── music/
│       │   │   ├── main.mp3
│       │   │   └── shadow.mp3
│       │   └── sfx/
│       │       ├── bass_drop_001.wav
│       │       └── typewriter_002.wav
│       ├── preview.html           # HTML-галерея для проверки ассетов
│       ├── project.prproj         # Stage 5 (Premiere-проект)
│       ├── final.mp4              # Stage 6
│       ├── thumbnail.jpg
│       ├── thumbnail_variants/    # A/B варианты
│       ├── metadata.json          # Описание, теги, таймкоды
│       └── youtube_url.txt        # Stage 7
│
└── tests/
    ├── test_state.py
    ├── test_stages/
    └── fixtures/
```


---

## 8. Этапы разработки

### Неделя 1: Ядро + Stages 1-3 (мозг)
**Цель:** научить пайплайн писать сценарии и разбивать их на JSON.

- [ ] Установка окружения (Python 3.11, venv)
- [ ] Структура проекта, базовые модули `core/`
- [ ] State machine + сохранение состояния в `state.json`
- [ ] Базовый CLI (`webik.py new`, `webik.py status`, `webik.py run-stage`)
- [ ] Сервис `services/llm/claude.py` — обёртка над Anthropic API
- [ ] Промт-шаблон `concept.txt` + stage_01_concept.py
- [ ] Промт-шаблон `script.txt` + 5 примеров стиля + stage_02_script.py
- [ ] Промт-шаблон `scenes.txt` + stage_03_scenes.py
- [ ] 5 файлов пресетов в `presets/*.json`
- [ ] Базовый Telegram-бот (уведомления + /approve, /revise)
- [ ] **Тест:** запустить `webik.py new "Айсберг Эпштейна"` → получить outline → script → scenes.json

### Неделя 2: Stage 4 — генерация ассетов
**Цель:** автоматический сбор всех картинок, видео, музыки, озвучки.

- [ ] `services/tts/elevenlabs.py` — генерация озвучки
- [ ] `services/tts/post_processing.py` — EQ + reverb через FFmpeg
- [ ] `services/stt/whisperx_runner.py` — word-level timestamps локально
- [ ] `services/images/pexels.py`, `unsplash.py`, `pixabay.py`, `wikimedia.py`
- [ ] `services/images/flux.py` — fallback AI-генерация
- [ ] `services/images/clip_scorer.py` — оценка релевантности
- [ ] `services/depth/immersity.py` + `depth_anything.py` — 3D-камера
- [ ] `services/video/kling.py` для критичных AI-видео сцен
- [ ] `services/music/suno.py` — генерация треков
- [ ] `services/sfx/elevenlabs_sfx.py` + `freesound.py`
- [ ] `stage_04_assets.py` — параллельная сборка через `asyncio`
- [ ] Генератор `preview.html` для проверки ассетов
- [ ] **Тест:** прогнать stage 4 на готовом scenes.json → получить полную папку assets/

### Неделя 3: Stage 5 — Pymiere + Premiere
**Цель:** автоматическая сборка проекта в Premiere со всеми эффектами.

- [ ] Установить Pymiere extension в Premiere
- [ ] `services/premiere/pymiere_wrapper.py` — высокоуровневое API
- [ ] `services/premiere/timeline_builder.py` — раскладка дорожек V1-V5, A1-A3
- [ ] `services/premiere/effects_applier.py` — применение плагинов и LUT
- [ ] `services/premiere/mogrt_loader.py` — загрузка шаблонов
- [ ] Тестовая сборка mini-проекта (3 сцены)
- [ ] Полная сборка stage 5
- [ ] Создание 8 .mogrt шаблонов (можно заказать на Fiverr ~$200)
- [ ] **Тест:** запустить stage 5 → открыть готовый .prproj → 80% работы сделано

### Неделя 4: Stages 6-7 + полировка
**Цель:** автоматический экспорт + загрузка на YouTube.

- [ ] `services/youtube/thumbnail_generator.py` — превью через Flux + Photopea
- [ ] `stage_06_export.py` — экспорт через Adobe Media Encoder (Pymiere)
- [ ] `stage_06_export.py` — генерация описания, тегов, таймкодов через Claude
- [ ] `services/youtube/uploader.py` — OAuth + загрузка как unlisted
- [ ] `stage_07_upload.py`
- [ ] Полное Telegram-меню с прогрессом
- [ ] Логирование всех операций
- [ ] **Тест:** end-to-end прогон от идеи до YouTube unlisted

### Неделя 5: Кастомизация и оптимизация
**Цель:** настроить под Webik'а, ускорить.

- [ ] Создать .mogrt шаблоны в фирменном стиле канала
- [ ] Запросить у Webik'а 5 примеров его лучших сценариев → положить в `services/llm/prompts/style_examples/`
- [ ] Настроить voice_id ElevenLabs (склонировать или подобрать)
- [ ] Создать LUT файлы в DaVinci Resolve (или скачать готовые)
- [ ] Скачать overlays (film grain, light leaks)
- [ ] Купить плагины Premiere (или установить если уже есть)
- [ ] Оптимизация: кэширование, параллелизация
- [ ] Документация для Webik'а

---

## 9. Описание STAGES

### STAGE 1: Концепция

**Файл:** `stages/stage_01_concept.py`
**Время:** ~30 секунд
**Вход:** идея от пользователя (`"Айсберг находок Эпштейна"`)
**Выход:** `outline.json`

**Логика:**
1. Загружает промт из `services/llm/prompts/concept.txt`
2. Подставляет идею пользователя
3. Отправляет в Claude API
4. Парсит JSON-ответ
5. Сохраняет в `projects/<n>/outline.json`
6. Обновляет state.json: `{"stage": 1, "status": "awaiting_approval"}`
7. Telegram bot шлёт уведомление с превью

**Структура `outline.json`:**
```json
{
  "title": "Айсберг находок Эпштейна",
  "preset": "ARCHIVE+SHADOW",
  "estimated_duration_min": 18,
  "target_audience": "русскоязычная, 16+",
  "intro_hook": "Краткое описание хука",
  "levels": [
    {
      "level": 1,
      "title": "Верхушка айсберга",
      "topics": [
        {
          "id": "1.1",
          "title": "Финансовая империя Эпштейна",
          "duration_sec": 90,
          "key_points": ["...", "..."],
          "preset_override": null
        },
        ...
      ]
    },
    ...
  ],
  "outro_summary": "...",
  "cta": "Telegram"
}
```

**Промт `concept.txt` (упрощённый):**
```
Ты — продюсер канала Webik. Канал делает айсберг-видео в стиле NetCore.

Аудитория: русскоязычная, 14-35 лет, любители конспирологии и тёмных тем.

Идея пользователя: {{IDEA}}

Создай структуру айсберга:
- 4 уровня (Верхушка → Водная гладь → Погружение → Бездна)
- 3-5 тем на уровень
- Чем глубже уровень, тем тёмнее и неизвестнее темы
- Каждая тема с заголовком и 3-5 ключевыми точками

Определи пресет визуала: MYSTIC / ARCHIVE / CIPHER / COSMIC, опционально + SHADOW.

Верни строго JSON по схеме [см. выше].
```

---

### STAGE 2: Сценарий

**Файл:** `stages/stage_02_script.py`
**Время:** ~2-3 минуты
**Вход:** `outline.json`
**Выход:** `script.md`

**Логика:**
1. Загружает `outline.json`
2. Загружает 5 примеров стиля из `services/llm/prompts/style_examples/`
3. Использует промт `script.txt` с few-shot примерами
4. Для каждой темы из outline пишет полный текст
5. Добавляет хук, переходы между уровнями, заключение, CTA
6. Вставляет маркеры пауз `[пауза 1.5с]` на драматических моментах
7. Сохраняет в `script.md`

**Особенности промта:**
- Few-shot: показываем Claude 5 реальных сценариев Webik'а как образец стиля
- Принципы: короткие предложения для напряжения, длинные для расслабления
- Обязательные элементы: хук в первые 3 секунды, мостики между темами, философская концовка
- Запрещено: сухой академизм, длинные параграфы без передышки, абстрактные концовки

---

### STAGE 3: Сцены (главное!)

**Файл:** `stages/stage_03_scenes.py`
**Время:** ~1-2 минуты
**Вход:** `script.md`, `outline.json`
**Выход:** `scenes.json`

**Логика:**
1. Загружает сценарий
2. Промт `scenes.txt` инструктирует Claude разбить сценарий на 60-150 микро-сцен по 3-8 секунд
3. Для каждой сцены Claude генерирует:
   - текст озвучки (фрагмент сценария)
   - тип визуала (`stock_photo` / `stock_video` / `ai_image` / `ai_video` / `archive` / `diagram`)
   - **поисковый запрос** для стоков (1-3 ключевых слова)
   - **AI-промт** на случай если стоки не подойдут (с тегами пресета)
   - тип движения камеры (`dolly_in` / `dolly_out` / `parallax_left` / `parallax_right` / `orbit` / `static`)
   - тип перехода К следующей сцене
   - mood (`tense` / `mystical` / `scientific` / `climactic` / `calm`)
   - SFX-маркер если нужен
   - применяемый пресет

**Структура `scenes.json`:**
```json
{
  "project_id": "epstein-iceberg",
  "primary_preset": "ARCHIVE",
  "modifiers": ["SHADOW"],
  "total_scenes": 87,
  "scenes": [
    {
      "id": "scene_001",
      "section": "intro",
      "level": 0,
      "voiceover": "Тысяча девятьсот девяносто седьмой год. Частный остров в Карибском море.",
      "duration_sec": 5.2,
      "visual": {
        "type": "ai_image",
        "search_query": "private caribbean island aerial 1990s",
        "ai_prompt": "Aerial view of mysterious private caribbean island, 1990s photograph, vintage film grain, faded archive aesthetic, helicopter view, --ar 16:9",
        "fallback_query": "tropical island aerial view"
      },
      "camera": {
        "movement": "dolly_in",
        "speed": "slow",
        "duration_sec": 5.2
      },
      "transition_out": {
        "type": "film_burn",
        "duration_ms": 800
      },
      "audio": {
        "music_layer": "main",
        "music_intensity": 0.4,
        "sfx": []
      },
      "preset": "ARCHIVE",
      "modifiers": [],
      "mood": "mysterious",
      "text_overlay": null
    },
    {
      "id": "scene_002",
      "voiceover": "Здесь происходило то, что 30 лет скрывали от мира.",
      "duration_sec": 4.0,
      "visual": {
        "type": "ai_image",
        "search_query": "epstein little saint james",
        "ai_prompt": "Mysterious dark mansion at dusk, 1990s photograph, dark shadows, vintage film stock, ominous atmosphere, --ar 16:9",
        "fallback_query": "luxury caribbean estate"
      },
      "camera": {
        "movement": "parallax_right",
        "speed": "medium"
      },
      "transition_out": {
        "type": "heartbeat_cut",
        "duration_ms": 200
      },
      "audio": {
        "music_layer": "main",
        "music_intensity": 0.6,
        "sfx": [
          {
            "type": "bass_drop",
            "trigger_word": "скрывали",
            "intensity": 0.8
          }
        ]
      },
      "preset": "ARCHIVE",
      "modifiers": ["SHADOW"],
      "mood": "tense",
      "text_overlay": {
        "text": "30 ЛЕТ ТАЙНЫ",
        "style": "stamp_red",
        "position": "lower_third",
        "duration_ms": 1500
      }
    }
  ],
  "topics_index": [
    {"id": "1.1", "scene_start": "scene_004", "scene_end": "scene_018"},
    ...
  ],
  "level_transitions": [
    {"after_scene": "scene_018", "transition": "dive_to_level_2"},
    ...
  ]
}
```

---

### STAGE 4: Генерация ассетов (самый длинный)

**Файл:** `stages/stage_04_assets.py`
**Время:** ~20-40 минут
**Вход:** `scenes.json`, `script.md`
**Выход:** папка `assets/` со всем содержимым

**Логика (параллельно через asyncio):**

#### 4.1 Озвучка
1. Берём весь текст из `script.md`
2. Разбиваем на чанки по 5000 символов (лимит ElevenLabs)
3. Каждый чанк → ElevenLabs → mp3
4. Склеиваем через FFmpeg
5. Применяем post-processing (EQ + selective reverb)
6. Сохраняем `assets/voice/full.mp3`

#### 4.2 Word-level timestamps
1. Запускаем WhisperX локально на `full.mp3`
2. Получаем JSON со словами и таймкодами
3. Сохраняем `assets/voice/words.json`

#### 4.3 Картинки (параллельно для всех scenes)
Для каждой сцены типа `stock_photo` или `ai_image`:
1. Сначала пробуем стоки: Pexels → Unsplash → Pixabay → Wikimedia
2. Скачиваем топ-5 результатов
3. CLIP-скоринг каждого относительно `ai_prompt`
4. Если лучший score > 0.65 → берём его
5. Иначе → генерим через Flux 1.1 Pro
6. Сохраняем `assets/images/scene_NNN.jpg`

#### 4.4 3D-камера
Для каждой статичной картинки:
1. Immersity AI API (или Depth Anything локально)
2. Применяем тип движения из `scenes.json` (dolly_in / parallax / orbit)
3. Скорость из настроек
4. На выходе mp4 длиной = `duration_sec` сцены
5. Сохраняем `assets/clips_3d/scene_NNN.mp4`

#### 4.5 AI-видео (только сцены типа `ai_video`)
1. Берём `ai_prompt` сцены
2. Отправляем в Kling 3.0 (стандарт) или Veo 3.1 (если помечено `priority: hero`)
3. Сохраняем `assets/videos_ai/scene_NNN.mp4`

#### 4.6 Стоковые видео (тип `stock_video`)
1. Pexels Videos API + Pixabay Videos
2. Скачиваем подходящий
3. Обрезаем до нужной длины через FFmpeg
4. Сохраняем `assets/stocks_video/scene_NNN.mp4`

#### 4.7 Музыка
1. Анализируем `scenes.json` — какие mood доминируют по уровням
2. Suno API: генерим `main.mp3` (для уровней 1-3) и `shadow.mp3` (для уровня 4 / SHADOW сцен)
3. Длина: примерно длина видео + запас
4. Сохраняем `assets/music/`

#### 4.8 SFX
1. Идём по `scenes.json` ищем все `sfx` маркеры
2. Для каждого: ElevenLabs SFX или Freesound (по типу)
3. Сохраняем с привязкой к сцене: `assets/sfx/sfx_<scene_id>_<index>.wav`

#### 4.9 HTML-превью
1. Генерируем `preview.html` со всеми ассетами в виде сетки
2. Каждая карточка: миниатюра + сцена + кнопка «перегенерить»
3. Кнопки сохраняют список в `regen_queue.json`
4. После approve в Telegram если есть `regen_queue` → перегеним только их

---

### STAGE 5: Сборка в Premiere (магия)

**Файл:** `stages/stage_05_assemble.py`
**Время:** ~5-10 минут
**Вход:** все файлы из `assets/` + `scenes.json`
**Выход:** открытый `project.prproj`

**Предусловия:**
- Adobe Premiere Pro запущен
- Pymiere extension установлена
- Все плагины из раздела 13 установлены
- Все .mogrt шаблоны в `templates/`

**Логика:**

#### 5.1 Создание проекта
```python
import pymiere
from pymiere import wrappers

# Создаём новый проект
project_path = "projects/<n>/project.prproj"
pymiere.objects.app.openDocument(project_path) if exists else create_new()

# Создаём sequence 1080p 30fps (или 4K 30)
sequence = wrappers.create_sequence(
    name="WEBIK_MAIN",
    width=1920, height=1080,
    framerate=30
)
```

#### 5.2 Импорт всех ассетов в bins
```python
project = pymiere.objects.app.project

# Создаём папки (bins)
bins = {
    "voice": project.rootItem.createBin("Voice"),
    "images_3d": project.rootItem.createBin("3D Clips"),
    "videos_ai": project.rootItem.createBin("AI Videos"),
    "stocks": project.rootItem.createBin("Stock Videos"),
    "music": project.rootItem.createBin("Music"),
    "sfx": project.rootItem.createBin("SFX"),
    "templates": project.rootItem.createBin("Templates")
}

# Импортируем
for asset in scan_assets("projects/<n>/assets"):
    project.importFiles([asset.path], suppress_ui=True, target_bin=bins[asset.category])
```

#### 5.3 Раскладка таймлайна

```
TRACK V5: Эффекты, флэши, vignette
TRACK V4: Субтитры (стилизованные из words.json)
TRACK V3: Карточки уровней + переходы
TRACK V2: Текстовые акценты (text_overlay из scenes.json)
TRACK V1: ОСНОВНОЕ ВИДЕО (3D-clips, AI-videos, stocks)

TRACK A1: Голос диктора (из voice/full.mp3)
TRACK A2: Музыка (с автоматическим side-chain ducking от A1)
TRACK A3: SFX
```

**Алгоритм:**
```python
current_time = 0
for scene in scenes_json["scenes"]:
    # 1. Определяем какой ассет идёт на V1
    if scene.visual.type == "ai_video":
        clip_path = f"assets/videos_ai/{scene.id}.mp4"
    elif scene.visual.type == "stock_video":
        clip_path = f"assets/stocks_video/{scene.id}.mp4"
    else:  # stock_photo, ai_image, archive
        clip_path = f"assets/clips_3d/{scene.id}.mp4"  # 3D-облёт
    
    # 2. Вставляем на V1
    sequence.videoTracks[0].insertClip(
        clip_path,
        time=current_time,
        end_time=current_time + scene.duration_sec
    )
    
    # 3. Применяем LUT по пресету
    apply_lut(clip, preset=scene.preset)
    
    # 4. Если SHADOW модификатор — добавляем vignette
    if "SHADOW" in scene.modifiers:
        apply_effect(clip, "Lumetri Color", {"vignette": -2})
    
    # 5. Текстовый оверлей на V2
    if scene.text_overlay:
        insert_mogrt(
            "templates/topic_card.mogrt",
            track=2,
            time=current_time,
            text=scene.text_overlay.text,
            style=scene.text_overlay.style
        )
    
    # 6. Переход К следующей сцене
    if scene.transition_out:
        apply_transition(
            track=1,
            time=current_time + scene.duration_sec - 0.5,
            type=scene.transition_out.type,  # "film_burn", "heartbeat_cut", etc
            duration=scene.transition_out.duration_ms
        )
    
    # 7. SFX на A3
    for sfx in scene.audio.sfx:
        # Находим точное время триггер-слова через words.json
        trigger_time = find_word_time(sfx.trigger_word, current_time, words_json)
        sequence.audioTracks[2].insertClip(
            f"assets/sfx/sfx_{scene.id}_{i}.wav",
            time=trigger_time
        )
    
    current_time += scene.duration_sec

# 8. Голос на A1 (целиком)
sequence.audioTracks[0].insertClip(
    "assets/voice/full.mp3",
    time=intro_duration
)

# 9. Музыка на A2 (с ducking)
sequence.audioTracks[1].insertClip(
    "assets/music/main.mp3",
    time=0
)
apply_audio_effect(audio_track_1, "Multiband Compressor", side_chain_from=audio_track_0)

# 10. Карточки уровней на V3
for transition in scenes_json["level_transitions"]:
    insert_mogrt(
        f"templates/level_card_{transition.target_level}.mogrt",
        track=2,
        time=transition.time
    )
```

#### 5.4 Применение пресета

```python
def apply_preset(clip, preset_name, modifiers=[]):
    preset = load_preset(f"presets/{preset_name.lower()}.json")
    
    # LUT
    apply_lut(clip, preset["lut_path"])
    
    # Если есть SHADOW
    if "SHADOW" in modifiers:
        apply_lut(clip, "luts/shadow_overlay.cube", opacity=0.3)
        apply_effect(clip, "Vignette", preset["shadow_vignette"])
    
    # Overlay (film grain, light leak, glitch)
    if preset.get("overlay"):
        add_overlay_track_clip(
            preset["overlay_path"],
            blend_mode="screen",
            opacity=0.15
        )
```

#### 5.5 Открытие проекта для QA
После сборки скрипт **не закрывает** Premiere, а оставляет открытым с активной sequence. Webik видит готовый проект и может докрутить руками.

---

### STAGE 6: Экспорт + метаданные

**Файл:** `stages/stage_06_export.py`
**Время:** ~10-15 минут
**Вход:** `project.prproj` (одобренный)
**Выход:** `final.mp4`, `thumbnail.jpg`, `metadata.json`

**Логика:**

#### 6.1 Экспорт через Adobe Media Encoder
```python
sequence = pymiere.objects.app.project.activeSequence

# Настройки экспорта
encoder_preset_path = "encoder_presets/youtube_4k.epr"

# Очередь в AME
pymiere.objects.app.encoder.encodeSequence(
    sequence,
    output_path="projects/<n>/final.mp4",
    preset=encoder_preset_path,
    work_area_type=1  # ENTIRE_SEQUENCE
)
```

#### 6.2 Генерация превью (thumbnail)
1. Анализируем `outline.json` → выбираем главный визуальный концепт
2. Flux 1.1 Pro → фон (тёмный, кинематографичный)
3. Photopea API или Pillow → накладываем:
   - Жёлтый текст-крючок (3-5 слов)
   - Капибару-маскот в углу
   - Опционально: красную стрелку, круг, эффект «затаскивания»
4. Генерим 3 варианта (для A/B)
5. Лучший → `thumbnail.jpg`

#### 6.3 Метаданные через Claude
```python
prompt = f"""
Сценарий: {script_md}

Сгенерируй для YouTube:
1. Заголовок (60-100 символов, цепляющий, с цифрой если уместно)
2. Описание (~500 слов, с таймкодами тем, ссылкой на Telegram, тегами)
3. 15-20 тегов (через запятую)
4. Таймкоды разделов в формате 0:00 название

Стиль: как у канала NetCore, мистический, интригующий.
"""
metadata = claude_api.generate(prompt, response_format="json")
save_json("metadata.json", metadata)
```

---

### STAGE 7: Загрузка на YouTube

**Файл:** `stages/stage_07_upload.py`
**Время:** ~5 минут
**Вход:** `final.mp4`, `thumbnail.jpg`, `metadata.json`
**Выход:** YouTube URL (как `unlisted`)

**Логика:**
1. OAuth 2.0 авторизация (один раз сохраняем `youtube_credentials.json`)
2. `youtube.videos().insert()`:
   - title из metadata.json
   - description из metadata.json
   - tags из metadata.json
   - categoryId: "24" (Entertainment) или "27" (Education)
   - **privacyStatus: "unlisted"** (не публичное!)
   - madeForKids: false
3. После загрузки — `youtube.thumbnails().set()` с превью
4. Сохраняем URL в `youtube_url.txt`
5. Telegram-сообщение:
   ```
   ✅ Видео загружено!
   📺 URL: https://youtu.be/...
   
   Превью, описание и теги установлены.
   Зайди в YouTube Studio и нажми «Опубликовать», когда готов.
   ```

**Webik в YouTube Studio проверяет всё последний раз и публикует.**


---

## 10. Установка и запуск

### Системные требования
- **OS:** Windows 10/11 (рекомендуется) или macOS
- **Python:** 3.11+
- **GPU:** NVIDIA с 8GB+ VRAM (для WhisperX и Depth Anything локально). Если нет — всё через API, чуть дороже.
- **RAM:** 16GB+
- **Disk:** 100GB свободно (для проектов и моделей)
- **Adobe Premiere Pro 2024+**
- **FFmpeg** в PATH
- **Node.js 18+** (для Pymiere extension)
- **Git**

### Шаг 1: Клонировать репозиторий
```bash
git clone https://github.com/webik/webik-pipeline.git
cd webik-pipeline
```

### Шаг 2: Создать виртуальное окружение
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### Шаг 3: Установить зависимости
```bash
pip install -r requirements.txt
```

**`requirements.txt`:**
```
anthropic>=0.40.0
elevenlabs>=1.10.0
openai-whisper
whisperx
fal-client>=0.5.0
google-api-python-client>=2.140.0
google-auth-oauthlib>=1.2.0
python-telegram-bot>=21.0
pymiere>=1.4
Pillow>=10.4
opencv-python>=4.10
ffmpeg-python>=0.2
moviepy>=1.0.3
torch>=2.4
transformers>=4.45
sentence-transformers
clip-by-openai
aiohttp>=3.10
asyncio
python-dotenv>=1.0
pydantic>=2.8
rich>=13.7
typer>=0.12
jinja2>=3.1
```

### Шаг 4: Установить Pymiere extension
```bash
# Скачиваем extension installer с GitHub
git clone https://github.com/qmasingarbe/pymiere
cd pymiere

# Windows:
extension_installer_win.bat

# macOS:
chmod +x extension_installer_mac.sh
./extension_installer_mac.sh
```

После установки запустить Premiere Pro → Window → Extensions → Pymiere Link

### Шаг 5: FFmpeg
```bash
# Windows (через winget):
winget install ffmpeg

# macOS:
brew install ffmpeg

# Проверка:
ffmpeg -version
```

### Шаг 6: Настроить .env
```bash
cp .env.example .env
# Отредактировать .env, вставить ключи
```

**`.env.example`:**
```env
# === LLM ===
ANTHROPIC_API_KEY=sk-ant-...

# === TTS ===
ELEVENLABS_API_KEY=...
ELEVENLABS_VOICE_ID=...

# === Generative ===
FAL_API_KEY=...

# === Stocks (бесплатные ключи) ===
PEXELS_API_KEY=...
UNSPLASH_API_KEY=...
PIXABAY_API_KEY=...

# === 3D Camera ===
IMMERSITY_API_KEY=...

# === Music ===
SUNO_API_KEY=...

# === SFX ===
FREESOUND_API_KEY=...

# === YouTube ===
YOUTUBE_CLIENT_SECRETS_PATH=./youtube_credentials.json
YOUTUBE_TOKEN_PATH=./youtube_token.json

# === Telegram ===
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...

# === Premiere ===
PREMIERE_PATH="C:\Program Files\Adobe\Adobe Premiere Pro 2024\Adobe Premiere Pro.exe"

# === Settings ===
DEFAULT_VIDEO_RESOLUTION=1920x1080
DEFAULT_FRAMERATE=30
ASSETS_QUALITY=high  # low | medium | high
USE_LOCAL_DEPTH=false  # true = Depth Anything локально, false = Immersity API
USE_LOCAL_WHISPER=true  # true = WhisperX локально (нужен GPU)
```

### Шаг 7: Получить API-ключи
- **Anthropic Claude:** https://console.anthropic.com/ → Settings → API Keys
- **ElevenLabs:** https://elevenlabs.io/ → Profile → API Keys
- **fal.ai:** https://fal.ai/dashboard/keys
- **Pexels:** https://www.pexels.com/api/new/
- **Unsplash:** https://unsplash.com/developers
- **Pixabay:** https://pixabay.com/api/docs/
- **Immersity AI:** https://www.immersity.ai/api
- **Suno:** https://sunoapi.com/ или прямые партнёры
- **Freesound:** https://freesound.org/apiv2/apply/
- **YouTube Data API:** Google Cloud Console → создать проект → включить YouTube Data API v3 → OAuth 2.0 credentials → скачать как `youtube_credentials.json` в корень
- **Telegram Bot:** написать @BotFather, создать бота, получить токен; для chat_id написать боту первое сообщение и получить через @userinfobot

### Шаг 8: Запустить Telegram-бот в фоне
```bash
python -m core.telegram_bot &
```

### Шаг 9: Проверка готовности
```bash
python webik.py doctor
```

Эта команда проверит:
- ✓ Все API-ключи валидны
- ✓ Premiere открывается через Pymiere
- ✓ FFmpeg в PATH
- ✓ GPU доступен (если используется локальный WhisperX)
- ✓ Все .mogrt шаблоны на месте
- ✓ Все LUT файлы на месте
- ✓ Telegram-бот отвечает

---

## 11. CLI-команды

```bash
# Создать новый проект
python webik.py new "Айсберг Эпштейна" --preset archive+shadow --duration 18

# Опции:
# --preset       — принудительный пресет (иначе LLM сам выберет)
# --duration     — целевая длительность в минутах (default: 15)
# --start-from   — с какого этапа начать (default: 1)


# Посмотреть статус
python webik.py status
# Выводит:
# ┌──────────────────────┬──────────┬─────────────────┐
# │ Project              │ Stage    │ Status          │
# ├──────────────────────┼──────────┼─────────────────┤
# │ epstein-iceberg      │ 4/7      │ awaiting        │
# │ china-iceberg        │ 7/7      │ uploaded        │
# └──────────────────────┴──────────┴─────────────────┘


# Запустить конкретный этап
python webik.py run-stage 4 --project epstein-iceberg


# Продолжить с последнего сохранённого этапа
python webik.py resume --project epstein-iceberg


# Одобрить текущий чекпоинт (то же что /approve в Telegram)
python webik.py approve --project epstein-iceberg


# Отправить фидбек на переделку
python webik.py revise --project epstein-iceberg --feedback "Усиль хук, добавь больше пауз перед бездной"


# Перегенерить конкретные ассеты по списку
python webik.py regen-assets --project epstein-iceberg --scenes "scene_005,scene_023,scene_087"


# Открыть превью-галерею в браузере
python webik.py preview --project epstein-iceberg


# Очистить кэш проекта (если совсем плохо)
python webik.py clean --project epstein-iceberg --keep script,outline


# Список всех проектов
python webik.py list


# Удалить проект
python webik.py delete --project old-iceberg


# Проверка готовности системы
python webik.py doctor


# Тестовый прогон (без затрат на API)
python webik.py dry-run "Тестовая идея"


# Шаблонные команды для частых задач
python webik.py quick --topic "Эпштейн" --auto-approve-all
# (создаёт проект и автоматически апрувит каждый этап без проверки — для тестов)
```

---

## 12. Telegram-бот

### Команды

| Команда | Описание |
|---------|----------|
| `/start` | Регистрация чата |
| `/status` | Статус всех активных проектов |
| `/projects` | Список проектов |
| `/project <id>` | Детали проекта |
| `/approve` | Одобрить текущий чекпоинт активного проекта |
| `/approve <project>` | Одобрить конкретный проект |
| `/revise <feedback>` | Переделать с фидбеком |
| `/regen` | Перегенерировать без фидбека |
| `/regen-scenes 5,10,42` | Перегенерить только указанные сцены (для stage 4) |
| `/preview` | Прислать ссылку на HTML-галерею |
| `/script` | Прислать текущий script.md |
| `/scenes` | Прислать scenes.json |
| `/cancel` | Отменить текущий проект |
| `/help` | Справка |

### Уведомления

После каждого stage бот шлёт сообщение:
```
🧊 Stage 3 готов: scenes.json
━━━━━━━━━━━━━━━━━━━━━━
Проект: epstein-iceberg
Сцен сгенерировано: 87
Пресет: ARCHIVE + SHADOW
Длительность: ~17 мин

📊 Бюджет на ассеты:
• Озвучка: $4.20
• Картинки (Flux): $3.20
• 3D-camera: $4.35
• AI-видео: $5.00
• Музыка: $0.30
• SFX: $0.20
─────────────────
ИТОГО: ~$17.25

📁 Файлы:
[scenes.json] — посмотреть
[preview.html] — превью разбивки

⏭ Следующий этап: генерация ассетов (~25 мин)

/approve — продолжить
/revise <текст> — переделать
```

При завершении пайплайна:
```
🎉 Видео готово и загружено!
━━━━━━━━━━━━━━━━━━━━━━
📺 https://youtu.be/abc123 (unlisted)

Заголовок: «Айсберг Эпштейна: что скрывалось 30 лет»
Длительность: 17:34
Размер: 4.2 GB

Зайди в YouTube Studio и опубликуй когда готов.

📊 Итого по проекту:
• Время от старта до готовности: 2 ч 14 мин
• Стоимость API: $19.85
• Сцен: 87
```

---

## 13. Плагины Premiere

Все плагины должны быть установлены ДО первого запуска stage 5. Pymiere ими управляет автоматически.

### Обязательные

| Плагин | Назначение | Где взять |
|--------|------------|-----------|
| **Sapphire by Boris FX** | Главные переходы (S_LightLeak, S_Glitch, S_Zap), цветовые эффекты | https://borisfx.com/products/sapphire/ |
| **Red Giant Universe** | Glitch, RGB Separation, Retrograde — для CIPHER | https://www.maxon.net/en/red-giant-universe |
| **FilmConvert Nitrate** | Кинокоррекция и LUT-применение, ARCHIVE-стиль | https://www.filmconvert.com/ |
| **Motion Bro** | Менеджер пресетов (управляет шаблонами) | https://motionbro.net/ |
| **Handy Seamless Transitions** | Базовые переходы между темами | https://aescripts.com/handy-seamless-transitions/ |

### Желательные

| Плагин | Назначение |
|--------|------------|
| **Magic Bullet Looks** | Альтернатива FilmConvert |
| **CINEPUNCH** | Расширенные переходы, light leaks, dust overlays |
| **Plural Eyes** | Авто-синхронизация SFX |
| **Beat Edit** | Авто-резка под ритм музыки |
| **AutoCaption / Submagic** (UXP) | Стилизованные анимированные субтитры |

### Маппинг переходов на плагины

В `presets/*.json` для каждого пресета указано какой плагин и эффект использовать:

```json
{
  "preset": "ARCHIVE",
  "transitions": {
    "default": {
      "plugin": "Sapphire",
      "effect": "S_FilmEffect",
      "params": {"grain": 0.4, "scratches": 0.3}
    },
    "between_topics": {
      "plugin": "Sapphire",
      "effect": "S_LightLeak",
      "params": {"intensity": 0.6, "color": "warm"}
    },
    "between_levels": {
      "plugin": "custom",
      "mogrt": "templates/dive_transition.mogrt"
    },
    "shadow_cut": {
      "plugin": "BuiltIn",
      "effect": "Dip to Black",
      "params": {"duration_ms": 200}
    }
  }
}
```

---

## 14. .mogrt шаблоны

**.mogrt** = Motion Graphics Template Premiere. Создаются один раз в After Effects (или Premiere), потом Pymiere подставляет в них контент.

### Список обязательных шаблонов

| Файл | Назначение | Кастомные параметры |
|------|------------|---------------------|
| `intro_sting.mogrt` | Открывающий лого Webik с капибарой | — (без параметров, всегда одинаковый) |
| `level_card_1.mogrt` | «🧊 УРОВЕНЬ 1: ВЕРХУШКА АЙСБЕРГА» | — |
| `level_card_2.mogrt` | «🌊 УРОВЕНЬ 2: ВОДНАЯ ГЛАДЬ» | — |
| `level_card_3.mogrt` | «🕳️ УРОВЕНЬ 3: ПОГРУЖЕНИЕ» | — |
| `level_card_4.mogrt` | «🕯️ УРОВЕНЬ 4: БЕЗДНА» | — |
| `topic_card.mogrt` | Карточка темы с подставляемым названием | `text`, `subtitle`, `style` (mystic/archive/cipher/cosmic) |
| `dive_transition.mogrt` | Фирменный «погружающий» переход между уровнями | `from_level`, `to_level` |
| `subtitle_template.mogrt` | Стиль субтитров | `text`, `highlight_word` |
| `outro_card.mogrt` | Финальная заставка с CTA | `telegram_link` |

### Как создавать (рекомендации)

**Вариант 1 — самому в After Effects + Premiere:**
1. After Effects → создать композицию 1920×1080
2. Анимация на 2-3 секунды
3. Добавить Essential Graphics панель
4. Кликнуть «Export Motion Graphics Template»
5. Сохранить .mogrt в `templates/`

**Вариант 2 — заказать на Fiverr (~$200 за все 9 шаблонов):**
- Запрос: «9 mogrt templates for Premiere Pro in dark mysterious YouTube iceberg style»
- Дать референсы NetCore
- Прислать лого Webik с капибарой

**Вариант 3 — купить готовые на Envato Elements/Motion Array:**
- Поиск: «iceberg youtube template mogrt»
- Адаптировать под свой стиль

---

## 15. Бюджет

### Стоимость одного 15-минутного айсберга

| Категория | Стоимость | Примечание |
|-----------|-----------|------------|
| Claude API (концепция + сценарий + JSON + метаданные) | $1.50 | ~50K input + 30K output tokens |
| ElevenLabs Multilingual v2 (15 мин озвучки) | $4.00 | Creator план |
| Flux 1.1 Pro (~80 картинок) | $3.20 | $0.04/картинка |
| Immersity AI (3D-камера, ~80 клипов) | $4.00 | $0.05/клип |
| Kling 3.0 (5 AI-видео сцен) | $5.00 | $0.10/сек × 10 сек |
| Suno API (3 трека) | $0.30 | |
| ElevenLabs SFX (~20 эффектов) | $0.20 | |
| Стоки Pexels/Unsplash/Pixabay | $0 | бесплатно |
| WhisperX, Depth Anything | $0 | локально |
| YouTube API | $0 | бесплатно (квоты) |
| **ИТОГО на ролик** | **~$18-20** | |

### Месячный бюджет (8 роликов)

| Категория | Стоимость |
|-----------|-----------|
| Per video × 8 | $144-160 |
| Подписка Sapphire/Red Giant | $30-50 |
| Подписка Suno (если активная) | $10 |
| Подписка fal.ai | $0 (pay-as-you-go) |
| **ИТОГО месяц** | **~$200** |

### Разовые затраты (старт)

| Категория | Стоимость |
|-----------|-----------|
| Sapphire (если ещё нет) | $300-700 |
| Red Giant Universe | $20/мес или $200/год |
| FilmConvert Nitrate | $99 |
| Motion Bro + HST | $50 |
| 9 .mogrt шаблонов (Fiverr) | $200 |
| Кастомный voice clone ElevenLabs (опционально) | $0 (на Pro плане бесплатно) |
| **ИТОГО старт** | **$700-1300** |

---

## 16. Чек-лист готовности

### Перед запуском пайплайна

#### Аккаунты и ключи
- [ ] Anthropic Claude API ключ ($5+ на балансе)
- [ ] ElevenLabs API ключ (Creator или Pro план)
- [ ] ElevenLabs voice_id выбран/склонирован
- [ ] fal.ai API ключ ($20+ на балансе)
- [ ] Pexels, Unsplash, Pixabay ключи
- [ ] Immersity AI ключ
- [ ] Suno API ключ
- [ ] Freesound API ключ
- [ ] YouTube Data API credentials.json
- [ ] Telegram бот создан, токен получен

#### Софт
- [ ] Python 3.11+ установлен
- [ ] Adobe Premiere Pro 2024+ установлен и активирован
- [ ] FFmpeg в PATH
- [ ] Node.js установлен
- [ ] Git установлен
- [ ] Pymiere extension установлена в Premiere
- [ ] Sapphire by Boris FX установлен
- [ ] Red Giant Universe установлен
- [ ] FilmConvert Nitrate установлен
- [ ] Motion Bro + Handy Seamless Transitions установлены
- [ ] CINEPUNCH (опционально)

#### Файлы
- [ ] 9 .mogrt шаблонов в `templates/`
- [ ] 5 .cube LUT файлов в `luts/`
- [ ] Overlay-видео в `overlays/`
- [ ] 5 примеров стиля в `services/llm/prompts/style_examples/`
- [ ] Брендинг канала: лого, капибара, шрифты

#### Тесты
- [ ] `python webik.py doctor` — все галочки
- [ ] `python webik.py dry-run "Тест"` — без ошибок
- [ ] Тестовый stage 1 → outline.json создаётся
- [ ] Тестовый stage 2 → script.md создаётся
- [ ] Тестовый stage 3 → scenes.json создаётся
- [ ] Тестовый stage 4 на 3 сценах → ассеты создаются
- [ ] Тестовый stage 5 → Premiere открывается с проектом
- [ ] Telegram уведомления приходят

#### Бренд
- [ ] Палитра канала зафиксирована
- [ ] Шрифты подобраны
- [ ] Голос диктора одобрен и стабилен
- [ ] Шаблон превью утверждён
- [ ] Описание/CTA шаблонизированы

---

## 🚀 С чего начать прямо сейчас

1. **Прочти этот документ полностью** (1 час)
2. **Получи API-ключи** — особенно Anthropic, ElevenLabs, fal.ai (30 мин)
3. **Создай Telegram-бот** через @BotFather (5 мин)
4. **Установи Premiere + плагины** (если ещё нет) (час)
5. **Скачай Pymiere и проверь связь** Python ↔ Premiere (30 мин)
6. **Открой Cursor / Claude Code в этой папке** и попроси AI начать с stage 1
7. **Через неделю** у тебя будет работающий генератор сценариев и JSON
8. **Через месяц** — полностью рабочий пайплайн

---

## 📞 Контекст для AI-разработчика

Если ты — AI (Claude/Cursor/Copilot), которому скинули этот документ для разработки:

- **Канал:** Webik (русскоязычный, формат «айсберг»)
- **Главный референс:** NetCore
- **Главный язык кода:** Python 3.11+
- **Главная цель:** автоматизировать всё кроме творческого QA
- **Webik работает в Adobe Premiere** и хочет максимум автоматизации монтажа
- **5 примеров реальных сценариев Webik'а** (Корея, Эксперименты на людях, Китай, Апокалипсис, Секс) → используй их как few-shot примеры стиля при генерации сценариев
- **Webik готов** покупать плагины Premiere, оплачивать API, ставить нужный софт
- **Webik НЕ программист** — пиши код качественно, документируй, делай проверки ошибок понятными

**Начинай разработку с Этапа 1 (Stages 1-3 — мозг пайплайна).** Это даст быстрый видимый результат и Webik сможет сразу начать получать пользу (генерация сценариев) пока ты работаешь над остальным.

---

**Конец документа.** Версия 1.0 — 2026-04-26.
