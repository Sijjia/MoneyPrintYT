"""Quick NER smoke test — без pytest, просто прогон на богатом тексте."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.text.ner import extract_entities


text = (
    "В 1962 году Сталин отдал приказ. Погибло 60 миллионов человек "
    "в СССР и Чернобыле. Кеннеди узнал об этом 23 февраля."
)

words = [
    {"word": "В", "start": 0.0, "end": 0.2},
    {"word": "1962", "start": 0.2, "end": 0.7},
    {"word": "году", "start": 0.7, "end": 1.0},
    {"word": "Сталин", "start": 1.1, "end": 1.5},
    {"word": "отдал", "start": 1.5, "end": 1.9},
    {"word": "приказ.", "start": 1.9, "end": 2.3},
    {"word": "Погибло", "start": 2.4, "end": 2.8},
    {"word": "60", "start": 2.8, "end": 3.0},
    {"word": "миллионов", "start": 3.0, "end": 3.5},
    {"word": "человек", "start": 3.5, "end": 4.0},
    {"word": "в", "start": 4.0, "end": 4.1},
    {"word": "СССР", "start": 4.1, "end": 4.5},
    {"word": "и", "start": 4.5, "end": 4.6},
    {"word": "Чернобыле.", "start": 4.6, "end": 5.2},
    {"word": "Кеннеди", "start": 5.4, "end": 5.9},
    {"word": "узнал", "start": 5.9, "end": 6.3},
    {"word": "об", "start": 6.3, "end": 6.5},
    {"word": "этом", "start": 6.5, "end": 6.8},
    {"word": "23", "start": 6.9, "end": 7.2},
    {"word": "февраля.", "start": 7.2, "end": 7.7},
]

ents = extract_entities(text, words)
print(f"Найдено {len(ents)} entities:")
for e in ents:
    print(f"  {e['type']:8} | {e['text']:25} | {e['start']:.2f}-{e['end']:.2f}")
