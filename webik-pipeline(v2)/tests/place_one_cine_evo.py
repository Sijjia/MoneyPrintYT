import sys,os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pathlib import Path
import pymiere
from pymiere.wrappers import time_from_seconds
from services.premiere_template.timeline_ops import import_media
ROOT=Path(__file__).resolve().parent.parent
CINE=ROOT/"projects"/"2026-08-18_aysberg-evolyutsii-temnaya-i-zapretnaya-storona-evolyutsii-o"/"assets"/"cine"
MOV=CINE/"cine_lasthuman.mov"; START=271.5
seq=pymiere.objects.app.project.activeSequence
v8=seq.videoTracks[7]
item=import_media(MOV)
v8.overwriteClip(item, time_from_seconds(START))
pymiere.objects.app.project.save()
print("OK cine_lasthuman на V8 @04:31; сохранено")
