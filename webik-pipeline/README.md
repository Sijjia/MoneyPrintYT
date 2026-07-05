# 🧊 Webik Pipeline

Полностью автоматизированный пайплайн создания YouTube-видео в формате «айсберг» для канала [@WebikStudio](https://www.youtube.com/@WebikStudio).

## Что делает

От идеи до загруженного видео на YouTube за 2-3 часа:
1. Концепция (структура айсберга по 4 уровням)
2. Сценарий (полный текст для озвучки)
3. Разбивка на сцены (JSON для монтажа)
4. Генерация ассетов (озвучка, картинки, 3D-камера, музыка, SFX)
5. Сборка проекта в Adobe Premiere через Pymiere
6. Экспорт + превью + метаданные
7. Загрузка на YouTube как unlisted

На каждом этапе ты получаешь уведомление в Telegram и можешь либо одобрить, либо отправить фидбек на переделку.

## Установка

См. [WEBIK_PIPELINE.md](./WEBIK_PIPELINE.md) — полное техзадание.

```bash
# 1. Клонировать
git clone <repo>
cd webik-pipeline

# 2. Виртуальное окружение
python -m venv venv
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate

# 3. Зависимости
pip install -r requirements.txt

# 4. Конфиг
cp .env.example .env
# Открой .env и заполни ключи

# 5. Проверка
python webik.py doctor
```

## Быстрый старт

```bash
# Создать проект
python webik.py new "Айсберг Эпштейна" --duration 17

# Запустить Stage 1 (концепция)
python webik.py run-stage 1 --project 2026-04-26_aysberg-epshteyna

# Посмотреть outline.json и одобрить
python webik.py approve --project 2026-04-26_aysberg-epshteyna

# Запустить Stage 2 (сценарий)
python webik.py run-stage 2 --project 2026-04-26_aysberg-epshteyna

# ... и т.д.
```

## Статус разработки

- [x] Stage 1: Концепция
- [x] Stage 2: Сценарий
- [x] Stage 3: Сцены
- [ ] Stage 4: Генерация ассетов (в разработке)
- [ ] Stage 5: Pymiere сборка (в разработке)
- [ ] Stage 6: Экспорт (в разработке)
- [ ] Stage 7: YouTube загрузка (в разработке)

## Структура

См. [WEBIK_PIPELINE.md раздел 7](./WEBIK_PIPELINE.md#7-структура-проекта).

## Документация

- [WEBIK_PIPELINE.md](./WEBIK_PIPELINE.md) — полное техзадание
- [services/llm/prompts/](./services/llm/prompts/) — промт-шаблоны
- [presets/](./presets/) — стилевые пресеты
