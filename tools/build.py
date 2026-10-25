#!/usr/bin/env python3
"""Build The Thai Base static pages.

Edit data/condos.json (projects), data/site.json (contact details) or the
page fragments in src/, then run from the repo root:

    python3 tools/build.py

Generated pages are written to the repo root so GitHub Pages serves them.
"""
import html
import json
from urllib.parse import quote
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = json.loads((ROOT / "data/site.json").read_text(encoding="utf-8"))
CONDOS = json.loads((ROOT / "data/condos.json").read_text(encoding="utf-8"))
SRC = ROOT / "src"

NAV = [
    ("/condos/", "Condos"),
    ("/bang-na.html", "Living in Bang Na"),
    ("/renting-guide.html", "Renting guide"),
    ("/list-your-condo.html", "For owners"),
]

_units_file = ROOT / "data/units.json"
UNITS = json.loads(_units_file.read_text(encoding="utf-8")) if _units_file.exists() else []
CONDO_BY_SLUG = {c["slug"]: c for c in CONDOS}
# "pending" units are kept in the data file but not published until their details are filled in.
UNITS = [u for u in UNITS if not u.get("pending")]
LIVE_UNITS = [u for u in UNITS if not u.get("draft")]


def is_sale(u):
    return u.get("deal") == "sale"


RENT_UNITS = [u for u in LIVE_UNITS if not is_sale(u)]
SALE_UNITS = [u for u in LIVE_UNITS if is_sale(u)]
if SALE_UNITS:
    NAV.insert(1, ("/sale/", "For sale"))
if RENT_UNITS:
    NAV.insert(1, ("/rent/", "For rent"))

# Stations on the BTS Sukhumvit line, west to east, with x positions in the strip.
STATIONS = [("Udom Suk", 140), ("Bang Na", 400), ("Bearing", 660)]

# Condos are grouped by zone so new areas can be added later; the site currently markets one.
ZONE_NAME = SITE.get("zone", "BTS Bang Na")
CONDO_NAMES = ", ".join(c["name"] for c in CONDOS[:-1]) + f" and {CONDOS[-1]['name']}" if len(CONDOS) > 1 else CONDOS[0]["name"]
RENTS_AS_OF = SITE.get("rents_as_of", "")
RENTS_AS_OF_TH = SITE.get("rents_as_of_th", RENTS_AS_OF)

e = html.escape


LABELS = {
    "en": {"wa": "Message on WhatsApp", "line": "Add us on LINE", "email": "Email us",
           "none": "Contact details are being set up."},
    "th": {"wa": "ทักทาง WhatsApp", "line": "เพิ่มเพื่อนใน LINE", "email": "ส่งอีเมล",
           "none": "กำลังจัดเตรียมช่องทางติดต่อ"},
}


def line_url():
    lid = SITE["contact"].get("line", "").strip()
    if not lid:
        return ""
    return f"https://line.me/R/ti/p/{lid}" if lid.startswith("@") else f"https://line.me/ti/p/~{lid}"


BRAND_MARK = ('<span class="brand-mark" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="#fff" '
              'stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 10.5 12 4l9 6.5"/>'
              '<path d="M5 9.5V20h14V9.5"/><path d="M10 20v-5h4v5"/></svg></span>')


def contact_links(cls="btn btn-primary", lang="en"):
    L = LABELS[lang]
    c = SITE["contact"]
    links = []
    if c.get("whatsapp"):
        num = "".join(ch for ch in c["whatsapp"] if ch.isdigit())
        links.append(f'<a class="{cls}" href="https://wa.me/{num}">{L["wa"]}</a>')
    if c.get("line"):
        line_cls = cls.replace("btn-primary", "btn-line")
        links.append(f'<a class="{line_cls}" href="{e(line_url())}">{L["line"]}</a>')
    if c.get("email"):
        links.append(f'<a class="{cls}" href="mailto:{e(c["email"])}">{L["email"]}</a>')
    if not links:
        return f'<p class="muted">{L["none"]}</p>'
    return '<div class="contact-links">' + "".join(links) + "</div>"


EN_FOOT = """
    <div>
      <h3>The Thai Base</h3>
      <p>Condos for rent at BTS Bang Na: The Coast Bangkok, Ideo O2, Ideo Mobi Eastgate and Ideo Mobi Eastpoint. We help Thai and foreign renters, in Thai or English.</p>
      {contact}
    </div>
    <div>
      <h3>Renters</h3>
      <ul>
        <li><a href="/condos/">Our four condos</a></li>
        <li><a href="/th/">ภาษาไทย</a></li>
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
      <p>คอนโดให้เช่าย่าน BTS บางนา: The Coast Bangkok, Ideo O2, Ideo Mobi Eastgate และ Ideo Mobi Eastpoint ดูแลทั้งผู้เช่าคนไทยและชาวต่างชาติ</p>
      {contact}
    </div>
    <div>
      <h3>สำหรับผู้เช่า</h3>
      <ul>
        <li><a href="/th/">คอนโดทั้ง 4 โครงการ</a></li>
        <li><a href="/rent/">ห้องว่างให้เช่า</a></li>
      </ul>
    </div>
    <div>
      <h3>สำหรับเจ้าของห้อง</h3>
      <ul>
        <li><a href="/th/list-your-condo.html">ฝากเช่าคอนโด</a></li>
        <li><a href="/">English</a></li>
      </ul>
    </div>"""


def layout(path, title, desc, body, lang="en", nav_path=None, alternates=None, noindex=False):
    current = ' aria-current="page"'
    nav_path = nav_path or path
    alt = "".join(f'\n<link rel="alternate" hreflang="{hl}" href="{SITE["base_url"]}{href}">'
                  for hl, href in (alternates or []))
    if noindex:
        alt += '\n<meta name="robots" content="noindex">'
    nav = "".join(
        f'<a href="{href}"{current if href == nav_path else ""}>{label}</a>'
        for href, label in NAV
    )
    full_title = f"{title} | {SITE['brand']}" if path != "/" else f"{SITE['brand']} — {SITE['tagline']}"
    canonical = SITE["base_url"] + path
    lang_href, lang_label, lang_code = (("/", "English", "en") if lang == "th" else ("/th/", "ภาษาไทย", "th"))
    for hl, href in (alternates or []):
        if hl != lang:
            lang_href = href
    line_btn = (f'<a class="btn btn-line btn-sm" href="{e(line_url())}">{"ทัก LINE" if lang == "th" else "Chat on LINE"}</a>'
                if line_url() else "")
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
<link href="https://fonts.googleapis.com/css2?family=Manrope:wght@600;700;800&family=IBM+Plex+Sans+Thai:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/css/site.css">
<script src="/assets/admin.js" defer></script>
</head>
<body>
<header class="site-head">
  <div class="wrap">
    <a class="brand" href="{'/th/' if lang == 'th' else '/'}">{BRAND_MARK}The Thai Base<span class="brand-tag">Bang Na</span></a>
    <nav class="site-nav" aria-label="Main">{nav}</nav>
    <div class="head-actions">
      <a class="lang-btn" href="{lang_href}" hreflang="{lang_code}" lang="{lang_code}">{lang_label}</a>
      {line_btn}
    </div>
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


