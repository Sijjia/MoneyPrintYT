"""Загрузка ролика на YouTube через Data API v3 (OAuth installed-app).
Грузит как PRIVATE-черновик (по умолчанию) — публикация ТОЛЬКО с --publish (после «ок» Айдара).
Два канала: --channel webik|debik (свои OAuth-токены).

Каналы (РАЗНЫЕ аккаунты):  debik = islamicrusick@gmail.com (EN) | webik = lillygameskg@gmail.com (RU)

Одноразовая настройка (Айдар):
  1) console.cloud.google.com → создать проект → включить "YouTube Data API v3"
  2) OAuth consent screen (External, Testing) → в Test users добавить ОБА:
       islamicrusick@gmail.com  и  lillygameskg@gmail.com
  3) Credentials → Create OAuth client ID → Desktop app → скачать JSON
  4) положить как  secrets/yt_client_secret.json
Сначала вход (откроет браузер):
  ! ../webik-pipeline/.venv/Scripts/python.exe tests/yt_upload.py --channel debik --auth-only
Затем заливка (EN → Debik, язык en для EN-аудитории; RU-видео заливается отдельно на webik с lang ru):
  ! ../webik-pipeline/.venv/Scripts/python.exe tests/yt_upload.py --channel debik \
      --video "E:/video for ytb/Deb1k/Iceberg GTA/Iceberg GTA_EN.mp4" \
      --meta  "E:/video for ytb/Deb1k/Iceberg GTA/meta_EN.md" \
      --thumb "E:/video for ytb/Deb1k/Iceberg GTA/thumb_EN_yt.jpg"
Первый запуск откроет браузер — войти именно в аккаунт нужного канала (Debik→islamicrusick,
Webik→lillygameskg); токен ляжет в secrets/yt_token_<channel>.json и переиспользуется.
БЕЗ --publish видео приватное (черновик)."""
import argparse, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SECRETS = ROOT / "secrets"
SECRETS.mkdir(exist_ok=True)
CLIENT_SECRET = SECRETS / "yt_client_secret.json"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload",
          "https://www.googleapis.com/auth/youtube"]
CATEGORY_GAMING = "20"


def parse_meta(p: Path):
    """meta_*.md: строка1=title, дальше описание; хвост TAGS: a, b, c."""
    raw = p.read_text(encoding="utf-8").splitlines()
    title = raw[0].strip().lstrip("# ").strip()
    tags = []
    body = []
    for ln in raw[1:]:
        if ln.strip().upper().startswith(("TAGS:", "ТЕГИ:")):
            tags = [t.strip() for t in ln.split(":", 1)[1].split(",") if t.strip()]
        else:
            body.append(ln)
    desc = "\n".join(body).strip()
    return title[:100], desc[:4900], tags[:60]


def get_service(channel: str):
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    token = SECRETS / f"yt_token_{channel}.json"
    creds = None
    if token.exists():
        creds = Credentials.from_authorized_user_file(str(token), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CLIENT_SECRET.exists():
                sys.exit(f"НЕТ {CLIENT_SECRET} — сначала одноразовая настройка (см. шапку файла)")
            flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET), SCOPES)
            creds = flow.run_local_server(port=0, prompt="consent",
                                          authorization_prompt_message=f"Войди в аккаунт канала «{channel}»")
        token.write_text(creds.to_json(), encoding="utf-8")
    return build("youtube", "v3", credentials=creds)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--channel", required=True, choices=["webik", "debik"])
    ap.add_argument("--auth-only", action="store_true",
                    help="только вход в аккаунт (OAuth) и сохранение токена, без заливки")
    ap.add_argument("--video")
    ap.add_argument("--meta")
    ap.add_argument("--thumb")
    ap.add_argument("--lang", default=None, help="ru|en (по умолчанию по каналу)")
    ap.add_argument("--loc-meta", nargs=2, action="append", metavar=("LANG", "META_MD"), default=[],
                    help="доп. локализация: язык + meta_*.md (можно несколько раз) — YouTube покажет "
                         "зрителю заголовок/описание на его языке = макс охват")
    ap.add_argument("--publish", action="store_true", help="СРАЗУ public (иначе private-черновик)")
    ap.add_argument("--schedule", default=None, help="ISO8601 UTC для отложенной публикации, напр 2026-09-12T15:00:00Z")
    a = ap.parse_args()

    if a.auth_only:
        yt = get_service(a.channel)
        me = yt.channels().list(part="snippet", mine=True).execute()
        ch = me.get("items", [{}])[0].get("snippet", {}).get("title", "?")
        print(f"✓ вход выполнен для канала «{a.channel}» → YouTube: «{ch}» (токен сохранён)")
        return 0
    if not (a.video and a.meta):
        sys.exit("нужны --video и --meta (или используй --auth-only)")

    from googleapiclient.http import MediaFileUpload
    title, desc, tags = parse_meta(Path(a.meta))
    lang = a.lang or ("ru" if a.channel == "webik" else "en")
    status = {"privacyStatus": "public" if a.publish else "private",
              "selfDeclaredMadeForKids": False, "embeddable": True,
              "publicStatsViewable": True, "license": "youtube"}
    if a.schedule and not a.publish:
        status["privacyStatus"] = "private"
        status["publishAt"] = a.schedule  # отложенная = private+publishAt
    snippet = {"title": title, "description": desc, "tags": tags,
               "categoryId": CATEGORY_GAMING, "defaultAudioLanguage": lang,
               "defaultLanguage": lang}
    # локализации для охвата в других языках (заголовок+описание на языке зрителя)
    locs = {}
    for lc, mp in a.loc_meta:
        lt, ld, _ = parse_meta(Path(mp))
        locs[lc] = {"title": lt, "description": ld}
    body = {"snippet": snippet, "status": status}
    if locs:
        body["localizations"] = locs
    print(f"канал={a.channel} | privacy={status['privacyStatus']}"
          + (f" | publishAt={a.schedule}" if a.schedule else "")
          + f"\nTITLE: {title}\nTAGS: {len(tags)} | desc {len(desc)} симв."
          + (f" | локализации: {list(locs)}" if locs else ""))
    yt = get_service(a.channel)
    media = MediaFileUpload(a.video, chunksize=1024 * 1024 * 8, resumable=True, mimetype="video/*")
    parts = "snippet,status" + (",localizations" if locs else "")
    req = yt.videos().insert(part=parts, body=body, notifySubscribers=a.publish, media_body=media)
    resp = None
    while resp is None:
        st, resp = req.next_chunk()
        if st:
            print(f"  залито {int(st.progress()*100)}%", flush=True)
    vid = resp["id"]
    print(f"✓ видео загружено: https://youtu.be/{vid}  (studio: https://studio.youtube.com/video/{vid}/edit)")
    if a.thumb and Path(a.thumb).exists():
        yt.thumbnails().set(videoId=vid, media_body=MediaFileUpload(a.thumb)).execute()
        print("✓ превью установлено")
    print("СТАТУС:", "PUBLIC" if a.publish else ("SCHEDULED" if a.schedule else "PRIVATE-черновик (публикация вручную/по --publish)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
