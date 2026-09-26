#!/usr/bin/env bash
# Ежедневный догруз шортсов «Айсберг GTA» на оба канала, квото-безопасно (по 3/канал = 6/день).
# Трекинг в secrets/shorts_uploaded_<channel>.json — уже залитые пропускаются. Когда всё залито —
# скрипт ничего не делает. Расписание публикации: 2/день 9:00 и 21:00 (UTC+6), старт 2026-09-12.
cd "C:/Users/aidar/OneDrive/Рабочий стол/automotization-youtube/webik-pipeline(v2)" || exit 1
PY="../webik-pipeline/.venv/Scripts/python.exe"
export PYTHONIOENCODING=utf-8
echo "===== $(date) ежедневный догруз шортсов ====="
"$PY" tests/yt_shorts_upload.py --channel debik \
  --dir "E:/video for ytb/Deb1k/Iceberg GTA/Shorts" \
  --meta "E:/video for ytb/Deb1k/Iceberg GTA/shorts_meta_EN.md" \
  --start 2026-09-12 --tz 6 --max 3 --go
"$PY" tests/yt_shorts_upload.py --channel webik \
  --dir "E:/video for ytb/Webik/Айсберг GTA/Shorts" \
  --meta "E:/video for ytb/Webik/Айсберг GTA/shorts_meta_RU.md" \
  --start 2026-09-12 --tz 6 --max 3 --go
