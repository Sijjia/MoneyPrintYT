@echo off
REM Ежедневный догруз шортсов, ASCII-пути (короткие 8.3 + ASCII-джанкшн E:\ytb_webik_gta) — работает под
REM планировщиком при любой кодовой странице. 3/канал/день. Запуск 14:07 (после сброса квоты ~13:00 Бишкек).
set PYTHONIOENCODING=utf-8
set PY=C:\Users\aidar\OneDrive\F0A5~1\AUTOMO~1\WEBIK-~1\VENV~1\Scripts\python.exe
set PROJ=C:\Users\aidar\OneDrive\F0A5~1\AUTOMO~1\WEBIK-~2
set LOG=%PROJ%\tests\yt_shorts_daily.log
cd /d "%PROJ%"
echo ===== %DATE% %TIME% shorts daily ===== >> "%LOG%"
"%PY%" "%PROJ%\tests\yt_shorts_upload.py" --channel debik --dir "E:\video for ytb\Deb1k\Iceberg GTA\Shorts" --meta "E:\video for ytb\Deb1k\Iceberg GTA\shorts_meta_EN.md" --start 2026-09-12 --tz 6 --max 3 --go >> "%LOG%" 2>&1
"%PY%" "%PROJ%\tests\yt_shorts_upload.py" --channel webik --dir "E:\ytb_webik_gta\Shorts" --meta "E:\ytb_webik_gta\shorts_meta_RU.md" --start 2026-09-12 --tz 6 --max 3 --go >> "%LOG%" 2>&1
