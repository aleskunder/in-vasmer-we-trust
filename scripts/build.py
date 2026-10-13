"""data/* -> site/. Чистый статический HTML, без фреймворков."""
import html
import json
import re
from collections import Counter
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SITE = ROOT / "site"
CH = "ethimologie"
BASE = "/in-vasmer-we-trust"   # префикс GitHub Pages; "" для корня
SITE_URL = "https://aleskunder.github.io" + BASE


def load(name):
    return yaml.safe_load((DATA / name).read_text(encoding="utf-8")) or []


def esc(s):
    return html.escape(str(s), quote=True)


def link(pid):
    return f"https://t.me/{CH}/{pid}"


ALPHABET = "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЭЮЯ"
MONTHS = ("январь", "февраль", "март", "апрель", "май", "июнь", "июль",
          "август", "сентябрь", "октябрь", "ноябрь", "декабрь")


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


def shell(active, title, subtitle, body):
    nav = "".join(
        f'<a href="{BASE}/{href}" class="{"on" if href == active else ""}">{esc(label)}</a>'
        for href, label in PAGES)
    return f"""<!doctype html>
<html lang="ru"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} — In Vasmer We Trust</title>
<meta name="description" content="{esc(subtitle)}">
<link rel="canonical" href="{SITE_URL}/{active}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="In Vasmer We Trust">
<meta property="og:locale" content="ru_RU">
<meta property="og:title" content="{esc(title)} — In Vasmer We Trust">
<meta property="og:description" content="{esc(subtitle)}">
<meta property="og:url" content="{SITE_URL}/{active}">
<meta property="og:image" content="{SITE_URL}/og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<link rel="stylesheet" href="{BASE}/style.css">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'><text y='13' font-size='14'>📖</text></svg>">
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


ASSETS = ROOT / "assets"


def chart_months(substantive):
    """Колонки «постов в месяц». Одна серия — легенда не нужна."""
    tally = Counter(p["date"][:7] for p in substantive)
    firstpost = {}
    for post in sorted(substantive, key=lambda x: x["id"]):
        firstpost.setdefault(post["date"][:7], post["id"])
    first, last = min(tally), max(tally)
    months = []
    y, m = int(first[:4]), int(first[5:7])
    while f"{y:04d}-{m:02d}" <= last:
        months.append(f"{y:04d}-{m:02d}")
        m += 1
        if m == 13:
            y, m = y + 1, 1
    peak = max(tally.values())
    W, H, PAD_B, PAD_T = 860, 150, 22, 16
    step = W / len(months)
    bw = min(24.0, step - 2)              # <=24px, 2px зазор поверхностью
    plot = H - PAD_B - PAD_T
    bars, ticks, seen = [], [], set()
    for i, key in enumerate(months):
        n = tally.get(key, 0)
        x = i * step + (step - bw) / 2
        if n:
            h = max(3.0, plot * n / peak)
            y0 = PAD_T + plot - h
            r = min(4.0, bw / 2, h)       # 4px скругление сверху, низ квадратный
            bars.append(
                f'<a class="barlink" href="{link(firstpost[key])}" '
                f'data-m="{MONTHS[int(key[5:7]) - 1]} {key[:4]}" data-n="{n}">'
                # прозрачная подложка во всю высоту — попасть мышью в тонкий столбик трудно
                f'<rect class="hit" x="{i * step:.1f}" y="{PAD_T}" '
                f'width="{step:.1f}" height="{plot:.1f}"/>'
                f'<path class="bar" d="M{x:.1f} {y0 + h:.1f}V{y0 + r:.1f}'
                f'a{r:.1f} {r:.1f} 0 0 1 {r:.1f} -{r:.1f}h{bw - 2 * r:.1f}'
                f'a{r:.1f} {r:.1f} 0 0 1 {r:.1f} {r:.1f}V{y0 + h:.1f}z"/></a>')
        year = key[:4]
        if year not in seen:
            seen.add(year)
            ticks.append(f'<text class="tick" x="{i * step:.1f}" y="{H - 6}">{year}</text>')
    peak_key = max(tally, key=lambda k: tally[k])
    px = months.index(peak_key) * step + step / 2
    label = (f'<text class="peaklabel" x="{px:.1f}" y="{PAD_T - 4:.0f}" '
             f'text-anchor="middle">{peak} за месяц</text>')
    return (f'<figure class="chart" id="months"><figcaption>Постов по месяцам, '
            f'{first[:4]}–{last[:4]} — столбик ведёт на первый пост месяца</figcaption>'
            f'<div class="tip" id="mtip" hidden></div>'
            f'<svg viewBox="0 0 {W} {H}" role="img"'
            f' aria-label="Столбики: число постов в каждый месяц. Пик — {peak}.">'
            f'<line class="axis" x1="0" y1="{H - PAD_B}" x2="{W}" y2="{H - PAD_B}"/>'
            f'{"".join(bars)}{label}{"".join(ticks)}</svg></figure>')


def render_entry(e):
    cls = "entry auto" if e.get("auto") else "entry"
    root = (f'<button type="button" class="r" data-root="{esc(e["r"])}" '
            f'title="показать всё гнездо">{esc(e["r"])}</button>') if e.get("r") else ""
    return (f'<div class="{cls}" id="w-{abs(hash(e["w"])) % 10**8}" '
            f'data-w="{esc(e["w"].lower())}" '
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
    (SITE / "style.css").write_text(
        (ASSETS / "style.css").read_text(encoding="utf-8"), encoding="utf-8")
    (SITE / "og.png").write_bytes((ASSETS / "og.png").read_bytes())
    (SITE / ".nojekyll").write_text("", encoding="utf-8")
    (SITE / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n", encoding="utf-8")
    today = __import__("datetime").date.today().isoformat()
    (SITE / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join(f"  <url><loc>{SITE_URL}/{href}</loc>"
                  f"<lastmod>{today}</lastmod></url>\n" for href, _ in PAGES)
        + "</urlset>\n", encoding="utf-8")

    # ---------- главная ----------
    cards = "".join(
        f'<li class="card"><h3><a href="{BASE}/serii.html#{esc(s["id"])}">{esc(s["title"])}</a></h3>'
        f'<p>{esc(" ".join(s["blurb"].split()))}</p>'
        f'<span class="when">{esc(s["period"])} · {len(s["posts"])} постов</span></li>'
        for s in series if s.get("index", True))
    # навигационный пост ссылается на сам сайт — в «Свежем» ему не место
    selfless = [p for p in substantive if SITE_URL not in p["text"]]
    recent = "".join(
        f'<li><a href="{link(p["id"])}">{esc(p["text"].split(chr(10))[0][:70])}</a> '
        f'<span class="when">{p["date"][:10]}</span></li>'
        for p in sorted(selfless, key=lambda p: p["id"], reverse=True)[:8])
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
<h2>Как шёл канал</h2>
{chart_months(substantive)}
<script>
(()=>{{
  const tip=document.getElementById('mtip'),fig=document.getElementById('months');
  if(!tip||!fig)return;
  for(const a of fig.querySelectorAll('.barlink')){{
    a.addEventListener('pointerenter',()=>{{
      tip.textContent=a.dataset.m+' — '+a.dataset.n+' постов';
      tip.hidden=false;
    }});
    a.addEventListener('pointermove',ev=>{{
      const b=fig.getBoundingClientRect();
      tip.style.left=(ev.clientX-b.left)+'px';
      tip.style.top=(ev.clientY-b.top)+'px';
    }});
    a.addEventListener('pointerleave',()=>{{tip.hidden=true;}});
  }}
}})();
</script>
"""
    (SITE / "index.html").write_text(
        shell("index.html", "Канал", "Указатель к каналу про этимологию", body), encoding="utf-8")

    # ---------- словарь ----------
    out, cur, letters = [], None, []
    for e in merged:
        b = bucket(e["w"])
        if b != cur:
            cur = b
            letters.append(b)
            out.append(f'<h2 class="letter" id="L{len(letters)}">{esc(b)}</h2>')
        out.append(render_entry(e))
    az = "".join(f'<a href="#L{i}" data-letter="{esc(b)}">{esc(b)}</a>'
                 for i, b in enumerate(letters, 1))
    js = """
<script>
const q=document.getElementById('q'),rows=[...document.querySelectorAll('.entry')],
      heads=[...document.querySelectorAll('.letter')],cnt=document.getElementById('cnt');
const N=rows.length;
const MAP={'ʰ':'h','ʲ':'j','ʷ':'w','ˠ':'g','ˡ':'l','ⁿ':'n',
 '₁':'1','₂':'2','₃':'3','₄':'4','₅':'5','₆':'6',
 '¹':'1','²':'2','³':'3','ħ':'h','ʕ':'',"ʔ":'',
 'ᵊ':'e','ʱ':'h'};
function norm(s){
  s=s.toLowerCase().replace(/ё/g,'е');
  s=s.normalize('NFD').replace(/[̀-ͯ]/g,'');
  return s.replace(/./g,c=>MAP[c]!==undefined?MAP[c]:c);
}
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
  for(const a of document.querySelectorAll('.azbar a')){
    const h=document.querySelector(a.getAttribute('href'));
    a.classList.toggle('off', !h || h.classList.contains('hidden'));
  }
}
q.addEventListener('input',run);

// корень в статье открывает всё гнездо
document.addEventListener('click',ev=>{
  const b=ev.target.closest('button.r'); if(!b)return;
  q.value=b.dataset.root; run();
  window.scrollTo({top:0,behavior:'smooth'});
});

// случайное слово
document.getElementById('rnd').addEventListener('click',()=>{
  q.value='';run();
  const r=rows[Math.floor(Math.random()*rows.length)];
  r.scrollIntoView({behavior:'smooth',block:'center'});
  r.classList.remove('flash');void r.offsetWidth;r.classList.add('flash');
});

// «/» фокусирует поиск
document.addEventListener('keydown',ev=>{
  if(ev.key==='/'&&document.activeElement!==q){ev.preventDefault();q.focus();}
});

const pre=new URLSearchParams(location.search).get('q');
if(pre){q.value=pre;}
run();
if(!('ontouchstart' in window)) q.focus({preventScroll:true});
</script>"""
    body = f"""
<h1>Словарь</h1>
<p class="lede">Все слова, которые разбирались в канале. Поиск по слову / глоссе / корню.</p>
<label class="vh" for="q">Поиск по словарю</label>
<input id="q" class="search" type="search" placeholder="кап, форточ, *wert- …"
       autocomplete="off" aria-describedby="cnt">
<div class="dictbar">
  <p class="count" id="cnt" role="status" aria-live="polite"></p>
  <button id="rnd" type="button" class="ghost">🎲 случайное слово</button>
</div>
<nav class="azbar" id="az" aria-label="Переход по алфавиту">{az}</nav>
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
    cards_q, index_q = [], []
    for n, q in enumerate(quizzes, 1):
        poll = next(p for p in posts if p["id"] == q["poll"]).get("poll", {})
        opts = poll.get("answers", [])
        correct = q.get("correct")
        words = ", ".join(q["words"])
        buttons = "".join(
            f'<li><button type="button" data-i="{i}">{esc(o.rstrip(";."))}</button></li>'
            for i, o in enumerate(opts))
        cards_q.append(
            f'<div class="qz hidden" data-correct="{"" if correct is None else correct}" '
            f'data-id="{q["poll"]}" data-n="{n}">'
            f'<p class="ws">{esc(words)}</p>'
            f'<p class="kind">№{n} из {len(quizzes)} · {esc(KIND.get(q["kind"], ""))}</p>'
            f'<ol class="opts">{buttons}</ol>'
            f'<p class="verdict hidden" role="status" aria-live="polite">'
            f'<span class="mark"></span> {esc(q["answer"])} '
            f'<a href="{link(q["post"])}">разбор&nbsp;↗</a> · '
            f'<a href="{link(q["poll"])}">опрос в канале&nbsp;↗</a></p></div>')
        index_q.append(
            f'<li><button type="button" data-goto="{q["poll"]}">'
            f'<span class="num">{n}</span><span class="t">{esc(words)}</span>'
            f'<span class="st" aria-hidden="true"></span></button></li>')

    quiz_js = """
