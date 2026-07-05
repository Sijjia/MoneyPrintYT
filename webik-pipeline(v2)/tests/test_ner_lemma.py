"""Проверка lemma-нормализации на падежных формах."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.text.ner import extract_entities

text = (
    "В 1953 году в Северной Кореи произошёл инцидент. "
    "Ким Ир Сен встретился с представителями США и ООН. "
    "Из Москвы в Пекин отправили делегацию."
)

words = []
t = 0.0
for w in text.replace(".", "").replace(",", "").split():
    dur = 0.05 + 0.05 * len(w)
    words.append({"word": w, "start": t, "end": t + dur})
    t += dur + 0.05

ents = extract_entities(text, words)
print(f"Найдено {len(ents)} entities:")
for e in ents:
    print(f"  {e['type']:8} | {e['text']:25} | {e['start']:.2f}-{e['end']:.2f}")