def line_strip(lang="en"):
    xs = dict(STATIONS)
    parts = ['<line class="track" x1="20" y1="70" x2="780" y2="70"/>']
    for name, x in STATIONS:
        parts.append(
            f'<g class="station"><circle cx="{x}" cy="70" r="11"/>'
            f'<text x="{x}" y="45" text-anchor="middle">{e(name)}</text></g>'
        )
    left, right = ("← Asok, Siam", "Samut Prakan →") if lang == "en" else ("← อโศก สยาม", "สมุทรปราการ →")
    parts.append(f'<g class="station"><text class="dir" x="20" y="105">{left}</text>'
                 f'<text class="dir" x="780" y="105" text-anchor="end">{right}</text></g>')
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
    label = ("BTS Sukhumvit line from Udom Suk to Bearing, with our four condos at BTS Bang Na" if lang == "en"
             else "รถไฟฟ้า BTS สายสุขุมวิท จากอุดมสุขถึงแบริ่ง และคอนโด 4 โครงการใกล้ BTS บางนา")
    return (f'<div class="line-scroll"><svg class="line-svg" viewBox="0 0 800 {height}" role="img" '
            f'aria-label="{e(label)}">' + "".join(parts) + "</svg></div>")


def units_here(c, sale=False):
    return [u for u in LIVE_UNITS if u["condo"] == c["slug"] and is_sale(u) == sale
            and u.get("status") not in ("rented", "sold")]


def rent_from(c):
    return min(r["typical"] for r in c["rents"]) if c.get("rents") else None


def condo_rows(items, lang="en"):
    rows = []
    for c in items:
        n = len(units_here(c))
        ns = len(units_here(c, sale=True))
        badge = ""
        if n:
            badge += (f'<span class="badge">{n} unit{"s" if n > 1 else ""} for rent</span>' if lang == "en"
                      else f'<span class="badge">ให้เช่า {n} ห้อง</span>')
        if ns:
            badge += (f'<span class="badge badge-sale">{ns} for sale</span>' if lang == "en"
                      else f'<span class="badge badge-sale">ขาย {ns} ห้อง</span>')
        frm = rent_from(c)
        price = ""
        if frm:
            price = (f'<div class="row-rent">from {baht(frm)}<span>/month</span></div>' if lang == "en"
                     else f'<div class="row-rent">เริ่ม {baht(frm)}<span>/เดือน</span></div>')
        summary = c["summary"] if lang == "en" else c.get("summary_th", c["summary"])
        walk = c["walk"] if lang == "en" else c.get("walk_th", c["walk"])
        built = f"Built {c['completed']}" if lang == "en" else f"สร้างเสร็จ {c['completed']}"
        rows.append(f"""<li class="condo-row">
  <h3><a href="/condos/{c['slug']}.html">{e(c['name'])}</a>{badge}</h3>
  <div><span class="station-tag">BTS {e(c['station'])}</span><div class="year">{e(walk)}</div></div>
  <p class="muted" style="margin:0">{e(summary)}</p>
  <div class="year">{price}{built} · {e(c['units'].replace(' units', ''))} {'units' if lang == 'en' else 'ห้อง'}</div>
</li>""")
    return '<ul class="condo-list">' + "".join(rows) + "</ul>"


def rent_note(lang="en"):
    if lang == "en":
        return (f"Typical asking rents for 12-month leases, from public listings in {RENTS_AS_OF}. "
                "Furnishing, floor and view move the price; ask us for units available now.")
    return (f"ค่าเช่าที่ตั้งประกาศโดยทั่วไป สำหรับสัญญา 12 เดือน จากประกาศเช่าสาธารณะ ณ {RENTS_AS_OF_TH} "
            "ค่าเช่าจริงขึ้นกับการตกแต่ง ชั้น และวิว สอบถามห้องว่างตอนนี้ได้เลย")


def rent_compare(lang="en"):
    """One table comparing typical rents across all condos, by unit type."""
    order = ["Studio", "1 bedroom", "1-bedroom duplex", "2 bedrooms", "3 bedrooms"]
    th = {"Studio": "สตูดิโอ", "1 bedroom": "1 ห้องนอน", "1-bedroom duplex": "1 นอน ดูเพล็กซ์",
          "2 bedrooms": "2 ห้องนอน", "3 bedrooms": "3 ห้องนอน"}
    types = [t for t in order if any(r["type"] == t for c in CONDOS for r in c.get("rents", []))]
    head = "".join(f'<th scope="col">{e(t if lang == "en" else th[t])}</th>' for t in types)
    body = []
    for c in CONDOS:
        by = {r["type"]: r for r in c.get("rents", [])}
        cells = "".join(f'<td>{baht(by[t]["typical"])}</td>' if t in by else '<td class="na">—</td>' for t in types)
        body.append(f'<tr><th scope="row"><a href="/condos/{c["slug"]}.html">{e(c["name"])}</a></th>{cells}</tr>')
    first = "Condo" if lang == "en" else "โครงการ"
    return (f'<div class="table-scroll"><table class="rent-table"><thead><tr><th scope="col">{first}</th>{head}</tr></thead>'
            f'<tbody>{"".join(body)}</tbody></table></div><p class="small muted">{e(rent_note(lang))}</p>')


def rent_table(c, lang="en"):
    if not c.get("rents"):
        return ""
    hd = ("Unit type", "Typical", "Usual range") if lang == "en" else ("ประเภทห้อง", "ค่าเช่าทั่วไป", "ช่วงราคา")
    rows = "".join(
        f'<tr><th scope="row">{e(r["type"] if lang == "en" else r["type_th"])}</th><td>{baht(r["typical"])}</td>'
        f'<td>{baht(r["low"])} – {baht(r["high"])}</td></tr>' for r in c["rents"])
    return (f'<div class="table-scroll"><table class="rent-table"><thead><tr><th scope="col">{hd[0]}</th>'
            f'<th scope="col">{hd[1]}</th><th scope="col">{hd[2]}</th></tr></thead><tbody>{rows}</tbody></table></div>'
            f'<p class="small muted">{e(rent_note(lang))}</p>')


