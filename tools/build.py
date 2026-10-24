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
    ("/", "Home"),
    ("/condos/", "Condos"),
    ("/bang-na.html", "Living in Bang Na"),
    ("/renting-guide.html", "Renting guide"),
    ("/list-your-condo.html", "For owners"),
    ("/contact.html", "Contact"),
    ("/th/", "ภาษาไทย"),
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


def page_home():
    units_block = ""
    if RENT_UNITS:
        units_block = f"""
<section class="section">
  <div class="wrap">
    <div class="section-head"><h2>Units for rent now</h2><a href="/rent/">All units for rent</a></div>
    {unit_cards(RENT_UNITS[:6])}
  </div>
</section>"""
    if SALE_UNITS:
        units_block += f"""
<section class="section">
  <div class="wrap">
    <div class="section-head"><h2>Units for sale</h2><a href="/sale/">All units for sale</a></div>
    {unit_cards(SALE_UNITS[:6])}
  </div>
</section>"""
    body = f"""
<section class="hero">
  <div class="wrap">
    <p class="lang-switch hero-lang"><a href="/th/" hreflang="th" lang="th">ดูหน้านี้เป็นภาษาไทย</a></p>
    <h1>Four condos at BTS Bang Na. One contact for all of them.</h1>
    <p>We know The Coast Bangkok, Ideo O2, Ideo Mobi Eastgate and Ideo Mobi Eastpoint unit by unit. Tell us your budget and move-in date and we'll send what's free in all four buildings, then show you round in Thai or English.</p>
    <div class="hero-actions">
      <a class="btn btn-primary" href="/condos/">Compare the four condos</a>
      <a class="btn btn-ghost" href="/contact.html">Tell us what you need</a>
    </div>
  </div>
  <div class="line-strip">
    <div class="wrap">
      <h2>All four are around BTS Bang Na</h2>
      <p class="hint">On the BTS Sukhumvit line, about 20–25 minutes to Asok without changing trains. Choose a building to see its details.</p>
      {line_strip()}
    </div>
  </div>
</section>
{units_block}
<section class="section">
  <div class="wrap">
    <div class="section-head"><h2>Which condo fits your budget</h2><a href="/condos/">Building details</a></div>
    {rent_compare()}
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="section-head"><h2>The four condos</h2></div>
    {condo_rows(CONDOS)}
  </div>
</section>

<section class="section">
  <div class="wrap split">
    <div class="prose">
      <h2>Why rent through us</h2>
      <ul class="ticks">
        <li><strong>One search, four buildings.</strong> Instead of messaging a different agent for each listing, you get one shortlist across every building at BTS Bang Na.</li>
        <li><strong>We only work here.</strong> We know which towers face the morning sun, which floors hear the expressway and what each building's juristic office allows.</li>
        <li><strong>No fee for renters.</strong> The owner pays our fee.</li>
        <li><strong>Thai or English.</strong> Viewings, the lease and move-in, in the language you prefer.</li>
      </ul>
    </div>
    <div class="panel">
      <h3>How renting with us works</h3>
      <ol class="steps">
        <li>Tell us your budget, bedrooms, move-in date and where you work or study.</li>
        <li>We send a shortlist of available units across the four buildings, with photos.</li>
        <li>We arrange viewings, in person or by video call.</li>
        <li>We go through the lease with you before you sign and record the unit's condition at move-in.</li>
      </ol>
      <a href="/renting-guide.html">What to expect when renting in Thailand</a>
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap split">
    <div class="panel panel-dark">
      <h2>Own a unit in one of these buildings?</h2>
      <p>Listing is free. You pay one month's rent only when we find your tenant on a one-year lease.</p>
      <a class="btn btn-primary" href="/th/list-your-condo.html">ฝากเช่ากับเรา</a>
      <a class="btn btn-ghost" href="/list-your-condo.html">List your condo</a>
    </div>
    <div>
      <h2>Talk to us</h2>
      <p>Send your budget, bedrooms and move-in date. We reply in Thai or English.</p>
      {contact_links()}
    </div>
  </div>
</section>
"""
    return layout("/", "", f"Condos for rent at BTS Bang Na: {CONDO_NAMES}. Compare typical rents, see available units and arrange viewings in Thai or English.",
                  body, alternates=HOME_ALTERNATES)


