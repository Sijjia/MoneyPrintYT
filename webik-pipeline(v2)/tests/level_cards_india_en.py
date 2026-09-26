"""EN-плашки уровней «Iceberg of India»: печатная машинка из EN level-анонсов, укладка на V4,
удаление русской шаблонной MOGRT «1 УРОВЕНЬ» (V1). Premiere открыт с EN-проектом."""
import sys, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import pymiere
from services.text.apocalypse_card import render_topic_card_typewriter

EN = ROOT / "projects" / "2026-09-22_aysberg-indii-misticheskaya-i-zagadochnaya-storona-strany_EN"
CARDS = EN / "assets" / "level_cards"; CARDS.mkdir(parents=True, exist_ok=True)
V4 = 3

# (scene, start, slot, EN text) — из EN закадра level-анонса
LEVELS = [
    ("scene_007", 34.5, 3.0, "Level One. The Tip of the Iceberg."),
    ("scene_062", 370.1, 2.6, "Level Two. The Water's Surface."),
    ("scene_116", 698.3, 3.2, "Level Three. The Descent."),
    ("scene_175", 1075.9, 2.6, "Level Four. The Abyss."),
]


def es(js): return pymiere.core.eval_script(js)


def main() -> int:
    for sid, st, slot, text in LEVELS:
        out = CARDS / f"level_{sid}_en.mov"
        p, dur = render_topic_card_typewriter(text, out, total_target=slot)
        path = str(Path(p).resolve()).replace("\\", "/")
        js = ('(function(){var proj=app.project;'
              f'proj.importFiles(["{path}"], true, proj.rootItem, false);var root=proj.rootItem,item=null;'
              f'for(var i=root.children.numItems-1;i>=0;i--){{if(root.children[i].name.indexOf("level_{sid}_en")>=0){{item=root.children[i];break;}}}}'
              f'if(!item)return "NOITEM";var tr=proj.activeSequence.videoTracks[{V4}];tr.overwriteClip(item,{st});return "OK";}})()')
        print(f"{sid}: {es(js)} «{text}» ({dur:.1f}s)", flush=True)

    rem = es('(function(){var t=app.project.activeSequence.videoTracks[0],n=0;'
             'for(var i=t.clips.numItems-1;i>=0;i--){var c=t.clips[i];'
             'if(c.start.seconds<45&&c.name.indexOf("Graphic")>=0){c.remove(false,false);n++;}}return "removed="+n;})()')
    print("V1 MOGRT:", rem, flush=True)
    es('app.project.save();')
    return 0


if __name__ == "__main__":
    sys.exit(main())