HOME_ALTERNATES = [("en", "/"), ("th", "/th/")]


def featured_card(lang="en"):
    c = next((x for x in CONDOS if x.get("featured")), CONDOS[0])
    here = units_here(c)
    rents = [u["rent_thb"] for u in here if u.get("rent_thb")]
    if c.get("photos"):
        photo, alt = c["photos"][0]["src"], c["photos"][0]["alt"]
    else:
        photo, alt = next((u["photos"][0] for u in here if u.get("photos")), ""), ""
    img = f'<img src="{e(photo)}" alt="{e(alt)}" width="1200" height="900">' if photo else ""
    walk = c["walk"] if lang == "en" else c.get("walk_th", c["walk"])
    if lang == "en":
        tag, count, per = "Featured building", f'{len(here)} unit{"s" if len(here) != 1 else ""} from', "/ month"
    else:
        tag, count, per = "โครงการแนะนำ", f"ว่าง {len(here)} ห้อง เริ่ม", "/ เดือน"
    price = (f'<div class="feature-price"><small>{count}</small><strong>{baht(min(rents))}<span> {per}</span></strong></div>'
             if rents else "")
    return f"""<a class="feature-card" href="/condos/{c['slug']}.html">
  <div class="feature-media">{img}<span class="chip">{tag}</span></div>
  <div class="feature-body">
    <div><span class="feature-name">{e(c['name'])}</span><span class="station-line"><span class="bts">BTS</span>{e(c['station'])} · {e(walk)}</span></div>
    {price}
  </div>
</a>"""


def building_photos(lang="en"):
    """Photo strip of the featured building for the home page."""
    c = next((x for x in CONDOS if x.get("featured")), None)
    if not c or len(c.get("photos", [])) < 2:
        return ""
    en = lang == "en"
    tiles = "".join(f'<li><img src="{e(p["src"])}" alt="{e(p["alt"])}" loading="lazy" width="600" height="450"></li>'
                    for p in c["photos"][1:6])
    credit = (f'<p class="small muted photo-credit">{"Photos" if en else "ภาพ"}: {e(c["photo_credit"])}, '
              f'{"used with permission" if en else "ใช้โดยได้รับอนุญาต"}.</p>' if c.get("photo_credit") else "")
    head = ("Inside The Coast Bangkok" if en else f"บรรยากาศ {c['name']}")
    sub = (f"{c['walk']}, next to BITEC, with pools, a gym and a community mall at its base."
           if en else f"{c.get('walk_th', c['walk'])} ติดไบเทค มีสระว่ายน้ำ ฟิตเนส และคอมมูนิตี้มอลล์ด้านล่าง")
    link = (f'<a href="/condos/{c["slug"]}.html">{"Building details" if en else "ข้อมูลโครงการ"} →</a>')
    return f"""<section class="section">
  <div class="wrap">
    <div class="section-head"><div><h2>{e(head)}</h2><p>{e(sub)}</p></div>{link}</div>
    <ul class="photo-strip">{tiles}</ul>
    {credit}
  </div>
</section>"""


def search_form(lang="en"):
    en = lang == "en"
    beds = [("", "Any" if en else "ทั้งหมด"), ("1", "1 bedroom" if en else "1 ห้องนอน"), ("2", "2 bedrooms" if en else "2 ห้องนอน")]
    budget = [("", "Any budget" if en else "ไม่จำกัด"), ("20000", "Up to ฿20,000" if en else "ไม่เกิน ฿20,000"),
              ("30000", "Up to ฿30,000" if en else "ไม่เกิน ฿30,000"), ("40000", "Up to ฿40,000" if en else "ไม่เกิน ฿40,000")]
    opts = lambda xs: "".join(f'<option value="{v}">{e(t)}</option>' for v, t in xs)
    return f"""<form class="search-bar" action="/rent/" method="get" role="search">
  <label class="search-field"><span>{"Bedrooms" if en else "ห้องนอน"}</span><select name="beds">{opts(beds)}</select></label>
  <label class="search-field"><span>{"Budget / month" if en else "งบต่อเดือน"}</span><select name="max">{opts(budget)}</select></label>
  <button class="btn btn-primary" type="submit">{"See available units" if en else "ดูห้องว่าง"} →</button>
</form>"""


def owners_band(lang="en"):
    if lang == "en":
        return f"""<section class="section">
  <div class="wrap">
    <div class="panel-dark cta-band">
      <div>
        <h2>Own a unit in one of these buildings?</h2>
        <p>Listing is free. You pay one month's rent only when we find your tenant on a one-year lease.</p>
      </div>
      <div class="btns">
        <a class="btn btn-line" href="{e(line_url())}">Add us on LINE {e(SITE['contact'].get('line', ''))}</a>
        <a class="btn btn-ghost" href="/list-your-condo.html">How listing works</a>
      </div>
    </div>
  </div>
</section>"""
    return f"""<section class="section">
  <div class="wrap">
    <div class="panel-dark cta-band">
      <div>
        <h2>มีห้องในโครงการเหล่านี้?</h2>
        <p>ฝากเช่าฟรี ไม่มีวันหมดอายุ จ่ายค่าบริการ 1 เดือน เฉพาะเมื่อได้ผู้เช่าสัญญา 1 ปีผ่านเรา</p>
      </div>
      <div class="btns">
        <a class="btn btn-line" href="{e(line_url())}">เพิ่มเพื่อน LINE {e(SITE['contact'].get('line', ''))}</a>
        <a class="btn btn-ghost" href="/th/list-your-condo.html">ฝากเช่ากับเรา</a>
      </div>
    </div>
  </div>
</section>"""


