#!/usr/bin/env python3
"""Build The Thai Base static pages.

Edit data/condos.json (projects), data/site.json (contact details) or the
page fragments in src/, then run from the repo root:

    python3 tools/build.py

Generated pages are written to the repo root so GitHub Pages serves them.
"""
import html
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = json.loads((ROOT / "data/site.json").read_text(encoding="utf-8"))
CONDOS = json.loads((ROOT / "data/condos.json").read_text(encoding="utf-8"))
SRC = ROOT / "src"

NAV = [
    ("/", "Home"),
    ("/condos/", "Condos"),
    ("/bang-na.html", "Living in Bang Na"),
    ("/renting-guide.html", "Renting guide"),
    ("/list-your-condo.html", "For owners"),
    ("/contact.html", "Contact"),
]

# Stations on the BTS Sukhumvit line, west to east, with x positions in the strip.
STATIONS = [("Punnawithi", 160), ("Udom Suk", 340), ("Bang Na", 520), ("Bearing", 690)]

e = html.escape


LABELS = {
    "en": {"wa": "Message on WhatsApp", "line": "Add us on LINE", "email": "Email us",
           "none": "Contact details are being set up."},
    "th": {"wa": "ทักทาง WhatsApp", "line": "เพิ่มเพื่อนใน LINE", "email": "ส่งอีเมล",
           "none": "กำลังจัดเตรียมช่องทางติดต่อ"},
}


def contact_links(cls="btn btn-primary", lang="en"):
    L = LABELS[lang]
    c = SITE["contact"]
    links = []
    if c.get("whatsapp"):
        num = "".join(ch for ch in c["whatsapp"] if ch.isdigit())
        links.append(f'<a class="{cls}" href="https://wa.me/{num}">{L["wa"]}</a>')
    if c.get("line"):
        lid = c["line"].strip()
        url = f"https://line.me/R/ti/p/{lid}" if lid.startswith("@") else f"https://line.me/ti/p/~{lid}"
        links.append(f'<a class="{cls}" href="{e(url)}">{L["line"]}</a>')
    if c.get("email"):
        links.append(f'<a class="{cls}" href="mailto:{e(c["email"])}">{L["email"]}</a>')
    if not links:
        return f'<p class="muted">{L["none"]}</p>'
    return '<div class="contact-links">' + "".join(links) + "</div>"


EN_FOOT = """
    <div>
      <h3>The Thai Base</h3>
      <p>Condo rentals in Bang Na for foreign professionals and families. Building facts come from public listings and are checked before each viewing.</p>
      {contact}
    </div>
    <div>
      <h3>Renters</h3>
      <ul>
        <li><a href="/condos/">Condos in Bang Na</a></li>
        <li><a href="/bang-na.html">Living in Bang Na</a></li>
        <li><a href="/renting-guide.html">Renting guide</a></li>
        <li><a href="/blog/thailand-visas.html">Visa types</a></li>
      </ul>
    </div>
    <div>
      <h3>Owners</h3>
      <ul>
        <li><a href="/list-your-condo.html">List your condo</a></li>
        <li><a href="/contact.html">Contact</a></li>
      </ul>
    </div>"""


FOOT_TH = """
    <div>
      <h3>The Thai Base</h3>
      <p>บริการปล่อยเช่าคอนโดในบางนาให้พนักงานและครอบครัวชาวต่างชาติ</p>
      {contact}
    </div>
    <div>
      <h3>สำหรับเจ้าของห้อง</h3>
      <ul>
        <li><a href="/th/list-your-condo.html">ลงประกาศคอนโด</a></li>
        <li><a href="/list-your-condo.html">English version</a></li>
      </ul>
    </div>
    <div>
      <h3>For renters</h3>
      <ul>
        <li><a href="/condos/">Condos in Bang Na</a></li>
        <li><a href="/renting-guide.html">Renting guide</a></li>
      </ul>
    </div>"""


