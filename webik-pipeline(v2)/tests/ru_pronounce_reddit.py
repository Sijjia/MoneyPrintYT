"""Нормализатор произношения для RU-озвучки ролика «Айсберг Reddit».
ГЛАВНОЕ: символ «/» в r/... TTS читал как «слэш» — убираем. r/X → «сабреддит X», латиница →
кириллическая фонетика, коды-названия оставляем читаемыми. Применяется к ТЕКСТУ РЕЧИ перед синтезом
(scenes.json/плашки НЕ трогаем).
  echo "r/nosleep" | python tests/ru_pronounce_reddit.py"""
import re

# латиница → кириллица: СНАЧАЛА длинные/составные. Регистронезависимо, по границам «слова»
# (где «/» и «_» считаются границей, чтобы имя внутри r/... и Solving_A858 тоже ловилось).
MAP = [
    # площадки/бренды
    ("Reddit", "Реддит"), ("subreddit", "сабреддит"), ("YouTube", "Ютуб"), ("TikTok", "Тикток"),
    ("Twitch", "Твич"), ("Discord", "Дискорд"), ("WhatsApp", "Вотсап"), ("Facebook", "Фейсбук"),
    ("VKontakte", "ВКонтакте"), ("Snopes", "Снопс"), ("BuzzFeed", "Базфид"), ("Scroll.in", "Скролл-ин"),
    ("KnowYourMeme", "Ноу-Ёр-Мим"), ("Whang", "Вэнг"), ("Guardian", "Гардиан"), ("Angelfire", "Энджелфайр"),
    ("GadgetZZ", "Гаджет-Зет-Зет"), ("4chan", "форчан"), ("Guinness", "Гиннесс"),
    # названия историй/тем (латиницей)
    ("The NoSleep Podcast", "Зе Нослип Подкаст"), ("nosleep", "нослип"), ("NoSleep", "Нослип"),
    ("MandelaEffect", "Мандела Эффект"), ("backrooms", "бэкрумс"), ("Backrooms", "Бэкрумс"),
    ("Penpal", "Пенпал"), ("Borrasca", "Борраска"), ("Psychosis", "Психозис"),
    ("Cicada 3301", "Цикада три триста один"), ("Cicada", "Цикада"),
    ("Liber Primus", "Либер Примус"), ("Blue Whale", "Блю Вейл"), ("Momo", "Момо"),
    ("Mother Bird", "Мазер Бёрд"), ("This Man", "Зис Мэн"),
    ("Swamps of Dagobah", "Свэмпс оф Дагоба"), ("Dagobah", "Дагоба"),
    ("Lake City Quiet Pills", "Лейк Сити Куайет Пиллс"),
    ("Ted the Caver", "Тед зе Кейвер"), ("Dionaea House", "Дионея Хаус"),
    ("Tinder", "Тиндер"), ("chadfish", "чэдфиш"), ("Chad", "Чэд"),
    # ники/имена (латиницей)
    ("The_Dalek_Emperor", "Зе Далек Эмперор"), ("1000Vultures", "тысяча Валчерс"),
    ("Parker Warner Wright", "Паркер Уорнер Райт"), ("Ooer", "Ооэр"),
    ("Solving_A858", "Солвинг А-восемь-пять-восемь"), ("A858", "А-восемь-пять-восемь"),
    ("Berenstein", "Беренстин"), ("Berenstain", "Беренстейн"),
    ("Unresolved Mysteries", "Анрезолвд Мистериз"), ("findbostonbombers", "файнд-бостон-бомберс"),
]

_COMPILED = [(re.compile(r"(?<![A-Za-zА-Яа-яЁё0-9])" + re.escape(lat) + r"(?![A-Za-zА-Яа-яЁё0-9])", re.I), cyr)
             for lat, cyr in MAP]

# r/Имя → «сабреддит Имя» (символ «/» больше НЕ произносится). Ловим и латиницу, и уже транслитом.
_SUB = re.compile(r"\br/([A-Za-zА-Яа-яЁё0-9_]+)")
# «slash x» (LLM так расшифровал /x/) и любые «слэш/slash» → убрать
_SLASHWORD = re.compile(r"\bslash\s+([A-Za-zА-Яа-яЁё])", re.I)


def normalize(text: str) -> str:
    # 1) латиница → кириллица (в т.ч. имя внутри r/nosleep станет r/нослип)
    for pat, cyr in _COMPILED:
        text = pat.sub(cyr, text)
    # 2) «slash x» (борда /x/ форчана) → «икс»; прочий «slash» убрать
    text = re.sub(r"\bslash\s+x\b", "икс", text, flags=re.I)
    text = _SLASHWORD.sub(r"\1", text)
    text = re.sub(r"\bslash\b", " ", text, flags=re.I)
    # 3) r/Имя → «сабреддит Имя»
    text = _SUB.sub(lambda m: "сабреддит " + m.group(1), text)
    # 4) схлопнуть повтор «сабреддит сабреддит» (если в тексте уже было «сабреддит r/…»)
    text = re.sub(r"\b(сабреддит)(\s+сабреддит)+\b", r"\1", text, flags=re.I)
    # 5) страховка: любой оставшийся «/» между словами → пробел (не «слэш»)
    text = re.sub(r"\s*/\s*", " ", text)
    return re.sub(r"[ ]{2,}", " ", text)


if __name__ == "__main__":
    import sys
    t = sys.stdin.read() if not sys.argv[1:] else " ".join(sys.argv[1:])
    print(normalize(t))