def page_home():
    units_block = ""
    if RENT_UNITS:
        units_block = f"""
<section class="section">
  <div class="wrap">
    <div class="section-head"><div><h2>Available now</h2><p>Units we have checked in person, with real photos.</p></div><a href="/rent/">All {len(RENT_UNITS)} units for rent →</a></div>
    {unit_cards(RENT_UNITS[:6])}
    <p class="small muted" style="margin-top:12px">{e(FAIR_NOTE['en'])}</p>
  </div>
</section>"""
    if SALE_UNITS:
        units_block += f"""
<section class="section">
  <div class="wrap">
    <div class="section-head"><h2>Units for sale</h2><a href="/sale/">All units for sale →</a></div>
    {unit_cards(SALE_UNITS[:6])}
  </div>
</section>"""
    body = f"""
<section class="hero">
  <div class="wrap hero-grid">
    <div>
      <p class="eyebrow">Condo rentals for expats · BTS Bang Na</p>
      <h1>Bang Na condos, checked before you see them.</h1>
      <p class="hero-lead">Real units at {e(CONDO_NAMES)}, with real photos and a fair-price check against each building's typical rent. We help in Thai or English, from first viewing to move-in.</p>
      {search_form()}
      <ul class="trust"><li>Units visited in person</li><li>No fee for renters</li><li>Help in English &amp; Thai</li></ul>
    </div>
    {featured_card()}
  </div>
</section>
{building_photos()}
{units_block}
<section class="section">
  <div class="wrap">
    <div class="section-head"><div><h2>Why Bang Na</h2><p>More space for the money than central Sukhumvit, still on the BTS line.</p></div><a href="/bang-na.html">Living in Bang Na →</a></div>
    <ul class="tiles">
      <li class="tile"><h3>On the BTS Sukhumvit line</h3><p>About 20–25 minutes to Asok without changing trains.</p></li>
      <li class="tile"><h3>Next to BITEC</h3><p>Central Bangna and Mega Bangna for shopping and groceries.</p></li>
      <li class="tile"><h3>International schools</h3><p>Bangkok Patana, St. Andrews, Berkeley and more in the area.</p></li>
      <li class="tile"><h3>Toward Suvarnabhumi</h3><p>On the airport side of the city via Bangna–Trad Road.</p></li>
    </ul>
    <div class="line-strip">
      <h3>All four condos are around BTS Bang Na</h3>
      <p class="hint">Choose a building to see its details.</p>
      {line_strip()}
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="section-head"><h2>Which condo fits your budget</h2><a href="/condos/">Building details →</a></div>
    {rent_compare()}
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="section-head"><h2>How renting with us works</h2><a href="/renting-guide.html">Renting guide →</a></div>
    <ol class="step-list">
      <li><h3>Tell us what you need</h3><p>Budget, bedrooms, move-in date and where you work or study. Message us on LINE.</p></li>
      <li><h3>Get a shortlist</h3><p>Available units across the four buildings, with photos and our notes.</p></li>
      <li><h3>View in person or by video</h3><p>Still abroad? We walk you through the unit on a live video call.</p></li>
      <li><h3>Sign and move in</h3><p>We go through the lease with you and record the unit's condition at move-in.</p></li>
    </ol>
  </div>
</section>
{owners_band()}
"""
    return layout("/", "", f"Condos for rent at BTS Bang Na: {CONDO_NAMES}. Units checked in person, real photos, fair-price check, viewings in Thai or English.",
                  body, alternates=HOME_ALTERNATES)


def page_home_th():
    units_block = ""
    if RENT_UNITS:
        units_block = f"""
<section class="section">
  <div class="wrap">
    <div class="section-head"><div><h2>ห้องว่างให้เช่าตอนนี้</h2><p>ห้องที่เราไปดูมาแล้ว พร้อมรูปจริง</p></div><a href="/rent/">ดูห้องเช่าทั้งหมด {len(RENT_UNITS)} ห้อง →</a></div>
    {unit_cards(RENT_UNITS[:6], "th")}
    <p class="small muted" style="margin-top:12px">{e(FAIR_NOTE['th'])}</p>
  </div>
</section>"""
    if SALE_UNITS:
        units_block += f"""
<section class="section">
  <div class="wrap">
    <div class="section-head"><h2>ห้องขาย</h2><a href="/sale/">ดูห้องขายทั้งหมด →</a></div>
    {unit_cards(SALE_UNITS[:6], "th")}
  </div>
</section>"""
    body = f"""
<section class="hero">
  <div class="wrap hero-grid">
    <div>
      <p class="eyebrow">คอนโดให้เช่า ใกล้ BTS บางนา</p>
      <h1>คอนโดบางนา ตรวจห้องให้ก่อนคุณไปดู</h1>
      <p class="hero-lead">ห้องจริงใน {e(CONDO_NAMES)} รูปจริง และเทียบค่าเช่ากับราคาทั่วไปของแต่ละโครงการ ดูแลทั้งภาษาไทยและอังกฤษ ตั้งแต่ดูห้องจนถึงวันย้ายเข้า</p>
      {search_form("th")}
      <ul class="trust"><li>ไปดูห้องจริงทุกห้อง</li><li>ผู้เช่าไม่เสียค่าบริการ</li><li>คุยได้ทั้งไทยและอังกฤษ</li></ul>
    </div>
    {featured_card("th")}
  </div>
</section>
{building_photos("th")}
{units_block}
<section class="section">
  <div class="wrap">
    <div class="section-head"><h2>ทั้ง 4 โครงการอยู่รอบ BTS บางนา</h2></div>
    <div class="line-strip" style="margin-top:0">
      <p class="hint">BTS สายสุขุมวิท ไปอโศกประมาณ 20–25 นาทีโดยไม่ต้องเปลี่ยนขบวน กดชื่อโครงการเพื่อดูรายละเอียด</p>
      {line_strip("th")}
    </div>
  </div>
</section>

<section class="section" id="compare">
  <div class="wrap">
    <div class="section-head"><h2>โครงการไหนเข้ากับงบของคุณ</h2></div>
    {rent_compare("th")}
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="section-head"><h2>ขั้นตอนเช่ากับเรา</h2></div>
    <ol class="step-list">
      <li><h3>บอกสิ่งที่ต้องการ</h3><p>งบ จำนวนห้องนอน วันที่อยากย้ายเข้า และที่ทำงานหรือที่เรียน ทักเราทาง LINE</p></li>
      <li><h3>รับรายการห้อง</h3><p>ห้องว่างจากทั้ง 4 โครงการ พร้อมรูปและข้อสังเกตของเรา</p></li>
      <li><h3>ดูห้องจริงหรือวิดีโอคอล</h3><p>อยู่ต่างประเทศก็ดูห้องผ่านวิดีโอคอลสดได้</p></li>
      <li><h3>เซ็นสัญญาและย้ายเข้า</h3><p>อธิบายสัญญาก่อนเซ็น และบันทึกสภาพห้องวันย้ายเข้า</p></li>
    </ol>
  </div>
</section>
{owners_band("th")}
"""
    return layout("/th/", "คอนโดให้เช่า ใกล้ BTS บางนา",
                  "คอนโดให้เช่าใกล้ BTS บางนา 4 โครงการ: The Coast Bangkok, Ideo O2, Ideo Mobi Eastgate, Ideo Mobi Eastpoint ห้องจริง รูปจริง เทียบค่าเช่า นัดชมห้องได้เลย",
                  body, lang="th", nav_path="/th/", alternates=HOME_ALTERNATES)


