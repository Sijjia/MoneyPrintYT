"""
services/text/ner.py
Извлечение entities из voiceover для размещения overlay-карточек.

Архитектура:
- DATE / NUMBER — через regex (быстро, не нужна модель)
- PERSON / LOC / ORG — через spaCy `ru_core_news_lg`
- Каждая entity матчится на whisper-words → точные start/end timestamps

Возвращает list of dicts:
    {"type": "DATE"|"NUMBER"|"PERSON"|"LOC"|"ORG",
     "text": "1962 году",
     "start": 12.34,
     "end": 13.10}
"""
import re
from typing import Dict, List, Optional

from core.logger import setup_logger
from services.stt.aligner import _normalize_word

log = setup_logger("ner")

# Кэш модели — одна загрузка на процесс
_NLP = None
_MORPH = None
_MORPH_TRIED = False


def _ensure_nlp():
    global _NLP
    if _NLP is not None:
        return _NLP
    try:
        import spacy
        log.info("Загружаю spaCy ru_core_news_lg...")
        _NLP = spacy.load("ru_core_news_lg")
        return _NLP
    except Exception as e:
        log.warning(f"spaCy load failed: {e}")
        return None


def _ensure_morph():
    """pymorphy3 — точная морфология для русского, для приведения к им.падежу."""
    global _MORPH, _MORPH_TRIED
    if _MORPH is not None or _MORPH_TRIED:
        return _MORPH
    _MORPH_TRIED = True
    try:
        import pymorphy3
        _MORPH = pymorphy3.MorphAnalyzer()
        return _MORPH
    except Exception as e:
        log.warning(f"pymorphy3 не доступен: {e}")
        return None


def _to_nominative(word: str) -> Optional[str]:
    """Приводит слово к именительному падежу через pymorphy3.

    Returns None если pymorphy3 не установлен или не смог разобрать.
    Сохраняет регистр первой буквы.
    """
    morph = _ensure_morph()
    if morph is None:
        return None
    try:
        parses = morph.parse(word)
        if not parses:
            return None
        p = parses[0]
        # Если уже в им.падеже — возвращаем как есть (нормальная форма)
        infl = p.inflect({"nomn"})
        if infl is None:
            return None
        nom = infl.word
        if not nom:
            return None
        if word[:1].isupper():
            nom = nom[:1].upper() + nom[1:]
        return nom
    except Exception:
        return None


# === Regex patterns для DATE и NUMBER ===

_MONTHS = (
    r"январ[ьяюе]|феврал[ьяюе]|март[аоуе]?|апрел[ьяюе]|"
    r"ма[йяюе]|июн[ьяюе]|июл[ьяюе]|август[аоуе]?|"
    r"сентябр[ьяюе]|октябр[ьяюе]|ноябр[ьяюе]|декабр[ьяюе]"
)

DATE_PATTERNS = [
    # «1953 год», «в 1962 году», «1900-х годов»
    (re.compile(r"\b(\d{4}\s*(?:год[ауе]?|г\.|гг\.|годов))\b", re.IGNORECASE), "DATE"),
    # «23 февраля 1962», «23 февраля»
    (
        re.compile(rf"\b(\d{{1,2}}\s+(?:{_MONTHS})(?:\s+\d{{4}})?)\b", re.IGNORECASE),
        "DATE",
    ),
    # «12.04.1961», «23/05/2001»
    (re.compile(r"\b(\d{1,2}[./]\d{1,2}[./]\d{2,4})\b"), "DATE"),
    # «XX век», «XIX века»
    (re.compile(r"\b((?:XIX|XX|XXI|XVII|XVIII)\s*век[ауе]?)\b", re.IGNORECASE), "DATE"),
]

NUMBER_PATTERNS = [
    # «60 миллионов жертв», «1500 метров», «5 тысяч человек»
    (
        re.compile(
            r"\b(\d{1,3}(?:[\s,.]\d{3})*"
            r"\s*(?:тысяч\w*|миллион\w*|миллиард\w*|млн|млрд|тыс\.?)"
            r"(?:\s+\w+)?)\b",
            re.IGNORECASE,
        ),
        "NUMBER",
    ),
    # «200%», «150 процентов»
    (re.compile(r"\b(\d+\s*(?:%|процент\w*))\b", re.IGNORECASE), "NUMBER"),
    # «60 человек», «20 жертв», «1500 метров» — числа с keyword unit
    (
        re.compile(
            r"\b(\d{1,3}(?:[\s,.]\d{3})*\s*"
            r"(?:человек|жертв\w*|погибш\w*|раненых?|мёртв\w*|"
            r"метр\w*|км|километр\w*|тонн\w*|"
            r"лет|год[ауе]?|часов?|минут\w*|секунд\w*|"
            r"доллар\w*|рубл\w+|евро))\b",
            re.IGNORECASE,
        ),
        "NUMBER",
    ),
]


