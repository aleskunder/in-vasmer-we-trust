"""data/* -> site/. Чистый статический HTML, без фреймворков."""
import html
import json
import re
import shutil
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SITE = ROOT / "site"
CH = "ethimologie"
BASE = "/in-vasmer-we-trust"   # префикс GitHub Pages; "" для корня


def load(name):
    return yaml.safe_load((DATA / name).read_text(encoding="utf-8")) or []


def esc(s):
    return html.escape(str(s), quote=True)


def link(pid):
    return f"https://t.me/{CH}/{pid}"


ALPHABET = "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЭЮЯ"


def bucket(word):
    first = word[0].upper()
    if first in ALPHABET:
        return first
    if re.match(r"[A-Z]", first):
        return "A–Z"
    return "#"


def sort_key(word):
    b = bucket(word)
    return (ALPHABET.index(b) if b in ALPHABET else (90 if b == "A–Z" else 99),
            word.lower())


PAGES = [("index.html", "Канал"), ("slovar.html", "Словарь"),
         ("korni.html", "Корни"), ("serii.html", "Серии"),
         ("oprosy.html", "Опросы")]


def shell(active, title, subtitle, body, extra_head=""):
    nav = "".join(
        f'<a href="{BASE}/{href}" class="{"on" if href == active else ""}">{esc(label)}</a>'
        for href, label in PAGES)
    return f"""<!doctype html>
<html lang="ru"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} — In Vasmer We Trust</title>
<meta name="description" content="{esc(subtitle)}">
<link rel="stylesheet" href="{BASE}/style.css">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'><text y='13' font-size='14'>📖</text></svg>">
{extra_head}
</head><body>
<header class="top">
  <div class="wrap">
    <a class="brand" href="{BASE}/index.html">In&nbsp;Vasmer&nbsp;We&nbsp;Trust</a>
    <nav>{nav}</nav>
  </div>
</header>
<main class="wrap">
{body}
</main>
<footer class="wrap">
  <p>Указатель к телеграм-каналу <a href="https://t.me/{CH}">@{CH}</a>.
  Обновляется полуавтоматически по мере появления постов и навайбкоживания фичей.</p>
</footer>
</body></html>
"""


