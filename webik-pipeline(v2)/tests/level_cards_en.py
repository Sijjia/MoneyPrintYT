"""EN-плашки уровней: рендер печатной машинкой (как топик-карточки) для 4 level-сцен из EN-закадра,
укладка на V4, удаление русской шаблонной MOGRT «1 УРОВЕНЬ» (V1). Premiere открыт с EN-проектом."""
import sys, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import pymiere
from services.text.apocalypse_card import render_topic_card_typewriter

EN = ROOT / "projects" / "2026-09-13_aysberg-reddit-strannaya-i-trevozhnaya-storona_EN"
CARDS = EN / "assets" / "level_cards"; CARDS.mkdir(parents=True, exist_ok=True)
V4 = 3

# (scene, start, slot, EN text)  — текст = закадр level-анонса
LEVELS = [
    ("scene_006", 23.1, 4.2, "Level One. The Tip of the Iceberg."),
    ("scene_062", 401.9, 3.2, "Level Two. Still Waters."),
    ("scene_115", 804.1, 3.6, "Level Three. The Descent."),
    ("scene_171", 1195.6, 4.1, "Level Four. The Abyss."),
]


def es(js):
    return pymiere.core.eval_script(js)


def main() -> int:
    for sid, st, slot, text in LEVELS:
        out = CARDS / f"level_{sid}_en.mov"
        p, dur = render_topic_card_typewriter(text, out, total_target=slot)
        path = str(Path(p).resolve()).replace("\\", "/")
        js = ('(function(){var proj=app.project;'
              f'proj.importFiles(["{path}"], true, proj.rootItem, false);'
              'var root=proj.rootItem,item=null;'
              f'for(var i=root.children.numItems-1;i>=0;i--){{if(root.children[i].name.indexOf("level_{sid}_en")>=0){{item=root.children[i];break;}}}}'
              'if(!item)return "NOITEM";'
              f'var tr=proj.activeSequence.videoTracks[{V4}];tr.overwriteClip(item,{st});return "OK";}})()')
        print(f"{sid}: {es(js)} «{text}» ({dur:.1f}s)", flush=True)

    # удалить русскую шаблонную плашку «1 УРОВЕНЬ» на V1 (Graphic возле 22-26с)
    rem = es('(function(){var t=app.project.activeSequence.videoTracks[0],n=0;'
             'for(var i=t.clips.numItems-1;i>=0;i--){var c=t.clips[i];'
             'if(c.start.seconds<40&&c.name.indexOf("Graphic")>=0){c.remove(false,false);n++;}}return "removed="+n;})()')
    print("V1 MOGRT:", rem, flush=True)
    # cleanup tiny + save
    print("clean:", es('(function(){var t=app.project.activeSequence.videoTracks[3],n=0;'
          'for(var j=t.clips.numItems-1;j>=0;j--){var c=t.clips[j];if((c.end.seconds-c.start.seconds)<0.15){c.remove(false,false);n++;}}'
          'app.project.save();return "tiny="+n;})()'), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
