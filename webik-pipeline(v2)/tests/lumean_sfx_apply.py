"""Ставит новый Lumean-SFX-пул по битам анимаций (переиспользует sfx_choreograph)
и батч-опускает громкость A5/A6 до тихого уровня 0.12 за ОДИН eval_script
(не 98 python-round-trip'ов ~8мин).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pymiere
import tests.sfx_choreograph as choreo

VOL = 0.12  # тихий уровень (как одобрено ранее)

VOL_JS = """
function setVol(){
  var seq=app.project.activeSequence;
  var idxs=[4,5];  // A5, A6
  var done=0;
  for(var t=0;t<idxs.length;t++){
    var trk=seq.audioTracks[idxs[t]];
    for(var i=0;i<trk.clips.numItems;i++){
      var c=trk.clips[i], vc=null;
      for(var j=0;j<c.components.numItems;j++){ if(c.components[j].displayName.toLowerCase()=='volume'){vc=c.components[j];break;} }
      if(!vc) continue;
      var lp=null;
      for(var k=0;k<vc.properties.numItems;k++){ if(vc.properties[k].displayName.toLowerCase()=='level'){lp=vc.properties[k];break;} }
      if(!lp) continue;
      try{ lp.setValue(%f,true); done++; }catch(e){}
    }
  }
  return 'vol_set='+done;
}
setVol();
""" % VOL


def main() -> int:
    print("=== расстановка нового Lumean-пула по битам ===")
    rc = choreo.main()
    if rc != 0:
        print("хореография вернула ошибку"); return rc
    print("=== батч-громкость A5/A6 →", VOL, "===")
    res = pymiere.core.eval_script(VOL_JS)
    print("  ", res)
    pymiere.objects.app.project.save()
    print("готово, проект сохранён")
    return 0


if __name__ == "__main__":
    sys.exit(main())
