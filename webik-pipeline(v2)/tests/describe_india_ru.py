"""RU-описание для «Айсберг Индии» (Webik). Таймкоды и тексты плашек — ДИНАМИЧЕСКИ с RU-таймлайна
(level_card / topic_card из scenes.json + alignment.json). Пишет meta_RU.md в E:\\...\\Webik\\Айсберг Индии.
Webik-футер: телега + донат + почта (reference_description_links)."""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RU = ROOT / "projects" / "2026-09-22_aysberg-indii-misticheskaya-i-zagadochnaya-storona-strany"
OUT = Path(r"E:\video for ytb\Webik\Айсберг Индии")

TITLE = "АЙСБЕРГ ИНДИИ — проклятые форты, культы убийц, запертые сокровищницы и самые тёмные тайны страны"
HOOK = ("Индия — это не только Тадж-Махал и йога. Под поверхностью прячется мир проклятий, запретных "
        "храмов и загадок, которые наука до сих пор не может объяснить. От аскетов-агхори Варанаси и "
        "храма крыс Карни Мата до озера скелетов Рупкунд, деревни, где птицы падают с неба, культа "
        "душителей Кали, запечатанной Двери B храма Падманабхасвами на миллиарды долларов и запретного "
        "острова Северный Сентинел — это полный айсберг Индии, от поверхностных легенд до самого тёмного дна.")

TAGS = ["айсберг индии", "тёмная сторона индии", "агхори", "варанаси", "тхаги", "культ кали", "рупкунд",
        "озеро скелетов", "джатинга", "деревня близнецов кодинхи", "храм падманабхасвами", "дверь b",
        "северный сентинел", "джон аллен чау", "храм крыс карни мата", "форт бхангарх", "кулдхара",
        "кумбха мела", "загадки индии", "айсберг", "документалка индия", "мистика индии"]

FOOTER = ["НАШ ТЕЛЕГРАМ-КАНАЛ – https://t.me/webik_studio", "",
          "Поддержка канала - https://www.donationalerts.com/r/webikstudio", "",
          "По сотрудничеству пишите - aidarbekr2@gmail.com"]


def tc(s): return f"{int(s // 60):02d}:{int(s % 60):02d}"


def main() -> int:
    sc = json.loads((RU / "scenes.json").read_text(encoding="utf-8"))["scenes"]
    al = json.loads((RU / "assets" / "alignment.json").read_text(encoding="utf-8"))["scenes"]
    rows = [(0.0, "Интро", "intro")]
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

    parts = [TITLE, "", HOOK, "", "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬", "ТАЙМКОДЫ:"]
    parts += lines
    parts += ["", "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬"] + FOOTER + ["", "ТЕГИ: " + ", ".join(TAGS)]
    txt = "\n".join(parts)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "meta_RU.md").write_text(txt, encoding="utf-8")
    print(f"meta_RU.md → {OUT}")
    print(f"TITLE: {TITLE}")
    print(f"topics: {sum(1 for r in rows if r[2]=='topic')} | levels: {sum(1 for r in rows if r[2]=='level')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
