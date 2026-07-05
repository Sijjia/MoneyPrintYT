# Сборка ролика — ЕДИНСТВЕННЫЙ ПУТЬ

> Template-based сборка. Всё остальное (процедурный Stage 5) — тупик, отключено.

## Как собрать

Premiere открыт + панель pymiere (порт 3000 слушает). **Не трогать Premiere во время прогона.**

```bash
# МИНИ (интро + Уровень 1, ~51 сцена) — для проверки
PYTHONUTF8=1 MINI_LIMIT_LEVEL=1  <venv>/python.exe tests/assemble_religioznyj.py

# ПОЛНЫЙ ролик (все сцены)
PYTHONUTF8=1 MINI_LIMIT_LEVEL=-1 <venv>/python.exe tests/assemble_religioznyj.py
```
`<venv>` = `../webik-pipeline/.venv/Scripts/python.exe`.
`PYTHONUTF8=1` обязателен (иначе UnicodeEncodeError на «→» в логе при пайпе).

## Что делает `tests/assemble_religioznyj.py`

1. `[A]` ffmpeg pretrim видеостоков под слот + loop-fill коротких (без дыр), звук `-an`.
2. `[A2]` рендер плашек ТЕМ (печатная машинка, `services/text/apocalypse_card.py::render_topic_card_typewriter`).
3. `[1]` reset: свежая копия шаблона Апокалипсиса → `project_template.prproj`.
4. `[2]` голос `full.mp3` на A1.
5. `[3]` очистка ВСЕГО шаблона в зоне: V1..Vn + A2..An (родной контент Апокалипсиса убран).
6. `[4]` видео на V3, `[4b]` темы на V4, `[4c]` звук машинки на A4.
7. `[5]` очистка всего после zone_end.
8. `[7]` dip-to-black фейды на V3 — **batch, один eval_script** (`apply_fades_batch_es`).
9. `[9]` save.

## Решения (не переделывать без Айдара)

- **Плашки ТЕМ** = свой .mov, печатная машинка, Share Tech Mono, **чёрный непрозрачный фон**,
  **макс 2 строки**, база 76px (длинное авто-ужимается). Настройки в `apocalypse_card.py`
  (`TW_*`). Одобрено Айдаром.
- **Плашки УРОВНЯ (1/2/3/4)** = НЕ ставим автоматом. Место на V1 пустое. Айдар вставляет
  свою графику руками для всех 4 уровней. (Родной MOGRT уровня = дип-ту-блэк со встроенной
  анимацией, скриптом корректно не ставится — мигает/чернеет.)
- **Музыку не ставим** (Айдар сам). Пайплайн = визуал + SFX.
- **Уровни L2-L4** и грейдинг/музыку Айдар доводит руками после сборки.

## ⛔ НЕ ИСПОЛЬЗОВАТЬ

- `webik.py run-stage 5` / `stages/stage_05_assemble.py` — ПРОЦЕДУРНЫЙ путь, тупик
  (строит таймлайн с нуля, старые Impact-карточки, дох на ~40 клипах). Отключён в webik.py.
- Массовые операции над клипами через объектную модель pymiere в python-цикле —
  медленно (O(n²)) и вешает Premiere. Всё делать ОДНИМ `eval_script` (пример — фейды).

## Зависимости сборщика (не трогать)

`tests/assemble_iceberg_test.py` (хелперы: log, health_check, trim_sfx, find_clip_by_timeline_start,
set_clip_volume, render_topic_card_typewriter, константы) ·
`services/text/apocalypse_card.py` · `services/premiere_template/{media_swap,timeline_ops}.py` ·
`services/premiere/archive_clip_placer.py`.
