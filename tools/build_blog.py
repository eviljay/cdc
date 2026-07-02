#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Генератор статичного блогу для CD Club.
Читає blog/posts.json + blog/posts/<slug>.md і створює:
  - blog/<slug>.html  — окрема SEO-сторінка на кожну статтю (контент вбудований у HTML)
  - blog.html         — індекс блогу зі списком статей
  - sitemap.xml       — карта сайту для пошуковиків
Запускати з кореня репозиторію:  python3 tools/build_blog.py
"""
import json, os, html, datetime
import markdown  # pip install markdown

SITE = "https://civildefense.club"
DEFAULT_COVER = "assets/hero-1.jpg"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MONTHS = ["", "січня", "лютого", "березня", "квітня", "травня", "червня",
          "липня", "серпня", "вересня", "жовтня", "листопада", "грудня"]

def fmt_date(s):
    try:
        d = datetime.date.fromisoformat(s[:10])
        return f"{d.day} {MONTHS[d.month]} {d.year}"
    except Exception:
        return s or ""

def abs_url(path):
    if not path:
        return ""
    if path.startswith("http"):
        return path
    return SITE + "/" + path.lstrip("/")

STYLE = """
    :root{--bg:#111315;--panel:#1d2023;--text:#f4f0ea;--muted:#b9b1a8;--line:rgba(255,255,255,.11);--accent:#ff6a2d;--accent2:#ff884f;--max:1000px}
    *{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--bg);color:var(--text);font-family:Inter,system-ui,sans-serif;line-height:1.6}
    img{display:block;max-width:100%}a{color:inherit;text-decoration:none}
    .wrap{width:min(var(--max),calc(100% - 40px));margin-inline:auto}
    .nav{position:sticky;top:0;z-index:40;background:rgba(14,15,17,.85);backdrop-filter:blur(14px);border-bottom:1px solid rgba(255,255,255,.06)}
    .nav .inner{height:78px;display:flex;align-items:center;justify-content:space-between;gap:20px}
    .brand img{height:48px}.nav a.back{font-size:13px;font-weight:900;text-transform:uppercase;letter-spacing:.08em;color:#ded8d0}.nav a.back:hover{color:var(--accent)}
    .head{padding:64px 0 20px}.overline{display:inline-flex;align-items:center;gap:10px;font-size:12px;font-weight:900;text-transform:uppercase;letter-spacing:.18em;color:var(--accent)}.overline:before{content:"";width:28px;height:2px;background:var(--accent)}
    h1.h1{font-family:Oswald,Impact,sans-serif;text-transform:uppercase;font-size:clamp(38px,6vw,72px);line-height:.98;margin:16px 0 8px}
    .list{display:grid;grid-template-columns:repeat(2,1fr);gap:22px;padding:26px 0 80px}
    .card{background:#181b1f;border:1px solid var(--line);border-radius:22px;overflow:hidden;display:flex;flex-direction:column;transition:.22s}.card:hover{border-color:var(--accent);transform:translateY(-3px)}
    .card .cover{aspect-ratio:16/9;object-fit:cover;background:#0a0c0d}.card .body{padding:24px;display:flex;flex-direction:column;flex:1}
    .card time{font-size:12px;color:var(--accent);text-transform:uppercase;letter-spacing:.12em;font-weight:800}
    .card h2{font-family:Oswald,Impact,sans-serif;text-transform:uppercase;font-size:26px;line-height:1.05;margin:12px 0 10px}
    .card p{margin:0 0 16px;color:var(--muted);font-size:15px}.card .more{margin-top:auto;font-weight:900;font-size:12px;text-transform:uppercase;letter-spacing:.1em}
    .article{padding:20px 0 90px}.article .meta{color:var(--accent);font-size:13px;text-transform:uppercase;letter-spacing:.12em;font-weight:800;margin-bottom:10px}
    .prose{max-width:760px}.prose h1{font-family:Oswald,Impact,sans-serif;text-transform:uppercase;font-size:clamp(32px,5vw,56px);line-height:1;margin:0 0 24px}
    .prose h2{font-family:Oswald,Impact,sans-serif;text-transform:uppercase;font-size:30px;margin:38px 0 14px}
    .prose h3{font-size:22px;margin:28px 0 10px}.prose p,.prose li{color:#e4ded6;font-size:17px}.prose ul,.prose ol{padding-left:22px}
    .prose blockquote{margin:26px 0;padding:16px 22px;border-left:3px solid var(--accent);background:#181b1f;border-radius:0 14px 14px 0;color:#cfc7be}
    .prose a{color:var(--accent);text-decoration:underline}.cover-lead{width:100%;aspect-ratio:16/7;object-fit:cover;border-radius:22px;margin-bottom:34px}
    .prose p img{width:100%;height:auto;border-radius:16px;margin:10px 0}.prose img+em,.prose figcaption{display:block;text-align:center;color:var(--muted);font-size:13px;margin-top:8px}
    .btn{display:inline-flex;align-items:center;gap:10px;min-height:48px;padding:0 22px;border-radius:999px;background:var(--accent);color:#fff;text-transform:uppercase;font-size:12px;font-weight:900;letter-spacing:.12em}.btn:hover{background:var(--accent2)}
    .backlink{display:inline-block;margin-bottom:24px;color:var(--muted);font-weight:800;font-size:13px;text-transform:uppercase;letter-spacing:.1em}.backlink:hover{color:var(--accent)}
    footer{border-top:1px solid var(--line);padding:26px 0;color:#8a8178;font-size:13px}
    .contact-fab{position:fixed;right:22px;bottom:22px;z-index:120;display:inline-flex;align-items:center;gap:10px;height:56px;padding:0 24px;border:0;border-radius:999px;background:var(--accent);color:#fff;font-weight:900;text-transform:uppercase;font-size:13px;letter-spacing:.1em;cursor:pointer;box-shadow:0 14px 34px rgba(255,106,45,.4);transition:.22s}.contact-fab:hover{background:var(--accent2);transform:translateY(-2px)}
    .modal{position:fixed;inset:0;z-index:200;display:none;align-items:center;justify-content:center;padding:20px;background:rgba(8,9,10,.72);backdrop-filter:blur(6px)}.modal.open{display:flex}
    .modal-card{width:min(520px,100%);background:var(--panel);border:1px solid var(--line);border-radius:26px;padding:36px;position:relative;max-height:92vh;overflow:auto;box-shadow:0 20px 70px rgba(0,0,0,.36)}
    .modal-close{position:absolute;top:16px;right:16px;width:40px;height:40px;border-radius:50%;border:1px solid var(--line);background:transparent;color:#fff;font-size:22px;cursor:pointer}.modal-close:hover{border-color:var(--accent);color:var(--accent)}
    .modal-card h3{font-family:Oswald,Impact,sans-serif;text-transform:uppercase;font-size:34px;margin:0 0 6px}.modal-card .sub{color:var(--muted);margin:0 0 22px}
    .field{margin-bottom:16px}.field label{display:block;font-size:12px;font-weight:800;text-transform:uppercase;letter-spacing:.1em;color:#cfc7be;margin-bottom:8px}
    .field input,.field textarea{width:100%;min-height:50px;border-radius:14px;border:1px solid var(--line);background:#15181b;color:#fff;padding:14px 16px;font-size:15px;font-family:inherit}.field textarea{min-height:110px;resize:vertical}.field input:focus,.field textarea:focus{outline:0;border-color:var(--accent)}
    .modal .btn{width:100%;border:0;cursor:pointer;justify-content:center}.form-note{margin:14px 0 0;font-size:13px;text-align:center}.form-note.ok{color:#7fd18a}.form-note.err{color:#ff8a6a}
    @media(max-width:760px){.list{grid-template-columns:1fr}.contact-fab{right:14px;bottom:14px;height:50px;padding:0 18px}.modal-card{padding:28px 22px}}
"""

# Модалка + плаваюча кнопка + скрипт (спільні для всіх сторінок)
CONTACT = """
  <button class="contact-fab" id="contactFab" type="button">✉ Зв'язатися</button>
  <div class="modal" id="contactModal" aria-hidden="true" role="dialog" aria-modal="true" aria-labelledby="contactTitle">
    <div class="modal-card">
      <button class="modal-close" id="contactClose" type="button" aria-label="Закрити">×</button>
      <h3 id="contactTitle">Напишіть нам</h3>
      <p class="sub">Залиште контакти й питання — ми зв'яжемося з вами найближчим часом.</p>
      <form id="contactForm" action="https://api.web3forms.com/submit" method="POST">
        <input type="hidden" name="access_key" value="YOUR_WEB3FORMS_ACCESS_KEY">
        <input type="hidden" name="subject" value="Нове звернення з блогу CD Club">
        <input type="hidden" name="from_name" value="Блог CD Club">
        <input type="checkbox" name="botcheck" style="display:none" tabindex="-1" autocomplete="off">
        <div class="field"><label for="cfName">Ім'я</label><input id="cfName" type="text" name="name" required placeholder="Як до вас звертатися"></div>
        <div class="field"><label for="cfContact">Телефон або e-mail</label><input id="cfContact" type="text" name="contact" required placeholder="+38 0__ ___ __ __ або email"></div>
        <div class="field"><label for="cfMsg">Питання</label><textarea id="cfMsg" name="message" required placeholder="Що вас цікавить?"></textarea></div>
        <button class="btn" type="submit" id="cfSubmit">Надіслати</button>
        <p class="form-note" id="cfNote" style="display:none"></p>
      </form>
    </div>
  </div>
  <script>
  (function(){var m=document.getElementById('contactModal'),f=document.getElementById('contactFab');
   function o(){m&&(m.classList.add('open'),m.setAttribute('aria-hidden','false'));}
   function c(){m&&(m.classList.remove('open'),m.setAttribute('aria-hidden','true'));}
   f&&f.addEventListener('click',o);var cb=document.getElementById('contactClose');cb&&cb.addEventListener('click',c);
   m&&m.addEventListener('click',function(e){e.target===m&&c();});
   document.addEventListener('keydown',function(e){e.key==='Escape'&&c();});
   document.addEventListener('click',function(e){var t=e.target.closest('[data-open-contact]');if(t){e.preventDefault();o();}});
   var fm=document.getElementById('contactForm'),n=document.getElementById('cfNote'),sb=document.getElementById('cfSubmit');
   function note(t,k){if(!n)return;n.textContent=t;n.className='form-note '+k;n.style.display='block';}
   fm&&fm.addEventListener('submit',function(e){e.preventDefault();
     if(fm.access_key&&fm.access_key.value.indexOf('YOUR_')===0){note("Форма ще не налаштована: додайте ключ Web3Forms.","err");return;}
     sb.disabled=true;sb.textContent="Надсилаємо…";
     fetch(fm.action,{method:'POST',body:new FormData(fm),headers:{'Accept':'application/json'}})
       .then(function(r){return r.json();})
       .then(function(d){if(d.success){fm.reset();note("Дякуємо! Ми отримали ваше повідомлення.","ok");}else{note("Не вдалося надіслати. Спробуйте пізніше.","err");}})
       .catch(function(){note("Помилка мережі. Спробуйте ще раз.","err");})
       .then(function(){sb.disabled=false;sb.textContent="Надіслати";});});
  })();
  </script>
"""

NAV = """
  <header class="nav">
    <div class="wrap inner">
      <a class="brand" href="{home}"><img src="{assets}cd-club-logo.svg" alt="CD Club"></a>
      <a class="back" href="{home}">← На головну</a>
    </div>
  </header>
"""

FOOTER = """  <footer><div class="wrap">© {year} CD Club · <a href="{home}" style="color:var(--accent)">civildefense.club</a></div></footer>"""


def post_page(post, body_html):
    slug = post["slug"]
    title = post["title"]
    excerpt = post.get("excerpt", "")
    cover = post.get("cover") or DEFAULT_COVER
    url = f"{SITE}/blog/{slug}.html"
    cover_abs = abs_url(cover)
    date_iso = post.get("date", "")[:10]
    cover_img = f'<img class="cover-lead" src="../{cover}" alt="{html.escape(title)}">' if cover else ""
    return f"""<!doctype html>
<html lang="uk">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)} | CD Club</title>
  <meta name="description" content="{html.escape(excerpt)}">
  <link rel="icon" href="../assets/favicon.ico">
  <link rel="canonical" href="{url}">
  <meta property="og:type" content="article">
  <meta property="og:site_name" content="CD Club">
  <meta property="og:title" content="{html.escape(title)}">
  <meta property="og:description" content="{html.escape(excerpt)}">
  <meta property="og:url" content="{url}">
  <meta property="og:image" content="{cover_abs}">
  <meta property="article:published_time" content="{date_iso}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{html.escape(title)}">
  <meta name="twitter:description" content="{html.escape(excerpt)}">
  <meta name="twitter:image" content="{cover_abs}">
  <script type="application/ld+json">{json.dumps({
      "@context":"https://schema.org","@type":"BlogPosting","headline":title,
      "description":excerpt,"image":cover_abs,"datePublished":date_iso,
      "mainEntityOfPage":url,"author":{"@type":"Organization","name":"CD Club"},
      "publisher":{"@type":"Organization","name":"CD Club","logo":{"@type":"ImageObject","url":SITE+"/assets/cd-club-logo.svg"}}
  }, ensure_ascii=False)}</script>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=Oswald:wght@500;600;700&display=swap" rel="stylesheet">
  <style>{STYLE}</style>
</head>
<body>
{NAV.format(home="../index.html", assets="../assets/")}
  <main class="wrap">
    <article class="article">
      <a class="backlink" href="../blog.html">← Усі статті</a>
      <div class="meta">{fmt_date(post.get('date',''))}</div>
      <div class="prose">
        {cover_img}
        <h1>{html.escape(title)}</h1>
{body_html}
      </div>
      <p style="margin-top:40px"><button class="btn" type="button" data-open-contact>Записатися на тренування</button></p>
    </article>
  </main>
{FOOTER.format(year=datetime.date.today().year, home="../index.html")}
{CONTACT}
</body>
</html>
"""


def index_page(posts):
    cards = []
    for p in posts:
        cover = p.get("cover")
        cover_img = f'<img class="cover" loading="lazy" src="{cover}" alt="{html.escape(p["title"])}">' if cover else ""
        cards.append(f"""      <a class="card" href="blog/{p['slug']}.html">{cover_img}
        <div class="body"><time>{fmt_date(p.get('date',''))}</time><h2>{html.escape(p['title'])}</h2>
        <p>{html.escape(p.get('excerpt',''))}</p><span class="more">Читати →</span></div></a>""")
    cards_html = "\n".join(cards)
    return f"""<!doctype html>
<html lang="uk">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Блог | CD Club</title>
  <meta name="description" content="Блог CD Club — поради зі стрілецької та тактичної підготовки, розбори спорядження, новини спільноти.">
  <link rel="icon" href="assets/favicon.ico">
  <link rel="canonical" href="{SITE}/blog.html">
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="CD Club">
  <meta property="og:title" content="Блог | CD Club">
  <meta property="og:description" content="Поради зі стрілецької та тактичної підготовки, розбори спорядження, новини спільноти.">
  <meta property="og:url" content="{SITE}/blog.html">
  <meta property="og:image" content="{SITE}/{DEFAULT_COVER}">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=Oswald:wght@500;600;700&display=swap" rel="stylesheet">
  <style>{STYLE}</style>
</head>
<body>
{NAV.format(home="index.html", assets="assets/")}
  <main class="wrap">
    <div class="head"><span class="overline">Блог</span><h1 class="h1">Статті та новини</h1></div>
    <div class="list">
{cards_html}
    </div>
  </main>
{FOOTER.format(year=datetime.date.today().year, home="index.html")}
{CONTACT}
</body>
</html>
"""


def sitemap(posts):
    today = datetime.date.today().isoformat()
    urls = [(f"{SITE}/", today), (f"{SITE}/blog.html", today)]
    for p in posts:
        urls.append((f"{SITE}/blog/{p['slug']}.html", (p.get("date", today) or today)[:10]))
    items = "\n".join(
        f"  <url><loc>{u}</loc><lastmod>{d}</lastmod></url>" for u, d in urls
    )
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{items}
</urlset>
"""


def main():
    posts = json.load(open(os.path.join(ROOT, "blog", "posts.json"), encoding="utf-8"))
    md = markdown.Markdown(extensions=["extra", "sane_lists", "smarty"])
    for p in posts:
        md.reset()
        src = open(os.path.join(ROOT, "blog", "posts", p["slug"] + ".md"), encoding="utf-8").read()
        # прибираємо перший H1 з md — заголовок ми рендеримо окремо
        lines = src.splitlines()
        if lines and lines[0].lstrip().startswith("# "):
            lines = lines[1:]
        body_html = md.convert("\n".join(lines).strip())
        # Робимо шляхи до картинок/файлів у тексті кореневими, щоб працювали
        # на сторінці blog/<slug>.html (пишіть у .md просто assets/foo.jpg).
        body_html = body_html.replace('src="assets/', 'src="/assets/').replace("src='assets/", "src='/assets/")
        body_html = body_html.replace('src="./assets/', 'src="/assets/')
        body_html = body_html.replace('href="assets/', 'href="/assets/')
        out = post_page(p, body_html)
        with open(os.path.join(ROOT, "blog", p["slug"] + ".html"), "w", encoding="utf-8") as f:
            f.write(out)
        print("  ->", f"blog/{p['slug']}.html")
    with open(os.path.join(ROOT, "blog.html"), "w", encoding="utf-8") as f:
        f.write(index_page(posts))
    print("  -> blog.html")
    with open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(sitemap(posts))
    print("  -> sitemap.xml")
    print(f"Готово: {len(posts)} статей.")


if __name__ == "__main__":
    main()