<script>
const KEY='ivwt-quiz-v1';
let saved={};
try{saved=JSON.parse(localStorage.getItem(KEY)||'{}')}catch(e){}
const cards=[...document.querySelectorAll('.qz')];
const idx=[...document.querySelectorAll('.qindex button')];
const el=id=>document.getElementById(id);
const byId=id=>cards.find(c=>c.dataset.id===String(id));
function store(){try{localStorage.setItem(KEY,JSON.stringify(saved))}catch(e){}}

function paint(){
  const done=Object.keys(saved).length;
  const right=Object.values(saved).filter(v=>v.ok).length;
  el('done').textContent=done; el('right').textContent=right;
  el('total').textContent=cards.length;
  el('reset').classList.toggle('hidden',!done);
  idx.forEach(b=>{
    const st=saved[b.dataset.goto];
    b.classList.toggle('ok', !!st&&st.ok);
    b.classList.toggle('no', !!st&&!st.ok);
  });
  el('nextwrap').classList.toggle('hidden', done>=cards.length);
  el('alldone').classList.toggle('hidden', done<cards.length);
}
function reveal(card,picked,save){
  const raw=card.dataset.correct, correct=raw===''?null:+raw;
  const ok = correct===null ? false : picked===correct;
  card.querySelectorAll('button').forEach(b=>{
    b.disabled=true; const i=+b.dataset.i;
    if(i===correct&&!b.querySelector('.tick')){b.classList.add('right');b.insertAdjacentHTML('beforeend','<span class="tick">\u2713</span>');}
    if(i===picked&&i!==correct&&!b.querySelector('.tick')){b.classList.add('wrong');b.insertAdjacentHTML('beforeend','<span class="tick">\u2717</span>');}
  });
  const v=card.querySelector('.verdict');
  v.querySelector('.mark').innerHTML = correct===null
    ? '<b class="ok">Верного варианта нет.</b>'
    : (ok?'<b class="ok">Верно.</b>':'<b class="no">Мимо.</b>');
  v.classList.remove('hidden');
  if(save){saved[card.dataset.id]={p:picked,ok:ok};store();paint();}
}
function show(card,scroll){
  cards.forEach(c=>c.classList.add('hidden'));
  card.classList.remove('hidden');
  idx.forEach(b=>b.classList.toggle('cur', b.dataset.goto===card.dataset.id));
  const st=saved[card.dataset.id];
  if(st!==undefined && card.querySelector('.verdict').classList.contains('hidden'))
    reveal(card,st.p,false);
  if(scroll) el('stage').scrollIntoView({behavior:'smooth',block:'start'});
}
function pick(){
  const left=cards.filter(c=>saved[c.dataset.id]===undefined);
  const pool=left.length?left:cards;
  return pool[Math.floor(Math.random()*pool.length)];
}
cards.forEach(card=>card.querySelectorAll('.opts button').forEach(b=>{
  b.addEventListener('click',()=>reveal(card,+b.dataset.i,true));
}));
idx.forEach(b=>b.addEventListener('click',()=>show(byId(b.dataset.goto),true)));
el('next').addEventListener('click',()=>show(pick(),true));
el('reset').addEventListener('click',()=>{
  saved={};store();
  cards.forEach(c=>{
    c.querySelector('.verdict').classList.add('hidden');
    c.querySelectorAll('.opts button').forEach(b=>{
      b.disabled=false;b.classList.remove('right','wrong');
      const t=b.querySelector('.tick'); if(t)t.remove();
    });
  });
  show(pick(),false);paint();
});
show(pick(),false);paint();
</script>"""

    body = f"""
<h1>Опросы</h1>
<p class="lede">Два формата: «какие из слов родственны» и «найдите лишнее».
В канале сперва выходил опрос, через несколько дней — разбор.
Показывается по одному случайному; внизу указатель по всем.</p>
<div class="scorebar">
  <span>отвечено <b id="done">0</b> из <b id="total">0</b></span>
  <span>угадано <b id="right">0</b></span>
  <button id="reset" type="button" class="hidden">сбросить</button>
</div>
<div id="stage">{''.join(cards_q)}</div>
<p id="nextwrap"><button id="next" class="nextbtn" type="button">Следующий случайный →</button></p>
<p id="alldone" class="hidden alldone">Все {len(quizzes)} пройдены. Можно сбросить и начать заново.</p>
<h2>Указатель</h2>
<ol class="qindex">{''.join(index_q)}</ol>
{quiz_js}
"""
    (SITE / "oprosy.html").write_text(
        shell("oprosy.html", "Опросы", "Интерактивы канала: ответить и проверить себя", body),
        encoding="utf-8")

    print(f"site/: {len(merged)} статей ({len(auto)} авто), {len(order)} корней, "
          f"{len(series)} серий, {len(quizzes)} опросов")


if __name__ == "__main__":
    build()