def layout(path, title, desc, body, lang="en", nav_path=None, alternates=None):
    current = ' aria-current="page"'
    nav_path = nav_path or path
    alt = "".join(f'\n<link rel="alternate" hreflang="{hl}" href="{SITE["base_url"]}{href}">'
                  for hl, href in (alternates or []))
    thai_font = ('\n<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+Thai:wght@400;500;600;700&display=swap" rel="stylesheet">'
                 if lang == "th" else "")
    nav = "".join(
        f'<a href="{href}"{current if href == nav_path else ""}>{label}</a>'
        for href, label in NAV
    )
    full_title = f"{title} | {SITE['brand']}" if path != "/" else f"{SITE['brand']} — {SITE['tagline']}"
    canonical = SITE["base_url"] + path
    foot = (FOOT_TH.format(contact=contact_links("btn btn-ghost", "th")) if lang == "th"
            else EN_FOOT.format(contact=contact_links("btn btn-ghost")))
    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(full_title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{canonical}">{alt}
<meta property="og:title" content="{e(full_title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{canonical}">
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,600;12..96,700&family=Instrument+Sans:wght@400;500;600&display=swap" rel="stylesheet">{thai_font}
<link rel="stylesheet" href="/css/site.css">
</head>
<body>
<header class="site-head">
  <div class="wrap">
    <a class="brand" href="/">The Thai Base</a>
    <nav class="site-nav" aria-label="Main">{nav}</nav>
  </div>
</header>
<main>
{body}
</main>
<footer class="site-foot">
  <div class="wrap foot-grid">{foot}
  </div>
  <div class="wrap"><p class="small">© {date.today().year} The Thai Base</p></div>
</footer>
</body>
</html>
"""


def line_strip():
    xs = dict(STATIONS)
    parts = ['<line class="track" x1="20" y1="70" x2="780" y2="70"/>']
    for name, x in STATIONS:
        parts.append(
            f'<g class="station"><circle cx="{x}" cy="70" r="11"/>'
            f'<text x="{x}" y="45" text-anchor="middle">{e(name)}</text></g>'
        )
    parts.append('<g class="station"><text class="dir" x="20" y="105">← Siam, Asok</text>'
                 '<text class="dir" x="780" y="105" text-anchor="end">Samut Prakan →</text></g>')
    counts = {}
    for c in CONDOS:
        x = xs.get(c["station"])
        if x is None:
            continue
        i = counts.get(c["station"], 0)
        counts[c["station"]] = i + 1
        y = 140 + i * 30
        parts.append(
            f'<a href="/condos/{c["slug"]}.html">'
            f'<line class="stem" x1="{x}" y1="82" x2="{x}" y2="{y - 5}"/>'
            f'<circle class="pin" cx="{x}" cy="{y}" r="6"/>'
            f'<text x="{x + 14}" y="{y + 5}">{e(c["name"])}</text></a>'
        )
    height = 140 + max(counts.values(), default=1) * 30
    return (f'<div class="line-scroll"><svg class="line-svg" viewBox="0 0 800 {height}" role="img" '
            f'aria-label="BTS Sukhumvit line from Punnawithi to Bearing with condos by station">'
            + "".join(parts) + "</svg></div>")


def condo_rows(items):
    rows = []
    for c in items:
        badge = '<span class="badge">Units coming soon</span>' if c.get("featured") else ""
        rows.append(f"""<li class="condo-row">
  <h3><a href="/condos/{c['slug']}.html">{e(c['name'])}</a>{badge}</h3>
  <div><span class="station-tag">BTS {e(c['station'])}</span><div class="year">{e(c['walk'])}</div></div>
  <p class="muted" style="margin:0">{e(c['summary'])}</p>
  <div class="year">Built {c['completed']}</div>
</li>""")
    return '<ul class="condo-list">' + "".join(rows) + "</ul>"


def page_home():
    body = f"""
<section class="hero">
  <div class="wrap">
    <h1>Rent a condo in Bang Na, close to the BTS and the school belt</h1>
    <p>We help foreign professionals and families find a condo in Bang Na: real buildings, honest details and an English-speaking contact from first viewing to signed lease.</p>
    <div class="hero-actions">
      <a class="btn btn-primary" href="/condos/">See condos</a>
      <a class="btn btn-ghost" href="/contact.html">Tell us what you need</a>
    </div>
  </div>
  <div class="line-strip">
    <div class="wrap">
      <h2>Condos by BTS station</h2>
      <p class="hint">Bang Na sits on the same BTS Sukhumvit line as Asok and Siam. Choose a building to see its details.</p>
      {line_strip()}
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="section-head"><h2>Condos we cover</h2><a href="/condos/">All condos</a></div>
    {condo_rows(CONDOS)}
  </div>
</section>

<section class="section">
  <div class="wrap split">
    <div class="prose">
      <h2>Why Bang Na</h2>
      <p>Bang Na gives you more space for your rent than central Sukhumvit while staying on the same BTS line. Many of Bangkok's international schools sit along Bangna–Trad Road and Sukhumvit 105–107, and Suvarnabhumi Airport is a short drive east.</p>
      <p><a href="/bang-na.html">Read the area guide</a></p>
    </div>
    <div class="panel">
      <h3>How renting with us works</h3>
      <ol class="steps">
        <li>Tell us your budget, move-in date, and where you work or your children study.</li>
        <li>We send a shortlist of available units with photos.</li>
        <li>We arrange viewings, in person or by video call.</li>
        <li>We check the lease in English with you before you sign.</li>
      </ol>
      <a href="/renting-guide.html">What to expect when renting in Thailand</a>
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap split">
    <div class="panel panel-dark">
      <h2>Own a condo in Bang Na?</h2>
      <p>We market your unit to foreign tenants and handle viewings and the lease in English.</p>
      <a class="btn btn-primary" href="/list-your-condo.html">List your condo</a>
    </div>
    <div>
      <h2>Talk to us</h2>
      <p>Send your budget, bedrooms and move-in date. We reply in English or Thai.</p>
      {contact_links()}
    </div>
  </div>
</section>
"""
    return layout("/", "", "Condo rentals in Bang Na, Bangkok for expats: buildings near BTS Bang Na, Udom Suk and Punnawithi, the international school belt, and English-speaking support.", body)


def page_condos_index():
    body = f"""
<div class="wrap">
  <div class="detail-head">
    <h1>Condos in Bang Na</h1>
    <p class="prose muted">Buildings along the BTS Sukhumvit line from Punnawithi to Bearing. Each page lists the building's facts and what it suits; ask us for units that are available now.</p>
  </div>
  {condo_rows(CONDOS)}
  <p class="small muted" style="margin-top:24px">Looking for a building that isn't listed? <a href="/contact.html">Tell us</a> and we'll check availability.</p>
</div>
<div class="section"></div>
"""
    return layout("/condos/", "Condos for rent in Bang Na", "Condos for rent in Bang Na near BTS Bang Na and Punnawithi: The Coast Bangkok, Ideo O2, Ideo Mobi Sukhumvit Eastgate, Whizdom 101.", body)


def page_condo(c):
    facts = [("Nearest BTS", f"BTS {c['station']}"), ("Distance", c["walk"]), ("Completed", str(c["completed"]))]
    if c.get("developer"):
        facts.append(("Developer", c["developer"]))
    if c.get("towers"):
        facts.append(("Buildings", c["towers"]))
    if c.get("units"):
        facts.append(("Size", c["units"]))
    facts_html = "".join(f"<div><dt>{e(k)}</dt><dd>{e(v)}</dd></div>" for k, v in facts)
    fac = "".join(f"<li>{e(x)}</li>" for x in c["facilities"])
    near = "".join(f"<li>{e(x)}</li>" for x in c["nearby"])
    src = "".join(f'<li><a href="{e(u)}" rel="nofollow">{e(t)}</a></li>' for t, u in c["sources"])
    avail = ("<p><strong>Units here are coming to the site soon.</strong> Message us now to hear about them first.</p>"
             if c.get("featured") else
             "<p>Ask us which units in this building are available now.</p>")
    body = f"""
<div class="wrap">
  <nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a> / <a href="/condos/">Condos</a> / {e(c['name'])}</nav>
  <div class="detail-head">
    <h1>{e(c['name'])}</h1>
    <p class="prose" style="font-size:1.1rem">{e(c['summary'])}</p>
    <dl class="facts">{facts_html}</dl>
  </div>
  <div class="split">
    <div class="prose">
      <h2>Who it suits</h2>
      <p>{e(c['good_for'])}</p>
      <h3>Unit types</h3>
      <p>{e(c['unit_types'])}</p>
      <h3>Facilities</h3>
      <ul class="ticks">{fac}</ul>
      <h3>Nearby</h3>
      <ul class="ticks">{near}</ul>
    </div>
    <div>
      <div class="panel">
        <h2>Rent a unit here</h2>
        {avail}
        {contact_links()}
      </div>
      <div class="notice small">Building details come from public listings and may change. We confirm everything at the viewing.</div>
      <p class="small muted">Sources</p>
      <ul class="small">{src}</ul>
    </div>
  </div>
</div>
<div class="section"></div>
"""
    desc = f"{c['name']} condo for rent in Bang Na, Bangkok. {c['walk']}. Facilities, unit types and nearby schools and shops."
    return layout(f"/condos/{c['slug']}.html", f"{c['name']} — condo for rent near BTS {c['station']}", desc, body)


OWNER_ALTERNATES = [("en", "/list-your-condo.html"), ("th", "/th/list-your-condo.html")]


def page_fragment(name, path, title, desc, lang="en", nav_path=None, alternates=None):
    frag = (SRC / name).read_text(encoding="utf-8").replace("{{CONTACT}}", contact_links(lang=lang))
    return layout(path, title, desc, frag, lang, nav_path, alternates)


def write(rel, content):
    out = ROOT / rel
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(content, encoding="utf-8")
    return rel


def main():
    pages = [
        ("index.html", "/", page_home()),
        ("condos/index.html", "/condos/", page_condos_index()),
    ]
    for c in CONDOS:
        pages.append((f"condos/{c['slug']}.html", f"/condos/{c['slug']}.html", page_condo(c)))
    for name, path, title, desc in [
        ("bang-na.html", "/bang-na.html", "Living in Bang Na: a guide for expats",
         "What it's like to live in Bang Na, Bangkok: BTS stations, international schools, shopping, hospitals and getting to the airport."),
        ("renting-guide.html", "/renting-guide.html", "Renting a condo in Thailand as a foreigner",
         "Deposits, leases, TM30 reporting, utilities and what to check before you sign a condo lease in Thailand."),
        ("list-your-condo.html", "/list-your-condo.html", "List your Bang Na condo for foreign tenants",
         "Rent your Bang Na condo to foreign professionals and families. We handle marketing, viewings and the lease in English."),
        ("th/list-your-condo.html", "/th/list-your-condo.html", "ปล่อยเช่าคอนโดบางนาให้ผู้เช่าชาวต่างชาติ",
         "ปล่อยเช่าคอนโดในบางนาให้พนักงานและครอบครัวชาวต่างชาติ เราดูแลการตลาด การพาชมห้อง และสัญญาเช่าภาษาอังกฤษให้"),
        ("contact.html", "/contact.html", "Contact",
         "Contact The Thai Base about condo rentals in Bang Na."),
        ("404.html", "/404.html", "Page not found", "Page not found."),
    ]:
        kw = {}
        if name.endswith("list-your-condo.html"):
            kw["alternates"] = OWNER_ALTERNATES
            if name.startswith("th/"):
                kw.update(lang="th", nav_path="/list-your-condo.html")
        pages.append((name, path, page_fragment(name, path, title, desc, **kw)))

    for rel, _, content in pages:
        write(rel, content)

    urls = [p for _, p, _ in pages if p != "/404.html"]
    sitemap = ['<?xml version="1.0" encoding="UTF-8"?>',
               '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    sitemap += [f"  <url><loc>{SITE['base_url']}{u}</loc></url>" for u in urls]
    sitemap.append("</urlset>")
    write("sitemap.xml", "\n".join(sitemap) + "\n")
    write("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {SITE['base_url']}/sitemap.xml\n")

    print(f"Built {len(pages)} pages.")
    if not any(SITE["contact"].values()):
        print("WARNING: no contact details in data/site.json — pages show 'Contact details are being set up.'")


if __name__ == "__main__":
    main()