def page_condos_index():
    body = f"""
<div class="wrap">
  <div class="detail-head">
    <h1>Our four condos at BTS Bang Na</h1>
    <p class="prose muted">Every building we cover is within reach of BTS Bang Na. Each page lists the building's facts, typical rents and who it suits; ask us for units that are available now.</p>
  </div>
  {condo_rows(CONDOS)}
  <section class="section">
    <h2>Typical rents compared</h2>
    {rent_compare()}
  </section>
</div>
<div class="section"></div>
"""
    return layout("/condos/", "Condos for rent at BTS Bang Na",
                  f"Condos for rent at BTS Bang Na: {CONDO_NAMES}. Facilities, unit types and typical rents.", body)


def page_condo(c):
    facts = [("Nearest BTS", f"BTS {c['station']}"), ("Distance", c["walk"]), ("Completed", str(c["completed"]))]
    if c.get("developer"):
        facts.append(("Developer", c["developer"]))
    if c.get("towers"):
        facts.append(("Buildings", c["towers"]))
    if c.get("units"):
        facts.append(("Size", c["units"]))
    if rent_from(c):
        facts.append(("Rents from", f"{baht(rent_from(c))} / month"))
    facts_html = "".join(f"<div><dt>{e(k)}</dt><dd>{e(v)}</dd></div>" for k, v in facts)
    fac = "".join(f"<li>{e(x)}</li>" for x in c["facilities"])
    near = "".join(f"<li>{e(x)}</li>" for x in c["nearby"])
    src = "".join(f'<li><a href="{e(u)}" rel="nofollow">{e(t)}</a></li>' for t, u in c["sources"])
    here = [u for u in RENT_UNITS if u["condo"] == c["slug"]]
    here_sale = [u for u in SALE_UNITS if u["condo"] == c["slug"]]
    units_section = (f'<section class="section"><h2>Units for rent here</h2>{unit_cards(here)}</section>' if here else "")
    units_section += (f'<section class="section"><h2>Units for sale here</h2>{unit_cards(here_sale)}</section>' if here_sale else "")
    avail = ("<p>Ask us which units in this building are available now. We can also check the other three buildings at BTS Bang Na in the same search.</p>")
    others = "".join(f'<li><a href="/condos/{o["slug"]}.html">{e(o["name"])}</a>'
                     + (f' — from {baht(rent_from(o))}' if rent_from(o) else "") + "</li>"
                     for o in CONDOS if o["slug"] != c["slug"])
    th = (f'<p lang="th" class="muted">{e(c["summary_th"])}</p>' if c.get("summary_th") else "")
    body = f"""
<div class="wrap">
  <nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a> / <a href="/condos/">Condos</a> / {e(c['name'])}</nav>
  <div class="detail-head">
    <h1>{e(c['name'])}</h1>
    <p class="prose" style="font-size:1.1rem">{e(c['summary'])}</p>
    {th}
    <dl class="facts">{facts_html}</dl>
  </div>
  <div class="split">
    <div class="prose">
      <h2>Typical rents</h2>
      {rent_table(c)}
      <h2>Who it suits</h2>
      <p>{e(c['good_for'])}</p>
      <h3>Unit types</h3>
      <p>{e(c['unit_types'])}</p>
      <h3>Facilities</h3>
      <ul class="ticks">{fac}</ul>
      <h3>Nearby</h3>
      <ul class="ticks">{near}</ul>
      <h3>Sources</h3>
      <ul class="small">{src}</ul>
    </div>
    <div>
      <div class="panel">
        <h2>Rent a unit here</h2>
        {avail}
        {contact_links()}
      </div>
      <div class="panel" style="margin-top:16px">
        <h3>The other buildings at BTS Bang Na</h3>
        <ul class="plain">{others}</ul>
      </div>
      <div class="notice small">Building details and rents come from public listings and may change. We confirm everything at the viewing.</div>
    </div>
  </div>
  {units_section}
</div>
<div class="section"></div>
"""
    desc = (f"{c['name']} condo for rent near BTS {c['station']}, Bangkok. {c['walk']}. "
            f"Typical rents, unit types and facilities.")
    return layout(f"/condos/{c['slug']}.html", f"{c['name']} — condo for rent near BTS {c['station']}", desc, body)


OWNER_ALTERNATES = [("en", "/list-your-condo.html"), ("th", "/th/list-your-condo.html")]


def baht(n):
    return f"฿{n:,.0f}"


def line_ask_url(text):
    lid = SITE["contact"].get("line", "").strip()
    if not lid.startswith("@"):
        return None
    return f"https://line.me/R/oaMessage/{lid}/?{quote(text)}"


def unit_title(u):
    beds = "Studio" if u["bedrooms"] == 0 else f'{u["bedrooms"]}-bedroom'
    return f'{beds}, {u["size_sqm"]:g} sq m'


def unit_url(u):
    return f"/{'sale' if is_sale(u) else 'rent'}/{u['slug']}.html"


def unit_price(u, lang="en"):
    """Price line for cards and the unit page: monthly rent, or the sale price."""
    if is_sale(u):
        if u.get("price_thb"):
            return baht(u["price_thb"])
        return "Price on request" if lang == "en" else "สอบถามราคา"
    if u.get("rent_thb"):
        return f"{baht(u['rent_thb'])}<span> / {'month' if lang == 'en' else 'เดือน'}</span>"
    return "Rent on request" if lang == "en" else "สอบถามค่าเช่า"


def unit_price_text(u):
    if is_sale(u):
        return baht(u["price_thb"]) if u.get("price_thb") else "Price on request"
    return f"{baht(u['rent_thb'])}/month" if u.get("rent_thb") else "Rent on request"


def floor_text(u, lang="en", tower=False):
    """Public pages show a floor range only. Signed-in admins see the exact floor
    (filled in by /assets/admin.js from the encrypted admin data)."""
    band = u.get("floor_band")
    label = (f"Floors {band}" if lang == "en" else f"ชั้น {band}") if band else ""
    if tower and u.get("tower"):
        label = (label + ", " if label else "") + (f"Tower {u['tower']}" if lang == "en" else f"ตึก {u['tower']}")
    if not label:
        return ""
    return f'<span data-floor-id="{e(u["id"])}" data-floor-tower="{e(u.get("tower", "") if tower else "")}" data-lang="{lang}">{e(label)}</span>'


