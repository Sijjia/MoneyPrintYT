"""ДЕ-СЛОП пост-проход по готовому сценарию: второй LLM-проход убирает оставшийся нейрослоп
(мягкие «выводы-осмысления», зазывалки-переходы, предложения-выстрелы, триколоны), СОХРАНЯЯ
все факты, структуру (## уровни / ### темы / [пауза]) и примерно ту же длину. Ставить СРАЗУ
после генерации сценария, до нарезки на сцены.

Вход: путь к script.md (аргумент или SCRIPT_PATH env). Пишет рядом <name>.deslop.md и, если
DESLOP_INPLACE=1, перезаписывает исходный (с бэкапом <name>.raw.md).
  ../webik-pipeline/.venv/Scripts/python.exe tests/deslop_script.py <script.md>
"""
import os, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from services.llm.claude import ClaudeService
from tests.slop_lib import flag_sentence, split_sentences, score_text

SYSTEM = (
    "Ты — жёсткий редактор-чистильщик документальных сценариев (RU, формат «айсберг»). Тебе дают "
    "текст ОДНОЙ темы. Твоя работа — вычистить нейрослоп ПОЛНОСТЬЮ, НИЧЕГО не выдумывая и НЕ теряя "
    "фактов. Пиши как живой диктор: конкретика вместо пафоса, рваный ритм, простые глаголы, конец на факте."
)

RULES = """Перепиши текст темы, вычистив нейрослоп ПОЛНОСТЬЮ. ЖЕЛЕЗНО сохрани ВСЕ факты, имена, даты,
цифры, названия и примерно ту же длину (±10%). Не выдумывай новых фактов. Числа — прописью.

⚠️ ФАКТЫ СВЯЩЕННЫ: КАЖДАЯ цифра, сумма, дата, имя, ник, название компании/игры/предмета из оригинала
ОБЯЗАНА остаться в переписанном тексте — их НЕЛЬЗЯ сокращать, объединять или выкидывать. Если в
оригинале «Linkmon99», «Vice», «восемьдесят пять тысяч долларов», «тринадцать тысяч шестьсот пять» —
всё это должно быть и в ответе. Ты чистишь ТОЛЬКО пустой пафос и штампы, а НЕ факты. И НЕ добавляй
своих деталей (никаких «курьеров», «армий ботов» и прочего, чего нет в оригинале).

⛔ УДАЛИ/ПЕРЕПИШИ (это и есть нейрослоп):
1. ПУСТЫЕ предложения-значимости (нет ни имени/даты/цифры/факта, только оценка важности) — УДАЛЯЙ
   ЦЕЛИКОМ, не смягчай: «это стало символом…», «оставило неизгладимый след», «поворотный момент»,
   «навсегда изменило…», «вошло в историю», «служит напоминанием», «сыграло ключевую роль», «целая
   эпоха», «богатое наследие», «последствия были ошеломляющими». Тема кончается на предыдущем ФАКТЕ.
2. ЗАПРЕЩЁННЫЕ ОБОРОТЫ — вырезать всегда:
   • «не просто …, а …» / «не только …, но и …» / «это не X — это Y» (главный ИИ-маркер);
   • деепричастные хвосты-значимости «…, подчёркивая/символизируя/знаменуя/закрепляя/превратив…»;
   • зачины «В мире, где…», «Представьте…», «Что если…», «Давайте разберёмся»;
   • зазывалки «Погружаемся», «Спускаемся глубже», «Идём дальше», «Добро пожаловать», «Приготовьтесь»;
   • фейк-саспенс «Мало кто знал», «Но всё изменилось», «И вот тогда», «Или так им казалось»;
   • оговорки «Важно отметить», «Стоит отметить»; риторич.вопрос+мгновенный ответ.
3. Хеджи-филлеры: «поистине», «по-настоящему», «буквально», «фактически», «по сути», «пожалуй» — убрать.
4. Инфляционные прилагательные пачками и «правило трёх» (три прилагательных подряд) — оставить максимум одно по делу.
5. Предложения-выстрелы 1-3 слова ради драмы — склеить в связное или развернуть.

✅ КАК ДОЛЖНО ЗВУЧАТЬ (живой диктор):
- Конкретика вместо значимости: не «это было важно», а ЧТО именно — имя, дата, цифра, последствие.
- РИТМ: БОЛЬШИНСТВО предложений — длинные связные (10-20 слов, с союзами «и/а/когда/после чего/при этом»), текущие одно из другого. Короткие (3-6 слов) — ТОЧЕЧНО для акцента, НЕ подряд. НЕ руби весь текст на короткие обрубки — это тоже раздражает зрителя. Свинг: длинное → длинное → короткий акцент → длинное.
- Простые глаголы (показал/сделал/украл/закрыли), не «продемонстрировал/осуществил».
- ТИРЕ — редко (макс. одно на несколько предложений), чаще точка/запятая.
- Конец темы — на КОНКРЕТНОМ факте/цифре, без морали и «бантиков».
- Читается как речь вслух (это озвучка).

{FLAGGED_BLOCK}
Сохрани строки-заголовки (### / ##) и метки [пауза Nс] КАК ЕСТЬ. Верни ТОЛЬКО очищенный текст, без комментариев."""


