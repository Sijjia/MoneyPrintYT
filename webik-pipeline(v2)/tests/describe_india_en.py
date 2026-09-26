"""EN-описание для «Iceberg of India» (Debik). Таймкоды и тексты плашек — ДИНАМИЧЕСКИ с EN-таймлайна
(level_card / topic_card из scenes.json + alignment.json). Пишет meta_EN.md в E:\\...\\Deb1k\\Iceberg India.
Debik-футер: только Subscribe (ссылок пока нет — см. reference_description_links)."""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EN = ROOT / "projects" / "2026-09-22_aysberg-indii-misticheskaya-i-zagadochnaya-storona-strany_EN"
OUT = Path(r"E:\video for ytb\Deb1k\Iceberg India")

TITLE = "The INDIA ICEBERG — Cursed Forts, Killer Cults, Sealed Vaults & the Darkest Mysteries of India"
HOOK = ("India is more than the Taj Mahal and yoga. Beneath the surface lies a world of curses, forbidden "
        "temples and mysteries science still can't fully explain. From the ash-covered Aghori of Varanasi "
        "and the rat temple of Karni Mata to the Skeleton Lake of Roopkund, the village where birds fall "
        "from the sky, the Thuggee strangler cult of Kali, the sealed Vault B of the Padmanabhaswamy Temple "
        "worth billions, and the forbidden North Sentinel Island — this is the full iceberg of India, from "
        "the surface legends down to the coldest, darkest depths.")

TAGS = ["india iceberg", "india dark side", "aghori", "varanasi", "thuggee", "cult of kali", "roopkund",
        "skeleton lake", "jatinga", "kodinhi twins", "padmanabhaswamy temple", "vault b", "north sentinel",
        "john allen chau", "karni mata rat temple", "bhangarh fort", "kuldhara", "kumbh mela",
        "indian mysteries", "iceberg explained", "india documentary", "unexplained india"]

FOOTER = ["👉 Subscribe for more deep-dive world icebergs."]


def tc(s): return f"{int(s // 60):02d}:{int(s % 60):02d}"


def main() -> int:
    sc = json.loads((EN / "scenes.json").read_text(encoding="utf-8"))["scenes"]
    al = json.loads((EN / "assets" / "alignment.json").read_text(encoding="utf-8"))["scenes"]
    rows = [(0.0, "Intro", "intro")]
    for s in sc:
        vt = (s.get("visual") or {}).get("type")
        if vt not in ("level_card", "topic_card"):
            continue
        st = al.get(s["id"], {}).get("start", 0)
        txt = (s.get("voiceover") or (s.get("visual") or {}).get("text") or "").strip().rstrip(".")
        rows.append((st, txt, "level" if vt == "level_card" else "topic"))
    rows.sort(key=lambda r: (r[0], {"intro": 0, "level": 1, "topic": 2}[r[2]]))

    lines = []
    for st, t, k in rows:
        if k == "level":
            lines.append("")
            lines.append(f"{tc(st)} ▬ {t}")
        else:
            lines.append(f"{tc(st)} {t}")

    parts = [TITLE, "", HOOK, "", "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬", "TIMECODES:"]
    parts += lines
    parts += ["", "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬"] + FOOTER + ["", "TAGS: " + ", ".join(TAGS)]
    txt = "\n".join(parts)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "meta_EN.md").write_text(txt, encoding="utf-8")
    print(f"meta_EN.md → {OUT}")
    print(f"TITLE: {TITLE}")
    print(f"topics: {sum(1 for r in rows if r[2]=='topic')} | levels: {sum(1 for r in rows if r[2]=='level')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
