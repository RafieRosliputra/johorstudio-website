"""Shared header, footer and contact details for every page.
Used by tools/build.py (main pages) and tools/projects.py (project posts).
Change contact details here once and rebuild.
"""
import html

WA = "https://wa.me/60127983745?text=Hi%20Rafi"   # WhatsApp buttons open with "Hi Rafi"
PHONE = "012-798 3745"
EMAIL = "johorstudio@gmail.com"
ADDRESS = "3038-A, Jln Merbau Satu, Bandar Putra, 81000 Kulai, Johor"
COMPANY = "PROMEDIA CREATIVE SOLUTIONS (JR0113470-V)"
MAPS = "https://maps.app.goo.gl/e5CBbhgkZm5Z6fnW8"
IG = "https://instagram.com/johorstudio"
TT = "https://www.tiktok.com/@johorstudio"
YT = "https://www.youtube.com/@rafierosliputra"
SITE = "https://johorstudio.com"
RAYA_URL = "https://bookings.johorstudio.cc/public"   # used only on raya.html

WA_ICON = '<svg viewBox="0 0 24 24" aria-hidden="true" fill="currentColor"><path d="M12 2a10 10 0 0 0-8.6 15.1L2 22l5-1.3A10 10 0 1 0 12 2Zm0 18.2a8.2 8.2 0 0 1-4.2-1.2l-.3-.2-3 .8.8-2.9-.2-.3A8.2 8.2 0 1 1 12 20.2Zm4.5-6.1c-.2-.1-1.5-.7-1.7-.8s-.4-.1-.6.1-.6.8-.8 1-.3.2-.5.1a6.7 6.7 0 0 1-3.3-2.9c-.3-.4.3-.4.7-1.3.1-.2 0-.3 0-.4l-.8-1.8c-.2-.5-.4-.4-.6-.4h-.5a1 1 0 0 0-.7.3 3 3 0 0 0-.9 2.2 5.2 5.2 0 0 0 1.1 2.8 11.9 11.9 0 0 0 4.6 4c1.7.7 2.4.8 3.2.7a2.8 2.8 0 0 0 1.8-1.3 2.3 2.3 0 0 0 .2-1.3c-.1-.1-.3-.2-.5-.3Z"/></svg>'

NAV = [("index.html", "Home"), ("services.html", "Services"), ("portfolio.html", "Portfolio"),
       ("projects/", "Projects"), ("raya.html", "Raya"), ("qr.html", "QR Creator"), ("about.html", "About"), ("contact.html", "Contact")]

LEGAL = ("© PROMEDIA CREATIVE SOLUTIONS (JR0113470-V). All photos on this website are our property and are "
         "protected under the Copyright Act 1987. Copying, editing, reposting or using them without written "
         "permission is prohibited, and we will take legal action to claim damages.")

LIGHTBOX = ('<dialog class="lightbox" aria-label="Photo"><div class="lb-bar"><div class="lb-info"><p class="lb-cap"></p>'
            f'<p class="lb-legal">{LEGAL}</p></div>'
            '<span class="lb-res"></span><button class="close" type="button">Close</button></div>'
            '<div class="lb-stage"><img alt="" draggable="false"></div></dialog>')


def render(current, title, desc, body, root="", path=None, og_image=None, body_class=None, extra_head=""):
    """Return a full HTML page.
    current: the NAV entry to highlight, e.g. "index.html" or "projects/"
    root:    relative path back to the site root ("" for top-level pages, "../../" for projects/<slug>/)
    path:    canonical path from the site root (defaults to current)
    """
    e = html.escape
    nav = "\n".join(
        f'<a href="{root}{h}"{" aria-current=\"page\"" if h == current else ""}>{t}</a>' for h, t in NAV)
    path = current if path is None else path
    canonical = SITE + "/" + ("" if path == "index.html" else path)
    og = og_image or f"{SITE}/img/hero/hero-01.webp"
    cls = body_class or "page-" + current.strip("/").split(".")[0].split("/")[0]
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{canonical}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:image" content="{og}">
<meta property="og:type" content="website">
<link rel="icon" href="{root}img/favicon.png">
<link rel="icon" type="image/png" sizes="192x192" href="{root}img/icon-192.png">
<link rel="apple-touch-icon" href="{root}img/apple-touch-icon.png">
<link rel="manifest" href="{root}manifest.webmanifest">
<meta name="theme-color" content="#cdc6c0">
<script defer src="https://ana.johorstudio.com/script.js" data-website-id="829b91de-d787-43d1-b711-ee608fcf0d60"></script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,400..700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{root}css/style.css?v=20261019">
{extra_head}
</head>
<body class="{cls}" data-root="{root}">
<a class="skip" href="#main">Skip to content</a>
<div class="raya-bar"><div class="wrap"><span>Raya photoshoot season is open at our Bandar Putra studio.</span><a href="{root}raya.html">See Raya photoshoot</a></div></div>
<header class="site-header">
  <div class="wrap">
    <a class="brand" href="{root}index.html"><img class="logo-dark" src="{root}img/logo-dark.png" alt="JohorStudio.com" width="131" height="46"><img class="logo-light" src="{root}img/logo-light.png" alt="" width="131" height="46"></a>
    <button class="menu-toggle" aria-expanded="false" aria-controls="nav">Menu</button>
    <nav class="nav" id="nav" aria-label="Main">
{nav}
<a class="btn" href="{WA}">{WA_ICON}WhatsApp us</a>
    </nav>
  </div>
</header>
<main id="main">
{body}
</main>
<footer class="site-footer">
  <div class="wrap">
    <div class="footer-grid">
      <div>
        <img src="{root}img/logo-light.png" alt="JohorStudio.com" width="154" height="54">
        <p>Professional digital media provider since 2014. Photography, videography, multicamera production and livestreaming across Malaysia.</p>
      </div>
      <div>
        <h3>Contact</h3>
        <ul>
          <li><a href="{WA}">WhatsApp {PHONE}</a></li>
          <li><a href="tel:+60127983745">Call {PHONE}</a></li>
          <li><a href="mailto:{EMAIL}">{EMAIL}</a></li>
        </ul>
      </div>
      <div>
        <h3>Studio</h3>
        <p><a href="{MAPS}">{ADDRESS}</a><br>By appointment only</p>
      </div>
      <div>
        <h3>Follow</h3>
        <ul>
          <li><a href="{IG}">Instagram</a></li>
          <li><a href="{TT}">TikTok</a></li>
          <li><a href="{YT}">YouTube</a></li>
        </ul>
      </div>
    </div>
    <div class="legal">
      <span>© <span data-this-year>2026</span> JohorStudio.com, {COMPANY}</span>
      <span>Serving Kulai, Johor Bahru, Pontian, Kota Tinggi, Kluang, Simpang Renggam and Batu Pahat</span>
    </div>
  </div>
</footer>
{LIGHTBOX}
<a class="wa-float" href="{WA}" aria-label="WhatsApp JohorStudio.com">{WA_ICON}<span>WhatsApp</span></a>
<script src="{root}js/meta-pixel.js"></script>
<script src="{root}js/analytics.js" defer></script>
<noscript><img height="1" width="1" style="display:none" src="https://www.facebook.com/tr?id=1135640695668913&amp;ev=PageView&amp;noscript=1"/></noscript>
<script src="{root}js/main.js" defer></script>
</body>
</html>
"""