TYPE_BY_BEDS = {0: "Studio", 1: "1 bedroom", 2: "2 bedrooms", 3: "3 bedrooms"}


def typical_rent(u):
    """The building's typical asking rent for this unit's bedroom count, if known."""
    c = CONDO_BY_SLUG[u["condo"]]
    want = TYPE_BY_BEDS.get(u.get("bedrooms"))
    for r in c.get("rents", []):
        if r["type"] == want:
            return r["typical"]
    return None


def is_fair_price(u):
    t = typical_rent(u)
    return bool(not is_sale(u) and u.get("rent_thb") and t and u["rent_thb"] <= t)


FAIR_NOTE = {
    "en": "“Fair price” means the rent is at or below the building's typical asking rent for that unit type.",
    "th": "“ราคาดี” หมายถึงค่าเช่าเท่ากับหรือต่ำกว่าค่าเช่าทั่วไปของห้องประเภทเดียวกันในโครงการ",
}


def unit_cards(units, lang="en"):
    if not units:
        return ""
    cards = []
    for u in units:
        c = CONDO_BY_SLUG[u["condo"]]
        done = u.get("status") in ("rented", "sold")
        badge = ""
        if done:
            badge = f'<span class="badge badge-muted">{"Sold" if is_sale(u) else "Rented"}</span>'
        elif is_fair_price(u):
            badge = f'<span class="badge">{"Fair price" if lang == "en" else "ราคาดี"}</span>'
        elif is_sale(u):
            badge = f'<span class="badge badge-sale">{"For sale" if lang == "en" else "ขาย"}</span>'
        checked = "" if is_sale(u) else f'<span class="chip">✓ {"Checked in person" if lang == "en" else "ตรวจห้องแล้ว"}</span>'
        img = (f'<img src="{e(u["photos"][0])}" alt="" loading="lazy" width="600" height="400">' if u.get("photos")
               else '<div class="unit-card-nophoto">Photos coming soon</div>')
        meta = " · ".join(x for x in [e(c['name']), floor_text(u, lang)] if x)
        cards.append(f"""<li class="unit-card" data-beds="{u.get('bedrooms', '')}" data-rent="{u.get('rent_thb') or ''}">
  <a href="{unit_url(u)}">
    <div class="unit-card-media">{img}{checked}</div>
    <div class="unit-card-body">
      <div class="unit-card-top"><div class="unit-price">{unit_price(u, lang)}</div>{badge}</div>
      <h3>{e(unit_title(u))}{' · ' + e(u['furnished']) if u.get('furnished') else ''}</h3>
      <p class="muted small">{meta}</p>
      <p class="station-line"><span class="bts">BTS</span>{e(c['station'])}</p>
    </div>
  </a>
</li>""")
    return '<ul class="unit-grid">' + "".join(cards) + "</ul>"


def page_unit(u):
    c = CONDO_BY_SLUG[u["condo"]]
    title = unit_title(u)
    photos = u.get("photos") or []
    if not photos:
        gallery_html = '<div class="notice">Photos of this unit are coming soon. Ask us on LINE for current photos or a video call.</div>'
    gallery = "" if not photos else (f'<a class="g-lead" href="{e(photos[0])}"><img src="{e(photos[0])}" alt="Photo 1 of {len(photos)}" width="1200" height="800"></a>'
               + "".join(f'<a href="{e(ph)}"><img src="{e(ph)}" alt="Photo {i} of {len(photos)}" loading="lazy" width="600" height="400"></a>'
                         for i, ph in enumerate(photos[1:5], 2)))
    more = (f'<p class="small muted">{len(photos) - 5} more photo{"s" if len(photos) - 5 > 1 else ""} — <a href="{e(photos[5])}">view</a> or ask us on LINE.</p>'
            if len(photos) > 5 else "")
    if photos:
        gallery_html = f'<div class="gallery">{gallery}</div>'

    sale = is_sale(u)
    spec = [("Price" if sale else "Rent", unit_price_text(u)),
            ("Bedrooms", "Studio" if u["bedrooms"] == 0 else str(u["bedrooms"])),
            ("Bathrooms", str(u["bathrooms"])),
            ("Size", f"{u['size_sqm']:g} sq m"),
            ("Floor", floor_text(u, tower=True)),
            ("Facing", u.get("facing", "")),
            ("Furnishing", u.get("furnished", "")),
            ("Available from", u.get("available_from", ""))]
    spec_html = "".join(f"<div><dt>{e(k)}</dt><dd>{v if k == 'Floor' else e(v)}</dd></div>" for k, v in spec if v)
    terms = [f"Deposit: {u['deposit_months']} months' rent" if u.get("deposit_months") else "",
             f"Paid in advance: {u['advance_months']} month's rent" if u.get("advance_months") else "",
             f"Minimum lease: {u['min_lease_months']} months" if u.get("min_lease_months") else "",
             {True: "Pets allowed", False: "No pets"}.get(u.get("pets"), "")]
    terms_html = "".join(f"<li>{e(t)}</li>" for t in terms if t)

    def tick_list(items):
        return '<ul class="ticks">' + "".join(f"<li>{e(x)}</li>" for x in items) + "</ul>" if items else ""

    furn = (f"<h2>Furniture and appliances</h2><div class=\"two-col\">{tick_list(u.get('furniture', []))}{tick_list(u.get('appliances', []))}</div>"
            if u.get("furniture") or u.get("appliances") else "")
    inc = tick_list(u.get("included", []))
    exc = tick_list(u.get("not_included", []))
    bills = (f"<h3>Included in the rent</h3>{inc}" if inc else "") + (f"<h3>Paid separately</h3>{exc}" if exc else "")
    desc_th = (f'<p lang="th">{e(u["description_th"])}</p>' if u.get("description_th") else "")
    ask = line_ask_url(f"Hi, I'm interested in unit {u['id']} at {c['name']} ({title}, {unit_price_text(u)}"
                       f"{', for sale' if sale else ''}). Is it still available?")
    ask_btn = (f'<a class="btn btn-line" href="{e(ask)}">Ask about this unit on LINE</a>' if ask else contact_links())
    status = ""
    if u.get("status") in ("rented", "sold"):
        status = (f'<div class="notice"><strong>This unit has been {"sold" if sale else "rented"}.</strong> '
                  'Ask us about similar units in the building.</div>')
    sample = ('<div class="notice"><strong>Sample listing.</strong> This page previews the layout; it is not a real unit.</div>'
              if u.get("draft") else "")
    body = f"""
<div class="wrap">
  <nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a> / <a href="{'/sale/' if sale else '/rent/'}">{'For sale' if sale else 'For rent'}</a> / <a href="/condos/{c['slug']}.html">{e(c['name'])}</a> / {e(u['id'])}</nav>
  {sample}
  {gallery_html}
  {more}
  <div class="unit-layout">
    <div>
      <div class="detail-head" style="padding-bottom:0">
        <p class="muted" style="margin:0"><a href="/condos/{c['slug']}.html">{e(c['name'])}</a> · <span class="station-tag">BTS {e(c['station'])}</span> · {e(c['walk'])}</p>
        <h1>{e(title)}{' for sale' if sale else ''}</h1>
      </div>
      {status}
      <dl class="facts">{spec_html}</dl>
      <div class="prose">
        <h2>About this unit</h2>
        <p>{e(u['description_en'])}</p>
        {desc_th}
        {furn}
        {bills}
        <h2>The building</h2>
        <p>{e(c['summary'])} <a href="/condos/{c['slug']}.html">Facilities and nearby places</a></p>
      </div>
    </div>
    <aside>
      <div class="panel price-panel">
        <div class="unit-price">{unit_price(u)}</div>
        {'<p class="small muted" style="margin:4px 0 0">Owner\'s asking price.</p>' if sale and u.get("price_thb") else ''}
        <ul class="plain small">{terms_html}</ul>
        {ask_btn}
        <p class="small muted" style="margin:12px 0 0">Unit ref {e(u['id'])}. We confirm availability before every viewing.</p>
      </div>
    </aside>
  </div>
</div>
<div class="section"></div>
"""
    word = "for sale" if sale else "for rent"
    bits = [unit_price_text(u), f"floors {u['floor_band']}" if u.get("floor_band") else "", u.get("furnished", "").lower()]
    desc = (f"{title} {word} at {c['name']}, Bang Na — " + ", ".join(b for b in bits if b)
            + f". Near BTS {c['station']}.")
    return layout(unit_url(u), f"{title} {word} at {c['name']}", desc, body,
                  nav_path="/sale/" if sale else "/rent/", noindex=bool(u.get("draft")))


