"""Проверка данных и собранного сайта. Падает, если что-то не сходится.

Запускается в CI перед выкладкой: лучше уронить прогон, чем молча
опубликовать словарь с битыми ссылками или опрос без верного ответа.
"""
import json
import re
import sys
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SITE = ROOT / "site"
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input",
        "link", "meta", "source", "track", "wbr"}

problems = []


def bad(msg):
    problems.append(msg)


def load(name):
    return yaml.safe_load((DATA / name).read_text(encoding="utf-8")) or []


class Balance(HTMLParser):
    """Считает незакрытые и неверно закрытые теги."""

    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.stack, self.errors = [], []

    def handle_starttag(self, tag, attrs):
        if tag not in VOID:
            self.stack.append((tag, self.getpos()[0]))

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if not self.stack:
            self.errors.append(f"лишний </{tag}> в строке {self.getpos()[0]}")
            return
        open_tag, line = self.stack.pop()
        if open_tag != tag:
            self.errors.append(f"<{open_tag}> строка {line} закрыт как </{tag}>")


def check_data():
    posts = json.loads((DATA / "posts.json").read_text(encoding="utf-8"))["posts"]
    ids = {p["id"] for p in posts}
    polls = {p["id"]: p["poll"] for p in posts if "poll" in p}

    entries = load("entries.yml") + [e for e in load("entries.auto.yml") if e.get("p")]
    roots = {r["r"] for r in load("roots.yml")}
    series = load("series.yml")
    quizzes = load("quizzes.yml")

    for e in entries:
        if e["p"] not in ids:
            bad(f"словарь: «{e['w']}» ссылается на несуществующий пост #{e['p']}")
        if e.get("r") and e["r"] not in roots:
            bad(f"словарь: у корня {e['r']} (слово «{e['w']}») нет глоссы в roots.yml")
        if not str(e.get("g", "")).strip():
            bad(f"словарь: у «{e['w']}» пустая глосса")

    for word, n in Counter(e["w"].lower() for e in entries).items():
        if n > 1:
            bad(f"словарь: «{word}» встречается {n} раза")

    used = {e["r"] for e in entries if e.get("r")}
    for orphan in sorted(roots - used):
        bad(f"корни: {orphan} описан, но к нему не привязано ни одного слова")

    for s in series:
        for pid, caption in s["posts"]:
            if pid not in ids:
                bad(f"серия «{s['id']}»: несуществующий пост #{pid} ({caption})")
        if not s["posts"]:
            bad(f"серия «{s['id']}» пустая")

    for q in quizzes:
        for key in ("poll", "post"):
            if q[key] not in ids:
                bad(f"опрос {q['poll']}: несуществующий пост #{q[key]} в поле {key}")
        options = polls.get(q["poll"], {}).get("answers", [])
        if not options:
            bad(f"опрос {q['poll']}: в архиве нет вариантов ответа")
        c = q.get("correct")
        if c is not None and not 0 <= c < len(options):
            bad(f"опрос {q['poll']}: correct={c}, а вариантов {len(options)}")
        if not str(q.get("answer", "")).strip():
            bad(f"опрос {q['poll']}: пустое пояснение")

    return len(entries), len(quizzes)


def check_site():
    pages = sorted(SITE.glob("*.html"))
    if not pages:
        bad("site/: нет ни одной страницы — сборка не отработала")
    for f in pages:
        raw = f.read_text(encoding="utf-8")
        parser = Balance()
        parser.feed(raw)
        parser.close()
        for tag, line in parser.stack:
            parser.errors.append(f"<{tag}> строка {line} не закрыт")
        for err in parser.errors[:5]:
            bad(f"{f.name}: {err}")
        body = re.sub(r"<(script|style)\b.*?</\1>", "", raw, flags=re.S | re.I)
        if re.search(r"<(?![/!a-zA-Z])", body):
            bad(f"{f.name}: голый символ «<» вне тега")
        if "og:image" not in raw:
            bad(f"{f.name}: нет og-разметки")
    for required in ("style.css", "og.png", "sitemap.xml", "robots.txt"):
        if not (SITE / required).exists():
            bad(f"site/: не хватает {required}")
    return len(pages)


if __name__ == "__main__":
    n_entries, n_quizzes = check_data()
    n_pages = check_site()
    if problems:
        print(f"НЕ ПРОШЛО, проблем: {len(problems)}")
        for pr in problems:
            print("  -", pr)
        sys.exit(1)
    print(f"всё сходится: {n_entries} статей, {n_quizzes} опросов, {n_pages} страниц")
