"""Разово: Telegram-экспорт (result.json) -> data/posts.json.

Экспорт — источник правды для архива: в нём есть структура опросов,
которой нет в публичном веб-фиде канала.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "posts.json"


def plain(text):
    """text_entities экспорта -> плоская строка."""
    if isinstance(text, str):
        return text
    return "".join(p if isinstance(p, str) else p.get("text", "") for p in text)


def main(export_path):
    raw = json.loads(Path(export_path).read_text(encoding="utf-8"))
    posts = []
    for m in raw["messages"]:
        if m.get("type") != "message":
            continue
        post = {
            "id": m["id"],
            "date": m["date"],
            "text": plain(m.get("text", "")).strip(),
            "has_media": any(k in m for k in ("photo", "file", "media_type")),
        }
        if "poll" in m:
            poll = m["poll"]
            post["poll"] = {
                "question": poll.get("question", ""),
                "answers": [a["text"] for a in poll.get("answers", [])],
                "voters": poll.get("total_voters"),
            }
        posts.append(post)

    posts.sort(key=lambda p: p["id"])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps({"channel": raw["name"], "username": "ethimologie", "posts": posts},
                   ensure_ascii=False, indent=1),
        encoding="utf-8",
    )
    polls = sum(1 for p in posts if "poll" in p)
    print(f"{len(posts)} сообщений, {polls} опросов, id {posts[0]['id']}..{posts[-1]['id']} -> {OUT}")


if __name__ == "__main__":
    main(sys.argv[1])