RENT_FILTER = """<form class="filter-bar" id="rent-filter" action="/rent/" method="get">
  <label for="f-beds">Bedrooms</label>
  <select id="f-beds" name="beds"><option value="">Any bedrooms</option><option value="1">1 bedroom</option><option value="2">2 bedrooms</option><option value="3">3 bedrooms</option></select>
  <label for="f-max">Budget</label>
  <select id="f-max" name="max"><option value="">Any budget</option><option value="20000">Up to ฿20,000</option><option value="30000">Up to ฿30,000</option><option value="40000">Up to ฿40,000</option></select>
  <span class="filter-count" id="filter-count" aria-live="polite"></span>
</form>"""

# Filters the cards on /rent/ by bedrooms and maximum rent, from the selects or the
# query string the home page search sends (?beds=1&max=30000). Units without a listed
# rent stay visible under a budget filter, since their rent is on request.
RENT_FILTER_JS = """(function () {
  var form = document.getElementById('rent-filter');
  if (!form) return;
  var beds = form.elements.beds, max = form.elements.max;
  var cards = document.querySelectorAll('.unit-grid .unit-card');
  var count = document.getElementById('filter-count'), empty = document.getElementById('filter-empty');
  var q = new URLSearchParams(location.search);
  if (q.get('beds')) beds.value = q.get('beds');
  if (q.get('max')) max.value = q.get('max');
  function apply() {
    var b = beds.value, m = parseInt(max.value, 10), shown = 0;
    cards.forEach(function (c) {
      var rent = parseInt(c.getAttribute('data-rent'), 10);
      var ok = (!b || c.getAttribute('data-beds') === b) && (!m || isNaN(rent) || rent <= m);
      c.hidden = !ok; if (ok) shown++;
    });
    count.textContent = shown + (shown === 1 ? ' unit' : ' units');
    empty.hidden = shown !== 0;
    var p = new URLSearchParams();
    if (b) p.set('beds', b); if (m) p.set('max', m);
    var url = location.pathname + (p.toString() ? '?' + p : '');
    try { history.replaceState(null, '', url); } catch (e) {}
  }
  form.addEventListener('change', apply);
  form.addEventListener('submit', function (ev) { ev.preventDefault(); apply(); });
  apply();
})();"""


def page_rent_index():
    if RENT_UNITS:
        inner = RENT_FILTER + unit_cards(RENT_UNITS) + f"""
<div class="filter-empty" id="filter-empty" hidden><p>No units match these filters right now.</p>
  <p class="muted">Tell us your budget and move-in date on LINE and we'll check all four buildings for you.</p>{contact_links()}</div>
<p class="small muted" style="margin-top:12px">{e(FAIR_NOTE['en'])}</p>
<script>{RENT_FILTER_JS}</script>"""
    else:
        inner = ('<p class="muted">New units are being added. Tell us your budget and move-in date and we\'ll send you what\'s available.</p>'
                 + contact_links())
    body = f"""
<div class="wrap">
  <div class="detail-head">
    <h1>Condos for rent in Bang Na</h1>
    <p class="prose muted">Units we have checked in person at The Coast Bangkok, Ideo O2, Ideo Mobi Eastgate and Ideo Mobi Eastpoint, all at BTS Bang Na.</p>
  </div>
  {inner}
</div>
<div class="section"></div>
"""
    return layout("/rent/", "Condo units for rent in Bang Na", "Condo units for rent in Bang Na near the BTS, with photos, rent and what's included.", body)


def page_sale_index():
    if SALE_UNITS:
        inner = unit_cards(SALE_UNITS)
    else:
        inner = ('<p class="muted">No units for sale right now. Tell us what you are looking for and we\'ll let you know when one comes up.</p>'
                 + contact_links())
    body = f"""
<div class="wrap">
  <div class="detail-head">
    <h1>Condos for sale in Bang Na</h1>
    <p class="prose muted">Units offered by their owners at The Coast Bangkok, Ideo O2, Ideo Mobi Eastgate and Ideo Mobi Eastpoint, all at BTS Bang Na. Prices are the owners' asking prices.</p>
  </div>
  {inner}
</div>
<div class="section"></div>
"""
    return layout("/sale/", "Condo units for sale in Bang Na", "Condo units for sale in Bang Na near the BTS, with photos, asking price and unit details.", body)


