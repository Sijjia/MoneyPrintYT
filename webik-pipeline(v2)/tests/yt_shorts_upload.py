"""Загрузка шортсов на YouTube с РАСПИСАНИЕМ: 2 шортса/день — 9:00 и 21:00 (локальное время).
Каждый шортс приватный до publishAt → в назначенный час публикуется сам. Порядок = по номеру файла.
Переиспользует OAuth-токен из tests/yt_upload.py (сначала --auth-only там).

  ! ../webik-pipeline/.venv/Scripts/python.exe tests/yt_shorts_upload.py --channel debik \
       --dir "E:/video for ytb/Deb1k/Iceberg GTA/Shorts" \
       --meta "E:/video for ytb/Deb1k/Iceberg GTA/shorts_meta_EN.md" \
       --start 2026-09-12 --tz 6
--start — дата первого шортса (9:00). --tz — часовой пояс канала (смещение от UTC, напр. 6=Бишкек,
3=Москва). БЕЗ --go только показывает план (dry-run), НИЧЕГО не грузит."""
import argparse, json, re, sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from tests.yt_upload import get_service, CATEGORY_GAMING, SECRETS  # noqa

SLOTS = [9, 21]  # часы публикации (локальные)


def parse_shorts_meta(p: Path):
    """## NN. Title #shorts  +  строки-описание до следующего ##."""
    blocks = re.split(r"(?m)^##\s+", p.read_text(encoding="utf-8"))
    items = {}
    for b in blocks[1:]:
        lines = b.strip().splitlines()
        head = lines[0].strip()
        m = re.match(r"(\d+)\.\s*(.+)", head)
        if not m:
            continue
        num = int(m.group(1))
        title = m.group(2).strip()
        desc = "\n".join(lines[1:]).strip()
        items[num] = (title, desc)
    return items


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--channel", required=True, choices=["webik", "debik"])
    ap.add_argument("--dir", required=True)
    ap.add_argument("--meta", required=True)
    ap.add_argument("--start", required=True, help="дата первого шортса YYYY-MM-DD")
    ap.add_argument("--tz", type=float, required=True, help="часовой пояс канала (смещение от UTC)")
    ap.add_argument("--go", action="store_true", help="реально грузить (иначе dry-run плана)")
    ap.add_argument("--max", type=int, default=0, help="макс шортсов за этот запуск (0=без лимита); "
                    "для экономии дневной квоты YouTube (~6 видео/сутки на проект)")
    a = ap.parse_args()
    state_f = SECRETS / f"shorts_uploaded_{a.channel}.json"
    done = json.loads(state_f.read_text()) if state_f.exists() else {}

    d = Path(a.dir)
    pref = "short_EN_" if a.channel == "debik" else "short_RU_"
    vids = sorted(d.glob(f"{pref}*.mp4"))
    if not vids:
        vids = sorted(d.glob("short_*.mp4"))
    meta = parse_shorts_meta(Path(a.meta))
    lang = "en" if a.channel == "debik" else "ru"
    tzoff = timezone(timedelta(hours=a.tz))
    start = datetime.strptime(a.start, "%Y-%m-%d").date()

    plan = []
    for i, v in enumerate(vids):
        num = int(re.search(r"(\d+)", v.stem).group(1))
        day = start + timedelta(days=i // len(SLOTS))
        hour = SLOTS[i % len(SLOTS)]
        local_dt = datetime(day.year, day.month, day.day, hour, 0, tzinfo=tzoff)
        utc_dt = local_dt.astimezone(timezone.utc)
        title, desc = meta.get(num, (v.stem, ""))
        title = title[:100]
        if "#shorts" not in title.lower() and "#shorts" not in desc.lower():
            desc = (desc + "\n\n#shorts").strip()
        plan.append((v, num, local_dt, utc_dt, title, desc))

    print(f"канал={a.channel} | {len(plan)} шортсов | 2/день 9:00 и 21:00 (UTC{a.tz:+g}) | "
          f"старт {a.start}\n")
    for v, num, ld, ud, title, _ in plan:
        mark = "✓залит" if str(num) in done else "      "
        print(f"  {mark} #{num:02d} {ld:%d.%m %H:%M} местн ({ud:%Y-%m-%dT%H:%M:%SZ})  {title[:48]}")
    if not a.go:
        print("\n(dry-run — добавь --go чтобы залить с расписанием)")
        return 0

    from googleapiclient.http import MediaFileUpload
    from googleapiclient.errors import HttpError
    yt = get_service(a.channel)
    up = 0
    for v, num, ld, ud, title, desc in plan:
        if str(num) in done:
            continue
        if a.max and up >= a.max:
            print(f"\n[стоп] достигнут лимит --max={a.max} за запуск; остальные — следующим запуском")
            break
        body = {"snippet": {"title": title, "description": desc,
                            "categoryId": CATEGORY_GAMING, "defaultLanguage": lang,
                            "defaultAudioLanguage": lang},
                "status": {"privacyStatus": "private",
                           "publishAt": ud.strftime("%Y-%m-%dT%H:%M:%SZ"),
                           "selfDeclaredMadeForKids": False}}
        media = MediaFileUpload(str(v), chunksize=1024 * 1024 * 4, resumable=True, mimetype="video/*")
        req = yt.videos().insert(part="snippet,status", body=body, media_body=media)
        try:
            resp = None
            while resp is None:
                _, resp = req.next_chunk()
        except HttpError as e:
            if "quota" in str(e).lower():
                print(f"\n[квота] дневная квота YouTube исчерпана на #{num:02d}. "
                      f"Залито за запуск: {up}. Остальные — завтра (квота сбросится).")
                break
            raise
        done[str(num)] = resp["id"]
        state_f.write_text(json.dumps(done, ensure_ascii=False))
        up += 1
        print(f"  ✓ #{num:02d} → https://youtu.be/{resp['id']}  публикация {ld:%d.%m %H:%M} местн")
    left = [n for v, n, *_ in plan if str(n) not in done]
    print(f"\nЗалито за запуск: {up} | всего готово: {len(done)}/{len(plan)} | осталось: {left or '—'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