CSS = """
:root{
  --bg:#fbf8f3; --panel:#fff; --ink:#23201c; --dim:#6d665d; --line:#e4ddd1;
  --accent:#8a4b2a; --accent-soft:#f0e3d8; --chip:#f3ece2;
}
@media (prefers-color-scheme:dark){
  :root{
    --bg:#16140f; --panel:#1e1b16; --ink:#ece6dc; --dim:#9a9184; --line:#312c24;
    --accent:#d99b6c; --accent-soft:#2d241c; --chip:#272118;
  }
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
  font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",sans-serif;
  -webkit-text-size-adjust:100%}
.wrap{max-width:860px;margin:0 auto;padding:0 20px}
a{color:var(--accent)}
h1,h2,h3{font-family:Georgia,"Iowan Old Style","Times New Roman",serif;font-weight:600;line-height:1.25}
h1{font-size:2rem;margin:.2em 0 .1em}
h2{font-size:1.35rem;margin:2.2rem 0 .6rem}
h3{font-size:1.05rem;margin:0 0 .2rem}

.top{border-bottom:1px solid var(--line);background:var(--panel);position:sticky;top:0;z-index:5}
.top .wrap{display:flex;flex-wrap:wrap;gap:.4rem 1.2rem;align-items:baseline;padding-block:.8rem}
.brand{font-family:Georgia,serif;font-weight:600;text-decoration:none;color:var(--ink);font-size:1.05rem}
.top nav{display:flex;gap:1rem;margin-left:auto;flex-wrap:wrap}
.top nav a{text-decoration:none;color:var(--dim);font-size:.93rem}
.top nav a.on,.top nav a:hover{color:var(--accent)}

.lede{color:var(--dim);font-size:1.05rem;max-width:62ch}
.stats{display:flex;flex-wrap:wrap;gap:.5rem 1.6rem;color:var(--dim);font-size:.9rem;
  margin:1.2rem 0 0;padding:0;list-style:none}
.stats b{color:var(--ink);font-weight:600}

.search{width:100%;padding:.75rem .9rem;font:inherit;color:var(--ink);
  background:var(--panel);border:1px solid var(--line);border-radius:10px;margin:1rem 0 .4rem}
.search:focus{outline:2px solid var(--accent);outline-offset:1px;border-color:transparent}
.count{color:var(--dim);font-size:.88rem;margin:0 0 1.2rem}

.cards{display:grid;gap:.9rem;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));
  padding:0;list-style:none;margin:1rem 0}
.card{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:1rem 1.1rem}
.card h3 a{text-decoration:none}
.card p{margin:.35rem 0 0;color:var(--dim);font-size:.92rem}
.card .when{display:block;color:var(--dim);font-size:.8rem;margin-top:.5rem}

.letter{font-family:Georgia,serif;font-size:1.5rem;color:var(--accent);
  margin:1.8rem 0 .5rem;padding-bottom:.2rem;border-bottom:1px solid var(--line)}
.entry{padding:.5rem 0;border-bottom:1px solid var(--line)}
.entry .w{font-weight:600}
.entry .g{color:var(--dim)}
.entry .r{display:inline-block;background:var(--chip);border-radius:6px;padding:.05em .45em;
  font-size:.82rem;color:var(--dim);margin-left:.3rem;white-space:nowrap}
.entry .src{font-size:.85rem;white-space:nowrap}
.entry.auto .w::after{content:"авто";font-size:.7rem;background:var(--accent-soft);
  color:var(--accent);border-radius:5px;padding:.1em .4em;margin-left:.4em;vertical-align:.1em}

.root{background:var(--panel);border:1px solid var(--line);border-radius:12px;
  padding:.9rem 1.1rem;margin:.7rem 0}
.root .head{display:flex;flex-wrap:wrap;gap:.5rem;align-items:baseline}
.root code{font-size:1.05rem;color:var(--accent);font-weight:600}
.root .gl{color:var(--dim)}
.root .n{margin-left:auto;color:var(--dim);font-size:.85rem}
.chips{display:flex;flex-wrap:wrap;gap:.35rem;margin:.6rem 0 0;padding:0;list-style:none}
.chips a{background:var(--chip);border-radius:7px;padding:.18em .55em;font-size:.9rem;
  text-decoration:none;color:var(--ink)}
.chips a:hover{background:var(--accent-soft);color:var(--accent)}

.serie{margin:0 0 2rem}
.serie .when{color:var(--dim);font-size:.85rem}
.serie ol{margin:.7rem 0 0;padding-left:1.4rem}
.serie li{margin:.25rem 0}
.recent{list-style:none;padding:0;margin:.8rem 0}
.recent li{display:flex;gap:1rem;align-items:baseline;padding:.4rem 0;border-bottom:1px solid var(--line)}
.recent .when{margin-left:auto;color:var(--dim);font-size:.85rem;white-space:nowrap}
.quiz{padding:.45rem 0;border-bottom:1px solid var(--line);font-size:.95rem}
.quiz .ws{font-weight:600}
.hidden{display:none !important}

.qz{background:var(--panel);border:1px solid var(--line);border-radius:12px;
  padding:1rem 1.1rem;margin:0 0 1rem}
.qz .ws{font-family:Georgia,serif;font-size:1.15rem;margin:0 0 .1rem}
.qz .kind{color:var(--dim);font-size:.8rem;margin:0 0 .7rem}
.qz ol.opts{list-style:none;margin:0;padding:0;display:grid;gap:.4rem}
.qz button{width:100%;text-align:left;font:inherit;color:var(--ink);cursor:pointer;
  background:var(--bg);border:1px solid var(--line);border-radius:9px;padding:.5rem .7rem}
.qz button:hover:not(:disabled){border-color:var(--accent);color:var(--accent)}
.qz button:disabled{cursor:default}
.qz button.right{border-color:#2e7d52;background:color-mix(in srgb,#2e7d52 12%,var(--bg));color:var(--ink)}
.qz button.wrong{border-color:#b3453a;background:color-mix(in srgb,#b3453a 12%,var(--bg));color:var(--ink)}
.qz button .tick{float:right;font-weight:700}
.qz .verdict{margin:.7rem 0 0;padding-top:.7rem;border-top:1px solid var(--line);font-size:.93rem}
.qz .verdict b.ok{color:#2e7d52} .qz .verdict b.no{color:#b3453a}
.scorebar{position:sticky;top:3.1rem;z-index:4;background:var(--panel);
  border:1px solid var(--line);border-radius:10px;padding:.55rem .9rem;margin:1rem 0 1.4rem;
  display:flex;gap:1rem;align-items:center;flex-wrap:wrap;font-size:.92rem}
.scorebar b{font-size:1.05rem}
.scorebar button{margin-left:auto;font:inherit;font-size:.85rem;color:var(--dim);cursor:pointer;
  background:none;border:1px solid var(--line);border-radius:7px;padding:.25rem .6rem}
.scorebar button:hover{color:var(--accent);border-color:var(--accent)}
@media (max-width:520px){
  h1{font-size:1.6rem}
  .top .wrap{padding-block:.6rem}
  .entry .src{display:block;white-space:normal}
}
"""