ADMIN_PRIVATE = ROOT / "data/private/units-private.json"
ADMIN_DATA = ROOT / "assets/admin-data.json"


ADMIN_PUBLIC = ROOT / "assets/admin-units.json"


def write_admin_public():
    """Non-secret unit fields for the admin table, rebuilt on every build.

    The admin view overlays these on the encrypted rows, so price, size and
    bedroom changes show up without the passphrase. Floors, owners, room
    numbers and notes stay in the encrypted file only."""
    rows = [{"id": u["id"], "url": unit_url(u) if not u.get("pending") else "", "deal": u.get("deal", "rent"),
             "price": unit_price_text(u) if not u.get("pending") else "", "beds": u.get("bedrooms"),
             "size": u.get("size_sqm"), "tower": u.get("tower", ""), "status": u.get("status", "")}
            for u in json.loads(_units_file.read_text(encoding="utf-8"))]
    ADMIN_PUBLIC.write_text(json.dumps(rows, ensure_ascii=False) + "\n", encoding="utf-8")


def encrypt_admin_data():
    """Encrypt exact floors and owner notes for the admin view.

    Needs data/private/units-private.json (never committed) and the passphrase in
    the TTB_ADMIN_PASSPHRASE environment variable. Without them the existing
    encrypted file is left as it is.
    """
    import base64, os
    pw = os.environ.get("TTB_ADMIN_PASSPHRASE", "")
    if not (pw and ADMIN_PRIVATE.exists()):
        if not ADMIN_DATA.exists():
            print("NOTE: no admin data built (set TTB_ADMIN_PASSPHRASE and add data/private/units-private.json).")
        return
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes
    private = json.loads(ADMIN_PRIVATE.read_text(encoding="utf-8"))
    rows = []
    for u in json.loads(_units_file.read_text(encoding="utf-8")):
        p = private.get(u["id"], {})
        rows.append({"id": u["id"], "url": unit_url(u) if not u.get("pending") else "", "deal": u.get("deal", "rent"),
                     "price": unit_price_text(u), "beds": u.get("bedrooms"), "size": u.get("size_sqm"),
                     "tower": u.get("tower", ""), "floor": p.get("floor"), "owner": p.get("owner", ""),
                     "room": p.get("room", ""), "notes": p.get("notes", "")})
    iters = 600000
    salt, iv = os.urandom(16), os.urandom(12)
    key = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=iters).derive(pw.encode())
    ct = AESGCM(key).encrypt(iv, json.dumps(rows, ensure_ascii=False).encode(), None)
    b64 = lambda b: base64.b64encode(b).decode()
    ADMIN_DATA.write_text(json.dumps({"v": 1, "iter": iters, "salt": b64(salt), "iv": b64(iv), "data": b64(ct)}) + "\n")
    print(f"Encrypted admin data for {len(rows)} units.")


def page_admin():
    body = """
<div class="wrap">
  <div class="detail-head">
    <h1>Admin</h1>
    <p class="prose muted">Sign in to see exact floors, owners and room numbers. Signed in, the listing pages also show exact floors on this device.</p>
  </div>
  <form id="admin-login" class="panel" style="max-width:420px">
    <label for="admin-pass"><strong>Passphrase</strong></label>
    <input id="admin-pass" type="password" autocomplete="current-password" required style="display:block;width:100%;margin:8px 0 12px;padding:10px;font:inherit">
    <button class="btn btn-primary" type="submit">Sign in</button>
    <p id="admin-msg" class="small muted" style="margin:10px 0 0"></p>
  </form>
  <div id="admin-table"></div>
</div>
<div class="section"></div>
"""
    return layout("/admin/", "Admin", "Admin", body, noindex=True)


def redirect_page(to):
    url = SITE["base_url"] + to
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Moved</title>'
            f'<meta name="robots" content="noindex"><link rel="canonical" href="{e(url)}">'
            f'<meta http-equiv="refresh" content="0; url={e(to)}"></head>'
            f'<body><p>This page has moved to <a href="{e(to)}">{e(url)}</a>.</p></body></html>\n')


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
        ("th/index.html", "/th/", page_home_th()),
        ("condos/index.html", "/condos/", page_condos_index()),
    ]
    for c in CONDOS:
        pages.append((f"condos/{c['slug']}.html", f"/condos/{c['slug']}.html", page_condo(c)))
    pages.append(("rent/index.html", "/rent/", page_rent_index()))
    pages.append(("sale/index.html", "/sale/", page_sale_index()))
    pages.append(("admin/index.html", "/admin/", page_admin()))
    for u in UNITS:
        pages.append((unit_url(u).lstrip("/"), unit_url(u), page_unit(u)))
    # Old addresses of units that moved (e.g. a rental now listed for sale) keep working.
    for u in UNITS:
        for old in u.get("redirect_from", []):
            write(old.lstrip("/"), redirect_page(unit_url(u)))
    for name, path, title, desc in [
        ("bang-na.html", "/bang-na.html", "Living around BTS Bang Na",
         "What it's like to live in Bang Na, Bangkok: BTS stations, international schools, shopping, hospitals and getting to the airport."),
        ("renting-guide.html", "/renting-guide.html", "Renting a condo in Thailand as a foreigner",
         "Deposits, leases, TM30 reporting, utilities and what to check before you sign a condo lease in Thailand."),
        ("list-your-condo.html", "/list-your-condo.html", "List your condo at BTS Bang Na",
         "Rent out your unit at The Coast Bangkok, Ideo O2, Ideo Mobi Eastgate or Ideo Mobi Eastpoint. Free listing; one month's rent only when we find your tenant."),
        ("th/list-your-condo.html", "/th/list-your-condo.html", "ฝากเช่าคอนโด The Coast, Ideo O2, Ideo Mobi Eastgate, Ideo Mobi Eastpoint",
         "ฝากเช่าคอนโดใกล้ BTS บางนา ลงประกาศฟรี จ่ายค่าบริการ 1 เดือนเฉพาะเมื่อได้ผู้เช่าสัญญา 1 ปีผ่านเรา หาผู้เช่าได้ทั้งคนไทยและชาวต่างชาติ"),
        ("contact.html", "/contact.html", "Contact",
         "Contact The Thai Base about condos for rent at BTS Bang Na."),
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
    write_admin_public()
    encrypt_admin_data()

    drafts = {unit_url(u) for u in UNITS if u.get("draft")}
    urls = [p for _, p, _ in pages if p not in ("/404.html", "/admin/") and p not in drafts]
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