def _lemmatize_entity(ent) -> str:
    """Возвращает entity в им.падеже для отображения зрителю.

    Сначала пробует pymorphy3 (точная морфология RU) для каждого токена,
    затем fallback на spaCy lemma_. Аббревиатуры (СССР, США, ООН) — без изменений.
    """
    out_tokens: List[str] = []

    for tok in ent:
        if tok.is_punct or tok.is_space:
            continue
        original = tok.text

        # Аббревиатура — все буквы заглавные и >=2, и строго буквы → не трогаем
        if len(original) >= 2 and original.isupper() and original.isalpha():
            out_tokens.append(original)
            continue

        # 1) pymorphy3 → именительный падеж
        nom = _to_nominative(original)
        if nom and len(nom) >= 2:
            out_tokens.append(nom)
            continue

        # 2) spaCy lemma_ как fallback
        lemma = (tok.lemma_ or "").strip()
        if lemma and lemma not in ("-", "_") and len(lemma) >= 2:
            if lemma.lower() != original.lower():
                if original[:1].isupper():
                    lemma = lemma[:1].upper() + lemma[1:]
                out_tokens.append(lemma)
                continue

        # 3) ничего не сработало — оригинал
        out_tokens.append(original)

    return " ".join(out_tokens).strip() or ent.text.strip()


def _find_word_index_for_char(char_idx: int, words_chars: List[int]) -> int:
    """Бинарный поиск индекса слова по позиции символа в полном тексте."""
    lo, hi = 0, len(words_chars) - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if words_chars[mid] <= char_idx:
            lo = mid + 1
        else:
            hi = mid
    return max(0, lo - 1)


def _build_word_timestamps(text: str, whisper_words: List[Dict]):
    """Сопоставляет позиции whisper-words с char-индексами в исходном `text`.

    Returns:
        (word_chars: List[int], whisper_words_filtered: List[Dict])
    Где word_chars[i] = char-индекс начала i-го слова в text.
    """
    word_chars: List[int] = []
    cursor = 0
    matched: List[Dict] = []
    for w in whisper_words:
        token = (w.get("word") or "").strip()
        if not token:
            continue
        # Удаляем пунктуацию для поиска
        norm = _normalize_word(token)
        if not norm:
            continue
        # Ищем эту же норму в text начиная с cursor
        # Простая heuristic: lowercase + skip non-word
        text_lower = text.lower()
        # Берём первое occurrence нормы в lowercase позиции >= cursor
        # Чтобы не путаться с одинаковыми словами — двигаемся вперёд
        pos = text_lower.find(norm, cursor)
        if pos < 0:
            # Whisper может расслышать другое слово — пропускаем
            continue
        word_chars.append(pos)
        matched.append(w)
        cursor = pos + len(norm)
    return word_chars, matched


def _resolve_span_timestamps(
    char_start: int,
    char_end: int,
    word_chars: List[int],
    whisper_words: List[Dict],
) -> Optional[Dict]:
    """Возвращает {start, end} в секундах для span [char_start, char_end] в тексте."""
    if not word_chars:
        return None
    start_idx = _find_word_index_for_char(char_start, word_chars)
    end_idx = _find_word_index_for_char(char_end - 1, word_chars)
    if start_idx >= len(whisper_words) or end_idx >= len(whisper_words):
        return None
    return {
        "start": float(whisper_words[start_idx]["start"]),
        "end": float(whisper_words[end_idx]["end"]),
    }


def extract_entities(text: str, whisper_words: List[Dict]) -> List[Dict]:
    """Извлекает entities + их таймштампы.

    Returns list of dicts отсортированных по start времени.
    Дедупликация по (type, text, start) — один entity не дублируется.
    """
    if not text or not whisper_words:
        return []

    word_chars, matched_words = _build_word_timestamps(text, whisper_words)
    if not word_chars:
        log.warning("Не удалось сопоставить whisper-words с текстом")
        return []

    raw: List[Dict] = []

    # 1) Regex DATE / NUMBER
    for patterns in (DATE_PATTERNS, NUMBER_PATTERNS):
        for pattern, etype in patterns:
            for m in pattern.finditer(text):
                span_text = m.group(1).strip()
                ts = _resolve_span_timestamps(m.start(1), m.end(1), word_chars, matched_words)
                if not ts:
                    continue
                raw.append({"type": etype, "text": span_text, **ts})

    # 2) spaCy PER / LOC / ORG
    nlp = _ensure_nlp()
    if nlp is not None:
        try:
            doc = nlp(text)
            for ent in doc.ents:
                if ent.label_ not in ("PER", "LOC", "ORG"):
                    continue
                etype = {"PER": "PERSON", "LOC": "LOC", "ORG": "ORG"}[ent.label_]
                ts = _resolve_span_timestamps(ent.start_char, ent.end_char, word_chars, matched_words)
                if not ts:
                    continue
                # Lemma → им.падеж для отображения: «Кореи» → «Корея», «Северной Кореи» → «Северная Корея»
                display = _lemmatize_entity(ent)
                raw.append({"type": etype, "text": display, **ts})
        except Exception as e:
            log.warning(f"spaCy NER упал: {e}")

    # Дедуп по (type, text, round(start,1))
    seen = set()
    unique: List[Dict] = []
    for ent in sorted(raw, key=lambda x: x["start"]):
        key = (ent["type"], ent["text"].lower(), round(ent["start"], 1))
        if key in seen:
            continue
        seen.add(key)
        unique.append(ent)
    return unique