def page_home_th():
    units_block = ""
    if RENT_UNITS:
        units_block = f"""
<section class="section">
  <div class="wrap">
    <div class="section-head"><h2>ห้องว่างให้เช่าตอนนี้</h2><a href="/rent/">ดูห้องเช่าทั้งหมด</a></div>
    {unit_cards(RENT_UNITS[:6], "th")}
  </div>
</section>"""
    if SALE_UNITS:
        units_block += f"""
<section class="section">
  <div class="wrap">
    <div class="section-head"><h2>ห้องขาย</h2><a href="/sale/">ดูห้องขายทั้งหมด</a></div>
    {unit_cards(SALE_UNITS[:6], "th")}
  </div>
</section>"""
    body = f"""
<section class="hero">
  <div class="wrap">
    <p class="lang-switch hero-lang"><a href="/" hreflang="en" lang="en">Read in English</a></p>
    <h1>คอนโดให้เช่า 4 โครงการ ใกล้ BTS บางนา ติดต่อที่เดียวครบ</h1>
    <p>เรารู้จัก The Coast Bangkok, Ideo O2, Ideo Mobi Eastgate และ Ideo Mobi Eastpoint แบบห้องต่อห้อง บอกงบและวันที่อยากย้ายเข้า เราส่งห้องว่างจากทั้ง 4 โครงการให้ แล้วพาชมห้องให้เลย</p>
    <div class="hero-actions">
      <a class="btn btn-primary" href="#compare">เทียบค่าเช่า 4 โครงการ</a>
      {contact_links("btn btn-ghost", "th").replace('<div class="contact-links">', '').replace('</div>', '')}
    </div>
  </div>
  <div class="line-strip">
    <div class="wrap">
      <h2>ทั้ง 4 โครงการอยู่รอบ BTS บางนา</h2>
      <p class="hint">BTS สายสุขุมวิท ไปอโศกประมาณ 20–25 นาทีโดยไม่ต้องเปลี่ยนขบวน กดชื่อโครงการเพื่อดูรายละเอียด</p>
      {line_strip("th")}
    </div>
  </div>
</section>
{units_block}
<section class="section" id="compare">
  <div class="wrap">
    <div class="section-head"><h2>โครงการไหนเข้ากับงบของคุณ</h2></div>
    {rent_compare("th")}
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="section-head"><h2>คอนโดทั้ง 4 โครงการ</h2></div>
    {condo_rows(CONDOS, "th")}
  </div>
</section>

<section class="section">
  <div class="wrap split">
    <div class="prose">
      <h2>ทำไมต้องเช่าผ่านเรา</h2>
      <ul class="ticks">
        <li><strong>หาครั้งเดียว ครบ 4 โครงการ</strong> ไม่ต้องทักหลายเอเจนต์ทีละประกาศ เราส่งห้องว่างจากทุกโครงการรอบ BTS บางนาให้ในครั้งเดียว</li>
        <li><strong>เราทำเฉพาะย่านนี้</strong> รู้ว่าตึกไหนแดดเช้า ชั้นไหนได้ยินเสียงทางด่วน และนิติฯ แต่ละที่มีกฎอะไร</li>
        <li><strong>ผู้เช่าไม่เสียค่าบริการ</strong> เจ้าของห้องเป็นผู้จ่าย</li>
        <li><strong>คุยได้ทั้งไทยและอังกฤษ</strong> ตั้งแต่ดูห้อง ทำสัญญา จนถึงวันย้ายเข้า</li>
      </ul>
    </div>
    <div class="panel">
      <h3>ขั้นตอนเช่ากับเรา</h3>
      <ol class="steps">
        <li>บอกงบ จำนวนห้องนอน วันที่อยากย้ายเข้า และที่ทำงานหรือที่เรียน</li>
        <li>เราส่งรายการห้องว่างจากทั้ง 4 โครงการ พร้อมรูป</li>
        <li>นัดดูห้องจริง หรือดูผ่านวิดีโอคอล</li>
        <li>อธิบายสัญญาก่อนเซ็น และบันทึกสภาพห้องวันย้ายเข้า</li>
      </ol>
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap split">
    <div class="panel panel-dark">
      <h2>มีห้องในโครงการเหล่านี้?</h2>
      <p>ฝากเช่าฟรี ไม่มีวันหมดอายุ จ่ายค่าบริการ 1 เดือน เฉพาะเมื่อได้ผู้เช่าสัญญา 1 ปีผ่านเรา</p>
      <a class="btn btn-primary" href="/th/list-your-condo.html">ฝากเช่ากับเรา</a>
    </div>
    <div>
      <h2>ติดต่อเรา</h2>
      <p>บอกงบ จำนวนห้องนอน และวันที่อยากย้ายเข้า เราตอบกลับทาง LINE</p>
      {contact_links(lang="th")}
    </div>
  </div>
</section>
"""
    return layout("/th/", "คอนโดให้เช่า ใกล้ BTS บางนา",
                  "คอนโดให้เช่าใกล้ BTS บางนา 4 โครงการ: The Coast Bangkok, Ideo O2, Ideo Mobi Eastgate, Ideo Mobi Eastpoint เทียบค่าเช่า ดูห้องว่าง นัดชมห้องได้เลย",
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


def floor_text(u, lang="en"):
    if not u.get("floor"):
        return ""
    return f"{'Floor' if lang == 'en' else 'ชั้น'} {u['floor']}"


def unit_cards(units, lang="en"):
    if not units:
        return ""
    cards = []
    for u in units:
        c = CONDO_BY_SLUG[u["condo"]]
        done = u.get("status") in ("rented", "sold")
        badge = f'<span class="badge badge-muted">{"Sold" if is_sale(u) else "Rented"}</span>' if done else ""
        meta = " · ".join(x for x in [e(c['name']), floor_text(u, lang), f"BTS {e(c['station'])}"] if x)
        cards.append(f"""<li class="unit-card">
  <a href="{unit_url(u)}">
    {f'<img src="{e(u["photos"][0])}" alt="" loading="lazy" width="600" height="400">' if u.get("photos") else '<div class="unit-card-nophoto">Photos coming soon</div>'}
    <div class="unit-card-body">
      <div class="unit-price">{unit_price(u, lang)}{badge}</div>
      <h3>{e(unit_title(u))}</h3>
      <p class="muted small">{meta}</p>
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
    floor = (str(u["floor"]) if u.get("floor") else "") + (f", Tower {u['tower']}" if u.get("tower") else "")
    spec = [("Price" if sale else "Rent", unit_price_text(u)),
            ("Bedrooms", "Studio" if u["bedrooms"] == 0 else str(u["bedrooms"])),
            ("Bathrooms", str(u["bathrooms"])),
            ("Size", f"{u['size_sqm']:g} sq m"),
            ("Floor", floor.lstrip(", ")),
            ("Facing", u.get("facing", "")),
            ("Furnishing", u.get("furnished", "")),
            ("Available from", u.get("available_from", ""))]
    spec_html = "".join(f"<div><dt>{e(k)}</dt><dd>{e(v)}</dd></div>" for k, v in spec if v)
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
    ask_btn = (f'<a class="btn btn-primary" href="{e(ask)}">Ask about this unit on LINE</a>' if ask else contact_links())
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
    bits = [unit_price_text(u), floor_text(u).lower(), u.get("furnished", "").lower()]
    desc = (f"{title} {word} at {c['name']}, Bang Na — " + ", ".join(b for b in bits if b)
            + f". Near BTS {c['station']}.")
    return layout(unit_url(u), f"{title} {word} at {c['name']}", desc, body,
                  nav_path="/sale/" if sale else "/rent/", noindex=bool(u.get("draft")))


def page_rent_index():
    if RENT_UNITS:
        inner = unit_cards(RENT_UNITS)
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

    drafts = {unit_url(u) for u in UNITS if u.get("draft")}
    urls = [p for _, p, _ in pages if p != "/404.html" and p not in drafts]
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
