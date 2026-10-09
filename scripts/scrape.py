"""Инкрементально добирает новые посты из публичного веб-фида канала.

t.me/s/<channel> отдаёт полный текст постов, даты и пермалинки.
Идём от свежих к старым через ?before=<id>, пока не упрёмся в то,
что уже лежит в data/posts.json.
"""
import html
import json
import re
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
STORE = ROOT / "data" / "posts.json"
CHANNEL = "ethimologie"
UA = "Mozilla/5.0 (X11; Linux x86_64) in-vasmer-we-trust/1.0"
MAX_PAGES = 120  # хватает на весь архив; при обычном прогоне делается 1 запрос

WRAP = re.compile(r'<div class="tgme_widget_message_wrap', re.S)
POST_ID = re.compile(r'data-post="[^/]+/(\d+)"')
TEXT = re.compile(r'<div class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>\s*(?:<div class="tgme_widget_message_(?:footer|reply_markup)|</div>)', re.S)
DATE = re.compile(r'<time datetime="([^"]+)"')
MEDIA = re.compile(r'tgme_widget_message_(?:photo|video|document|poll)')


def strip_tags(fragment):
    s = re.sub(r"<br\s*/?>", "\n", fragment)
    s = re.sub(r"</p>\s*<p[^>]*>", "\n\n", s)
    s = re.sub(r"<[^>]+>", "", s)
    return html.unescape(s).strip()


def parse_page(markup):
    """-> [{id, date, text, has_media}] в порядке появления."""
    out = []
    for chunk in WRAP.split(markup)[1:]:
        m = POST_ID.search(chunk)
        if not m:
            continue
        t = TEXT.search(chunk)
        d = DATE.search(chunk)
        out.append({
            "id": int(m.group(1)),
            "date": (d.group(1) if d else ""),
            "text": strip_tags(t.group(1)) if t else "",
            "has_media": bool(MEDIA.search(chunk)),
        })
    return out


def fetch(session, before=None):
    url = f"https://t.me/s/{CHANNEL}"
    r = session.get(url, params={"before": before} if before else None, timeout=30)
    r.raise_for_status()
    return r.text


def main(full=False):
    store = json.loads(STORE.read_text(encoding="utf-8"))
    known = {p["id"] for p in store["posts"]}
    highest = max(known) if known else 0
    if full:
        highest = 0

    session = requests.Session()
    session.headers["User-Agent"] = UA

    found, before, pages = {}, None, 0
    while pages < MAX_PAGES:
        pages += 1
        batch = parse_page(fetch(session, before))
        if not batch:
            break
        for p in batch:
            if p["id"] not in known and p["id"] not in found:
                found[p["id"]] = p
        oldest = min(p["id"] for p in batch)
        if oldest <= highest:   # дошли до уже известного — дальше не нужно
            break
        before = oldest
        time.sleep(1)           # вежливость к серверу

    if not found:
        print("новых постов нет")
        return 0

    store["posts"].extend(found.values())
    store["posts"].sort(key=lambda p: p["id"])
    STORE.write_text(json.dumps(store, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"добавлено {len(found)}: {sorted(found)[:10]}{'...' if len(found) > 10 else ''}")
    return len(found)


if __name__ == "__main__":
    sys.exit(0 if main(full="--full" in sys.argv) >= 0 else 1)
