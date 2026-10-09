"""Эвристика: из постов, которых ещё нет в курируемом словаре, достаёт
кандидатов в заголовочные слова -> data/entries.auto.yml.

Курируемый entries.yml этот скрипт не трогает никогда.
Чтобы «узаконить» авто-статью, перенеси её строку в entries.yml руками.
"""
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

# Строка-заголовок: «Фундук:», «Художник», «Сметана [smetana]:», «Pen:»
HEAD = re.compile(r"^([А-ЯЁA-Z][^\n]{1,40}?):?$")
# Следующая строка должна выглядеть как начало этимологии
MARK = ("От ", "Из ", "Через ", "Происходит от", "В честь", "From ", "Шортен",
        "<—", "←", "—>", "<-", "Протослав", "протослав", "праслав", "Праслав",
        "лат.", "греч.", "Лат", "Гр ", "нем.", "фр.", "англ.")
# Корень: *что-то рядом с маркером прото-языка
ROOTS = re.compile(r"(?:PIE|праиндоевр\.|протоиндоевр\.|прото-?слав\.|праслав\.|"
                   r"прагерм\.|протогерм\.|Proto-\w+|протобалтослав\.)\s*"
                   r"(\*[^\s,;:()«»\"]{2,})")

STOP = {"итак", "итог", "ответ", "бонус", "кстати", "вообще", "答"}


def headwords(text):
    lines = [l.strip() for l in text.split("\n")]
    out = []
    for i, line in enumerate(lines[:-1]):
        m = HEAD.fullmatch(line)
        if not m:
            continue
        nxt = lines[i + 1]
        if not nxt.startswith(MARK):
            continue
        w = m.group(1).strip()
        if w.lower().rstrip(":") in STOP or len(w.split()) > 4:
            continue
        # сам заголовок не должен быть началом этимологии («От слова тень»)
        # или анонсом раздела («Зонтик в языках мира»)
        if w.startswith(MARK) or re.search(r"\bв (языках|разных)\b", w, re.I):
            continue
        # глосса — первая содержательная строка этимологии, подрезанная
        gloss = re.sub(r"\s+", " ", nxt).strip(" .;")
        if len(gloss) > 150:
            gloss = gloss[:147].rsplit(" ", 1)[0] + "…"
        root = None
        tail = "\n".join(lines[i + 1:i + 8])
        rm = ROOTS.search(tail)
        if rm:
            root = rm.group(1).rstrip(".,;:»")
        out.append({"w": w, "g": gloss, "p": None, "r": root})
    return out


def main():
    posts = yaml.safe_load((DATA / "posts.json").read_text(encoding="utf-8"))["posts"]
    curated = yaml.safe_load((DATA / "entries.yml").read_text(encoding="utf-8")) or []
    known_posts = {e["p"] for e in curated}
    known_words = {e["w"].lower() for e in curated}

    auto = []
    for post in posts:
        if post["id"] in known_posts or len(post["text"]) < 150:
            continue
        for cand in headwords(post["text"]):
            if cand["w"].lower() in known_words:
                continue
            cand["p"] = post["id"]
            cand["auto"] = True
            known_words.add(cand["w"].lower())
            auto.append({k: v for k, v in cand.items() if v is not None})

    out = DATA / "entries.auto.yml"
    header = ("# Автоматически извлечённые кандидаты. Не редактируй здесь —\n"
              "# файл перезаписывается при каждом прогоне. Хорошую статью\n"
              "# перенеси в entries.yml, и отсюда она пропадёт.\n")
    out.write_text(header + yaml.safe_dump(auto, allow_unicode=True, sort_keys=False,
                                           default_flow_style=False),
                   encoding="utf-8")
    print(f"{len(auto)} авто-кандидатов из {len(posts)} постов -> {out.name}")


if __name__ == "__main__":
    main()