def render_entry(e):
    cls = "entry auto" if e.get("auto") else "entry"
    root = f'<span class="r">{esc(e["r"])}</span>' if e.get("r") else ""
    return (f'<div class="{cls}" data-w="{esc(e["w"].lower())}" '
            f'data-g="{esc(e["g"].lower())}" data-r="{esc((e.get("r") or "").lower())}">'
            f'<span class="w">{esc(e["w"])}</span>{root} — '
            f'<span class="g">{esc(e["g"])}</span> '
            f'<a class="src" href="{link(e["p"])}">пост&nbsp;#{e["p"]}&nbsp;↗</a></div>')


def build():
    entries = load("entries.yml")
    auto = [e for e in (load("entries.auto.yml") or []) if e.get("p")]
    known = {e["w"].lower() for e in entries}
    merged = entries + [e for e in auto if e["w"].lower() not in known]
    merged.sort(key=lambda e: sort_key(e["w"]))

    roots = load("roots.yml")
    series = load("series.yml")
    quizzes = load("quizzes.yml")
    posts = json.loads((DATA / "posts.json").read_text(encoding="utf-8"))["posts"]
    substantive = [p for p in posts if len(p["text"]) > 150]
    last = max(p["date"] for p in posts)[:10]

    SITE.mkdir(exist_ok=True)
    (SITE / "style.css").write_text(CSS, encoding="utf-8")
    (SITE / ".nojekyll").write_text("", encoding="utf-8")

    # ---------- главная ----------
    cards = "".join(
        f'<li class="card"><h3><a href="{BASE}/serii.html#{esc(s["id"])}">{esc(s["title"])}</a></h3>'
        f'<p>{esc(" ".join(s["blurb"].split()))}</p>'
        f'<span class="when">{esc(s["period"])} · {len(s["posts"])} постов</span></li>'
        for s in series if s.get("index", True))
    recent = "".join(
        f'<li><a href="{link(p["id"])}">{esc(p["text"].split(chr(10))[0][:70])}</a> '
        f'<span class="when">{p["date"][:10]}</span></li>'
        for p in sorted(substantive, key=lambda p: p["id"], reverse=True)[:8])
    body = f"""
<h1>In Vasmer We Trust</h1>
<p class="lede">Указатель к <a href="https://t.me/{CH}">@{CH}</a> — каналу
про этимологию и случайные штуки. Здесь лежат ссылки на разборы
конкретных слов, сюжетные циклы + праиндоевропейские корни.</p>
<ul class="stats">
  <li><b>{len(substantive)}</b> постов</li>
  <li><b>{len(merged)}</b> слов в словаре</li>
  <li><b>{len(roots)}</b> корней</li>
  <li><b>{len(quizzes)}</b> интерактивов</li>
  <li>последний пост <b>{last}</b></li>
</ul>
<h2>Серии</h2>
<ul class="cards">{cards}</ul>
<h2>Свежее</h2>
<ul class="recent">{recent}</ul>
"""
    (SITE / "index.html").write_text(
        shell("index.html", "Канал", "Указатель к каналу про этимологию", body), encoding="utf-8")

    # ---------- словарь ----------
    out, cur = [], None
    for e in merged:
        b = bucket(e["w"])
        if b != cur:
            cur = b
            out.append(f'<h2 class="letter" data-letter="1">{esc(b)}</h2>')
        out.append(render_entry(e))
    js = """
<script>
const q=document.getElementById('q'),rows=[...document.querySelectorAll('.entry')],
      heads=[...document.querySelectorAll('.letter')],cnt=document.getElementById('cnt');
const N=rows.length;
function norm(s){return s.toLowerCase().replace(/ё/g,'е');}
function run(){
  const v=norm(q.value.trim());
  let shown=0;
  for(const r of rows){
    const hit=!v||norm(r.dataset.w).includes(v)||norm(r.dataset.g).includes(v)||norm(r.dataset.r).includes(v);
    r.classList.toggle('hidden',!hit); if(hit)shown++;
  }
  for(const h of heads){
    let n=h.nextElementSibling,any=false;
    while(n&&!n.classList.contains('letter')){
      if(n.classList.contains('entry')&&!n.classList.contains('hidden')){any=true;break;}
      n=n.nextElementSibling;}
    h.classList.toggle('hidden',!any);
  }
  cnt.textContent=v?`${shown} из ${N}`:`${N} слов`;
}
q.addEventListener('input',run);
const pre=new URLSearchParams(location.search).get('q');
if(pre){q.value=pre;}
run();q.focus({preventScroll:true});
</script>"""
    body = f"""
<h1>Словарь</h1>
<p class="lede">Все слова, которые разбирались в канале. Поиск по слову / глоссе / корню.</p>
<input id="q" class="search" type="search" placeholder="кап, форточ, *wert- …" autocomplete="off">
<p class="count" id="cnt"></p>
{''.join(out)}
{js}
"""
    (SITE / "slovar.html").write_text(
        shell("slovar.html", "Словарь", "Все разобранные слова со ссылками на посты", body),
        encoding="utf-8")

    # ---------- корни ----------
    by_root = {}
    for e in merged:
        if e.get("r"):
            by_root.setdefault(e["r"], []).append(e)
    gloss = {r["r"]: r["g"] for r in roots}
    order = sorted(by_root, key=lambda r: (-len(by_root[r]), r))
    blocks = []
    for r in order:
        ws = sorted(by_root[r], key=lambda e: e["w"].lower())
        chips = "".join(f'<li><a href="{link(e["p"])}">{esc(e["w"])}</a></li>' for e in ws)
        blocks.append(
            f'<div class="root"><div class="head"><code>{esc(r)}</code>'
            f'<span class="gl">{esc(gloss.get(r, ""))}</span>'
            f'<span class="n">{len(ws)}</span></div><ul class="chips">{chips}</ul></div>')
    body = f"""
<h1>Корни</h1>
<p class="lede">{len(order)} прото-корней, до которых добрались посты.</p>
{''.join(blocks)}
"""
    (SITE / "korni.html").write_text(
        shell("korni.html", "Корни", "Праиндоевропейские корни и слова, которые к ним сошлись", body),
        encoding="utf-8")

    # ---------- серии ----------
    blocks = []
    for s in series:
        items = "".join(f'<li><a href="{link(pid)}">{esc(cap)}</a></li>' for pid, cap in s["posts"])
        blocks.append(
            f'<section class="serie" id="{esc(s["id"])}"><h2>{esc(s["title"])}</h2>'
            f'<p class="when">{esc(s["period"])} · {len(s["posts"])} постов</p>'
            f'<p class="lede">{esc(" ".join(s["blurb"].split()))}</p>'
            f'<ol>{items}</ol></section>')
    body = f"""
<h1>Серии</h1>
<p class="lede">Серии постов по отдельным случайным языковым и не очень темам.</p>
{''.join(blocks)}
"""
    (SITE / "serii.html").write_text(
        shell("serii.html", "Серии", "Сюжетные циклы канала и архив интерактивов", body),
        encoding="utf-8")

    # ---------- опросы ----------
    KIND = {"rodstvo": "какие слова родственны",
            "lishnee": "найдите лишнее",
            "other": "вопрос"}
    cards_q = []
    for n, q in enumerate(quizzes, 1):
        poll = next(p for p in posts if p["id"] == q["poll"]).get("poll", {})
        opts = poll.get("answers", [])
        correct = q.get("correct")
        buttons = "".join(
            f'<li><button type="button" data-i="{i}">{esc(o.rstrip(";."))}</button></li>'
            for i, o in enumerate(opts))
        cards_q.append(
            f'<div class="qz" data-correct="{"" if correct is None else correct}" data-id="{q["poll"]}">'
            f'<p class="ws">{esc(", ".join(q["words"]))}</p>'
            f'<p class="kind">{n}/{len(quizzes)} · {esc(KIND.get(q["kind"], ""))}</p>'
            f'<ol class="opts">{buttons}</ol>'
            f'<p class="verdict hidden">'
            f'<span class="mark"></span> {esc(q["answer"])} '
            f'<a href="{link(q["post"])}">разбор&nbsp;↗</a> · '
            f'<a href="{link(q["poll"])}">опрос в канале&nbsp;↗</a></p></div>')

    quiz_js = """
<script>
const KEY='ivwt-quiz-v1';
let saved={};
try{saved=JSON.parse(localStorage.getItem(KEY)||'{}')}catch(e){}
const cards=[...document.querySelectorAll('.qz')];
const el=id=>document.getElementById(id);
function store(){try{localStorage.setItem(KEY,JSON.stringify(saved))}catch(e){}}
function score(){
  const done=Object.keys(saved).length;
  const right=Object.values(saved).filter(v=>v.ok).length;
  el('done').textContent=done; el('right').textContent=right;
  el('total').textContent=cards.length;
  el('reset').classList.toggle('hidden',!done);
}
function reveal(card,picked,save){
  const raw=card.dataset.correct, correct=raw===''?null:+raw;
  const btns=[...card.querySelectorAll('button')];
  const ok = correct===null ? false : picked===correct;
  btns.forEach(b=>{
    b.disabled=true; const i=+b.dataset.i;
    if(i===correct){b.classList.add('right');b.insertAdjacentHTML('beforeend','<span class="tick">\u2713</span>');}
    if(i===picked&&i!==correct){b.classList.add('wrong');b.insertAdjacentHTML('beforeend','<span class="tick">\u2717</span>');}
  });
  const v=card.querySelector('.verdict');
  v.querySelector('.mark').innerHTML = correct===null
    ? '<b class="ok">Верного варианта нет.</b>'
    : (ok?'<b class="ok">Верно.</b>':'<b class="no">Мимо.</b>');
  v.classList.remove('hidden');
  if(save){saved[card.dataset.id]={p:picked,ok:ok};store();score();}
}
cards.forEach(card=>{
  const prev=saved[card.dataset.id];
  if(prev!==undefined) reveal(card,prev.p,false);
  card.querySelectorAll('button').forEach(b=>{
    b.addEventListener('click',()=>reveal(card,+b.dataset.i,true));
  });
});
el('reset').addEventListener('click',()=>{saved={};store();location.reload();});
score();
</script>"""

    body = f"""
<h1>Опросы</h1>
<p class="lede">Два формата: «какие из слов родственны» и «найдите лишнее».
В канале сперва выходил опрос, через несколько дней — разбор.
Здесь можно ответить и сразу проверить себя.</p>
<div class="scorebar">
  <span>отвечено <b id="done">0</b> из <b id="total">0</b></span>
  <span>угадано <b id="right">0</b></span>
  <button id="reset" type="button" class="hidden">сбросить</button>
</div>
{''.join(cards_q)}
{quiz_js}
"""
    (SITE / "oprosy.html").write_text(
        shell("oprosy.html", "Опросы", "Интерактивы канала: ответить и проверить себя", body),
        encoding="utf-8")

    print(f"site/: {len(merged)} статей ({len(auto)} авто), {len(order)} корней, "
          f"{len(series)} серий, {len(quizzes)} опросов")


if __name__ == "__main__":
    build()