def split_topics(md: str):
    """→ [(prefix_lines, body)] по темам ### ; заголовки уровней/паузы отдаём как «prefix» к след. блоку."""
    lines = md.splitlines()
    blocks, cur_header, cur_body = [], [], []
    def flush():
        if cur_header or cur_body:
            blocks.append(("\n".join(cur_header), "\n".join(cur_body).strip()))
    for ln in lines:
        if ln.startswith("### "):
            flush(); cur_header.clear(); cur_body.clear()
            cur_header.append(ln)
        elif ln.startswith("## ") or ln.strip() in ("[пауза 2с]", "[пауза 1.5с]", "[пауза 1с]"):
            # структурная строка вне тела — как отдельный «header-only» блок
            flush(); cur_header.clear(); cur_body.clear()
            blocks.append((ln, ""))
        else:
            cur_body.append(ln)
    flush()
    return blocks


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(os.environ["SCRIPT_PATH"])
    md = path.read_text(encoding="utf-8")
    blocks = split_topics(md)
    n_topics = sum(1 for h, b in blocks if b.strip())
    print(f"тем к чистке: {n_topics} | всего блоков: {len(blocks)}", flush=True)

    before = score_text(md)
    llm = ClaudeService(model="anthropic/claude-sonnet-4.5")
    out_parts, done = [], 0
    for header, body in blocks:
        if not body.strip():
            out_parts.append(header)
            continue
        # подсвечиваем модели КОНКРЕТНЫЕ слоп-предложения этой темы (детектор slop_lib)
        flagged = []
        for s in split_sentences(body):
            h = flag_sentence(s)
            if h:
                flagged.append(f'  • [{", ".join(h)}] «{s[:110]}»')
        fb = ("ДЕТЕКТОР УЖЕ НАШЁЛ В ЭТОМ ТЕКСТЕ СЛОП (обязательно исправь КАЖДОЕ):\n" +
              "\n".join(flagged[:20]) + "\n") if flagged else "Детектор явных шаблонов не нашёл — всё равно вычисти пафос и выровненный ритм.\n"
        prompt = RULES.replace("{FLAGGED_BLOCK}", fb) + "\n\nТЕКСТ ТЕМЫ:\n" + (header + "\n" if header else "") + body
        try:
            cleaned = llm.call(prompt, max_tokens=3000, temperature=0.2, system=SYSTEM).strip()
            cleaned = re.sub(r"^```.*$|^```$", "", cleaned, flags=re.M).strip()
        except Exception as e:
            print(f"  ✗ блок упал ({str(e)[:50]}) — оставляю как есть", flush=True)
            cleaned = (header + "\n\n" if header else "") + body
        # страховка: заголовок ### должен сохраниться
        if header.startswith("### ") and not cleaned.lstrip().startswith("### "):
            cleaned = header + "\n\n" + cleaned
        # СТРАХОВКА ФАКТОВ: латинские ИМЕНА/названия из оригинала не должны пропасть.
        # Игнорим дженерик-акронимы (RP/GTA/DLC/NPC/AO/FBI/CEO/UFO и т.п.) — они не «факты-имена».
        GENERIC = {"RP", "GTA", "DLC", "NPC", "AO", "FBI", "CEO", "UFO", "PC", "PS3", "PS4",
                   "TV", "USA", "UK", "AI", "HD", "ID", "URL", "GTAV", "GTAVI", "III", "IV"}
        def lat(t):
            out = set()
            for w in re.findall(r"[A-Za-z][A-Za-z0-9.\-]{2,}", t):
                base = w.strip(".-").upper()
                if base in GENERIC or (w.isupper() and len(w) <= 4):
                    continue
                out.add(w)
            return out
        lost = lat(body) - lat(cleaned)
        if lost:
            try:
                retry = llm.call(prompt + f"\n\n⚠ ТЫ ПОТЕРЯЛ названия/имена: {sorted(lost)}. "
                                 "Перепиши ЗАНОВО, вернув их ВСЕ на места, остальное так же чисто.",
                                 max_tokens=3000, temperature=0.2, system=SYSTEM).strip()
                retry = re.sub(r"^```.*$|^```$", "", retry, flags=re.M).strip()
                if header.startswith("### ") and not retry.lstrip().startswith("### "):
                    retry = header + "\n\n" + retry
                if not (lat(body) - lat(retry)):
                    cleaned = retry
                else:
                    print(f"    ⚠ всё ещё потеряны {sorted(lat(body)-lat(retry))[:6]} — откат к оригиналу", flush=True)
                    cleaned = (header + "\n\n" if header else "") + body
            except Exception:
                cleaned = (header + "\n\n" if header else "") + body
        out_parts.append(cleaned)
        done += 1
        print(f"  ✓ {done}/{n_topics} {header[:50]}", flush=True)

    cleaned_md = "\n\n".join(p for p in out_parts if p.strip())
    out = path.with_suffix(".deslop.md")
    out.write_text(cleaned_md, encoding="utf-8")
    after = score_text(cleaned_md)
    print(f"\n→ {out}", flush=True)
    print(f"СЛОП до→после: флагнуто {before['flagged_pct']}%→{after['flagged_pct']}% | "
          f"пустых {before['empty_pct']}%→{after['empty_pct']}% | "
          f"тире/1k {before['emdash_per_1k']}→{after['emdash_per_1k']} | "
          f"разброс длины {before['len_stdev']}→{after['len_stdev']}", flush=True)
    if os.environ.get("DESLOP_INPLACE") == "1":
        bak = path.with_suffix(".raw.md")
        if not bak.exists():
            bak.write_text(md, encoding="utf-8")
        path.write_text(cleaned_md, encoding="utf-8")
        print(f"перезаписан {path.name} (бэкап {bak.name})", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
