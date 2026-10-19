"""Builds the HTML pages in site/ from the content below.
Header and footer are shared, so contact details are changed in one place.
Run:  python3 tools/build.py   (optional — the built pages are already in site/)
"""
import pathlib, html, json, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from layout import (render, WA, PHONE, EMAIL, ADDRESS, COMPANY, MAPS, IG, TT, YT, SITE,
                    RAYA_URL, WA_ICON, LIGHTBOX)

ROOT = pathlib.Path(__file__).resolve().parent.parent / "site"


def page(file, title, desc, body, extra_head=""):
    (ROOT / file).write_text(render(file, title, desc, body, extra_head=extra_head), encoding="utf-8")


def img(name, alt, folder="gallery", sm=True, cls="", lazy=True):
    src = f"img/{folder}/{name}{'-sm' if sm else ''}.webp"
    return f'<img src="{src}" alt="{html.escape(alt)}"{" loading=\"lazy\"" if lazy else ""}{f" class=\"{cls}\"" if cls else ""}>'



PORTFOLIO = {i["file"]: i for i in json.load(open(ROOT / "data" / "portfolio.json"))["items"]}

def lb(name, cls=""):
    """Thumbnail button that opens the lightbox (full resolution when available)."""
    it = PORTFOLIO[name]
    full = f' data-full="img/gallery/{name}-full.webp" data-size="{it["size"]}"' if it.get("full") else ""
    return (f'<button type="button" class="lb-thumb {cls}" data-lightbox data-src="img/gallery/{name}.webp"{full} '
            f'data-caption="{html.escape(it["caption"])}"><img src="img/gallery/{name}-sm.webp" alt="{html.escape(it["caption"])}" loading="lazy"></button>')

def media(name, alt):
    """Clickable (lightbox) unless it is a behind-the-scenes shot."""
    return lb(name, "media") if name in PORTFOLIO else img(name, alt)


# ---------------- HOME ----------------
FEATURED = ['studio-fashion-06', 'photo-corporate-portrait-02', 'studio-fashion-04', 'photo-sports-motocross-01', 'studio-product-01', 'convo-graduation-stage-01', 'studio-fashion-12', 'photo-landscape-pier', 'studio-fashion-18', 'photo-event-award-ceremony']
HERO = [
 {
  "name": "hero-06",
  "caption": "Studio fashion photography",
  "pos": "45% 35%",
  "mpos": "55% 30%"
 },
 {
  "name": "hero-01",
  "caption": "Live camera on stage, Butterfly 22nd Convocation, Trove Hotel",
  "pos": "72% 40%",
  "mpos": "82% 40%"
 },
 {
  "name": "hero-03",
  "caption": "Live switching, ADTEC JTM 29th Convocation 2026",
  "pos": "40% 50%",
  "mpos": "55% 45%"
 },
 {
  "name": "hero-04",
  "caption": "Motorsport photography",
  "pos": "45% 50%",
  "mpos": "50% 35%"
 },
 {
  "name": "hero-05",
  "caption": "Our crew on the ballroom floor",
  "pos": "58% 45%",
  "mpos": "55% 40%"
 },
 {
  "name": "hero-02",
  "caption": "Fashion and lifestyle shoots",
  "pos": "55% 35%",
  "mpos": "50% 35%"
 },
 {
  "name": "hero-07",
  "caption": "Multicam coverage, ADTEC JTM 2026",
  "pos": "50% 55%",
  "mpos": "40% 55%"
 },
 {
  "name": "hero-08",
  "caption": "Award ceremonies and official portraits",
  "pos": "50% 8%",
  "mpos": "50% 30%"
 }
]
slides = "\n".join(
    f'''<figure class="slide{" is-active" if i == 0 else ""}" aria-roledescription="slide" aria-label="{i+1} of {len(HERO)}">
  <picture>
    <source media="(max-aspect-ratio: 4/5)" srcset="img/hero/{h['name']}-m.webp">
    <img src="img/hero/{h['name']}.webp" alt="{html.escape(h['caption'])}" style="--pos:{h['pos']};--mpos:{h['mpos']}"{' fetchpriority="high"' if i == 0 else ' loading="lazy"'} decoding="async">
  </picture>
</figure>''' for i, h in enumerate(HERO))
dots = "".join(f'<button type="button" class="dot-btn" aria-label="Show slide {i+1}"{" aria-current=\"true\"" if i == 0 else ""}></button>' for i in range(len(HERO)))

SERVICES = [
    ("multicam", "Multicamera production", "bts-multiview-switcher-01",
     "Two to three cameras switched live to the LED screen in the hall, with a full recording for you after."),
    ("livestream", "Livestreaming", "bts-outdoor-control-tent",
     "YouTube, Facebook Live, Zoom and hybrid events, plus live feeds of medical procedures to a lecture hall."),
    ("videography", "Videography", "bts-interview-setup",
     "Event highlights, interviews and corporate video. Same-day edit available for your closing session."),
    ("photography", "Event photography", "photo-event-symposium-speaker",
     "Conferences, dinners, award ceremonies and corporate portraits. Edited photos in one to three days."),
    ("convocation", "Convocation and school photos", "convo-graduation-stage-01",
     "On-stage scroll moments, a pop-up studio at the venue, and class and group photos for every level."),
    ("studio", "Studio photography", "studio-fashion-06",
     "Our Bandar Putra studio for family, Raya, portraits, products, fashion and convocation shoots."),
]
svc_rows = "\n".join(f"""<li class="service">
  {img(i, t)}
  <div><h3>{t}</h3><p>{d}</p></div>
  <a class="more" href="services.html#{k}">Details</a>
</li>""" for k, t, i, d in SERVICES)

CLIENTS = ["CONSAL XIX, Kuala Lumpur", "Hospital Sultanah Aminah", "Hospital Sultan Ismail", "Petronas",
           "Asia Aeronautical Training Academy (AATA)", "ADTEC JTM", "Butterfly Education Centre", "SMK Kulai Besar"]

REVIEWS = [
    ("the photos turned out very nice. i love it", None, "Sabrina Nur Aisha"),
    ("Very good photoshoot session", None, "Syahrul Azmeer Ismail"),
    ("Perkhidmatan yang terbaik!", "The best service!", "Abdulrahim Abdrahman"),
    ("Servis terbaik", "Best service", "Nurul Asyikin"),
    ("Nice picture, pro photographer", None, "Hesharm Ibrahim"),
]
rev = "\n".join(
    f'<blockquote><p>“{html.escape(q)}”</p>{f"<p class=\"tr\">{html.escape(t)}</p>" if t else ""}<cite>{html.escape(n)}, Google review</cite></blockquote>'
    for q, t, n in REVIEWS[:3])

BTS = [("bts-multiview-switcher-01", "Multiview switcher at an awards ceremony"),
       ("bts-butterfly-control-room-mixer", "Control room above the ballroom"),
       ("bts-adtec2026-viewfinder", "Stage camera viewfinder"),
       ("bts-virtual-studio-live", "Virtual studio with live Zoom guests"),
       ("bts-outdoor-camera-rain", "Shooting live in the rain"),
       ("bts-butterfly-gimbal-monitor", "Gimbal camera with field monitor"),
       ("bts-team-photo-adtec2026", "Our crew, ADTEC JTM 2026")]
bts = "\n".join(f"<figure>{img(n, c)}<figcaption>{c}</figcaption></figure>" for n, c in BTS)

page("index.html",
     "JohorStudio.com | Multicam, livestream, photo and video in Johor",
     "Johor-based media team since 2014: multicamera production, livestreaming, videography, event and studio photography. Serving Kulai, Johor Bahru and all of Malaysia.",
     f"""
<section class="hero-full" aria-roledescription="carousel" aria-label="Featured work">
  <div class="slides">
{slides}
  </div>
  <div class="hero-shade" aria-hidden="true"></div>
  <div class="hero-text">
    <div class="wrap">
      <h1>Your event, on every screen.</h1>
      <p class="lead">Professional digital media provider since 2014. We run the cameras, the switcher and the stream, hand in hand with you and your event organiser.</p>
      <div class="actions">
        <a class="btn btn-light" href="contact.html">Get a quotation</a>
        <a class="btn btn-ghost" href="portfolio.html">See our work</a>
        <a class="btn btn-ghost" data-raya hidden href="raya.html">Raya photoshoot</a>
      </div>
      <div class="hero-controls">
        <button type="button" class="hc-prev" aria-label="Previous slide">‹</button>
        <div class="dots">{dots}</div>
        <button type="button" class="hc-next" aria-label="Next slide">›</button>
        <p class="hero-caption" aria-live="polite"></p>
      </div>
    </div>
  </div>
  <a class="scroll-cue" href="#intro" aria-label="Scroll to content"><span></span></a>
</section>

<section class="section bg-white" id="intro">
  <div class="wrap">
    <dl class="facts">
      <div><dt>Since 2014</dt><dd>Twelve years covering events in Johor</dd></div>
      <div><dt>500 to 2,000 guests</dt><dd>Our usual event size</dd></div>
      <div><dt>Same-day edit</dt><dd>Highlights ready before your event ends</dd></div>
      <div><dt>Full recording</dt><dd>Every livestream handed over in full</dd></div>
    </dl>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="section-head"><h2>What we do</h2><a href="services.html">All services</a></div>
    <ul class="services">
{svc_rows}
    </ul>
  </div>
</section>

<section class="section bg-white">
  <div class="wrap">
    <div class="section-head"><h2>Photography</h2><a href="portfolio.html#studio">More photos</a></div>
    <p class="muted" style="margin-top:-20px">Tap any photo to view it at full resolution.</p>
    <div class="mosaic">
      {"".join(lb(n) for n in FEATURED)}
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="section-head"><h2>Recent projects</h2><a href="projects/">All projects</a></div>
    <div class="projects" data-recent-projects="5">
      <noscript><p><a href="projects/">See all our projects</a></p></noscript>
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="section-head"><h2>Behind the scenes</h2><a href="portfolio.html#multicam">More set-ups</a></div>
    <div class="strip">
{bts}
    </div>
  </div>
</section>

<section class="section bg-white">
  <div class="wrap">
    <div class="section-head"><h2>Trusted by</h2></div>
    <ul class="clients">{"".join(f"<li>{c}</li>" for c in CLIENTS)}</ul>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="section-head"><h2>What clients say</h2><a href="{MAPS}">Reviews on Google</a></div>
    <div class="reviews">
{rev}
    </div>
  </div>
</section>

<section class="cta-band">
  <div class="wrap">
    <h2>Tell us your date and venue.</h2>
    <div class="actions">
      <a class="btn" href="{WA}">{WA_ICON}WhatsApp us</a>
      <a class="btn btn-line" href="contact.html">Send event details</a>
    </div>
  </div>
</section>
""")

# ---------------- SERVICES ----------------
DETAIL = [
    ("multicam", "Multicamera production", ["bts-multiview-switcher-01", "bts-butterfly-two-operators-wide", "bts-adtec2026-camera-row"],
     "We cover your stage with two to three cameras and switch them live, so the hall sees close-ups on the LED screen while it happens.",
     ["Live switching to LED screens and projectors", "Camera operators on comms with our director", "Full programme recording handed to you after the event", "Site visit before large events"]),
    ("livestream", "Livestreaming", ["bts-outdoor-control-tent", "bts-virtual-studio-live", "bts-live-talkshow-screen"],
     "Streams to YouTube, Facebook Live and Zoom, including hybrid events where speakers join remotely, and live feeds of medical procedures to a lecture hall.",
     ["YouTube and Facebook Live", "Zoom and hybrid sessions with remote guests", "Green screen and virtual sets", "Live medical and procedure broadcasts", "Full recording included"]),
    ("videography", "Videography", ["bts-interview-setup", "bts-butterfly-shoulder-rig", "bts-butterfly-riser-camera"],
     "Event highlights, interviews and corporate video, shot and edited by the same team that runs your live production.",
     ["Same-day edit for closing ceremonies", "Interviews and testimonials", "Corporate and promotional video"]),
    ("photography", "Event and corporate photography", ["photo-event-award-ceremony-02", "photo-corporate-portrait-02", "photo-sports-motocross-01"],
     "Conferences, dinner functions, award ceremonies, sports and official portraits. Edited photos are delivered within one to three days through our private cloud.",
     ["Conferences and symposiums", "Dinner functions and award nights", "Official and corporate portraits", "Sports and motorsport"]),
    ("convocation", "Convocation and school photography", ["convo-graduation-stage-01", "school-class-photo-01", "school-class-photo-02"],
     "Scroll presentations on stage, a pop-up studio at the venue for families, and class and group photos for primary, secondary and tertiary institutions.",
     ["On-stage scroll moments", "Pop-up studio at your venue", "Class, prefect and club photos", "Prints in 4R, 8R and frames, or digital only"]),
    ("studio", "Studio photography", ["studio-fashion-12", "studio-product-01", "studio-fashion-15"],
     "Our studio in Bandar Putra, Kulai, is open by appointment for family and Raya portraits, corporate headshots, products, fashion and convocation shoots.",
     ["Family and Raya photoshoots", "Corporate headshots", "Product and fashion", "Convocation portraits"]),
]
svc = "\n".join(f"""<article class="svc-detail" id="{k}">
  <div class="svc-media">{"".join(media(i, t) for i in imgs)}</div>
  <div>
    <h2>{t}</h2>
    <p class="lead">{d}</p>
    <ul>{"".join(f"<li>{b}</li>" for b in bullets)}</ul>
    <p><a href="portfolio.html#{k}">See {t.lower()} work</a></p>
  </div>
</article>""" for k, t, imgs, d, bullets in DETAIL)

page("services.html",
     "Services | Multicam, livestream, photography in Johor | JohorStudio.com",
     "Multicamera production, livestreaming, videography, event, convocation and studio photography in Kulai, Johor Bahru, Pontian, Kota Tinggi, Kluang, Batu Pahat and across Malaysia.",
     f"""
<section class="page-head"><div class="wrap">
  <h1>Services</h1>
  <p class="lead">One team for cameras, switching, streaming and photos. Prices depend on your programme, so we quote every event individually.</p>
</div></section>
<div class="wrap">
{svc}
<article class="svc-detail" id="areas">
  <div>
    <h2>Where we work</h2>
    <p class="lead">Based in Bandar Putra, Kulai. We cover all of Johor and travel across Malaysia, with past work in Kuala Lumpur, Perak and Terengganu.</p>
  </div>
  <div>
    <p>Kulai, Johor Bahru, Pontian, Kota Tinggi, Kluang, Simpang Renggam, Batu Pahat, and the rest of Malaysia on request.</p>
    <p><a class="btn" href="contact.html">Get a quotation</a></p>
  </div>
</article>
</div>
""")

# ---------------- PORTFOLIO ----------------
FILTERS = [("all", "All"), ("multicam", "Multicam"), ("livestream", "Livestream"), ("videography", "Videography"),
           ("photography", "Photography"), ("convocation", "Convocation"), ("studio", "Studio")]
page("portfolio.html",
     "Portfolio | JohorStudio.com",
     "Photos and behind-the-scenes from our multicam, livestream, videography, convocation and studio work in Johor.",
     f"""
<section class="page-head"><div class="wrap">
  <h1>Portfolio</h1>
  <p class="lead">Real jobs, real set-ups. Choose a service to filter, and tap a photo to see it at full resolution.</p>
</div></section>
<section class="wrap" style="padding-bottom:72px">
  <div class="filters" role="group" aria-label="Filter by service">
    {"".join(f'<button type="button" data-filter="{k}" aria-pressed="{"true" if k == "all" else "false"}">{t}</button>' for k, t in FILTERS)}
  </div>
  <div class="gallery" data-portfolio></div>
</section>
<section class="section bg-white"><div class="wrap">
  <div class="section-head"><h2>Video</h2><a href="{YT}">Our YouTube channel</a></div>
  <p data-videos-empty class="muted">Watch our livestreams and event videos on <a href="{YT}">YouTube</a>.</p>
  <div class="videos"></div>
</div></section>
""")

# ---------------- PROJECTS ----------------
# Project posts are generated by tools/projects.py into site/projects/.
# projects.html only forwards old links there.
(ROOT / "projects.html").write_text("""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Projects | JohorStudio.com</title>
<meta http-equiv="refresh" content="0; url=projects/"><link rel="canonical" href="https://johorstudio.com/projects/"></head>
<body><p><a href="projects/">Projects</a></p></body></html>
""", encoding="utf-8")

# ---------------- RAYA ----------------
# Photos: site/img/raya/<file>-sm.webp, <file>.webp, <file>-full.webp, listed in site/data/raya-gallery.json
# The photos are drawn by js/main.js from data/raya-gallery.json (rated photos only), so changes need no rebuild.
raya_thumbs = '<div class="gallery" data-raya-gallery></div>'
page("raya.html",
     "Raya Photoshoot Studio in Kulai, Johor | JohorStudio.com",
     "Hari Raya family, couple and group photoshoots at the JohorStudio.com studio in Bandar Putra, Kulai. Book your Raya slot online.",
     f"""
<section class="page-head"><div class="wrap">
  <h1>Raya studio photoshoot</h1>
  <p class="lead">Family, couple and big group portraits in your Raya outfits, shot in our Bandar Putra studio with bright, even lighting and ready-made Raya sets.</p>
  <div class="actions" style="margin-top:20px"><a class="btn" href="{RAYA_URL}">Book a Raya slot</a><a class="btn btn-line" href="{WA}">Ask on WhatsApp</a></div>
</div></section>
<section class="section bg-white"><div class="wrap">
  <ol class="services">
    <li class="service" style="grid-template-columns:1fr"><div><h3>Sets for every group size</h3><p>Choose from our white classic set and our pastel panelled sets, with benches for seated family rows and plenty of floor for large families.</p></div></li>
    <li class="service" style="grid-template-columns:1fr"><div><h3>Formal and fun</h3><p>We start with the classic family line-up, then loosen up with candid, playful and couple shots so everyone gets a favourite.</p></div></li>
    <li class="service" style="grid-template-columns:1fr"><div><h3>Book online</h3><p>Pick a date and time slot on our <a href="{RAYA_URL}">online booking page</a>. Slots fill up quickly during Ramadan and the first weeks of Syawal.</p></div></li>
  </ol>
</div></section>
<section class="wrap" style="padding-top:56px;padding-bottom:72px">
  <div class="section-head"><h2>Recent Raya sessions</h2></div>
  <p class="muted">Real clients photographed in our studio. Tap a photo to view it at full resolution.</p>
  <div class="gallery">
{raya_thumbs}
  </div>
</section>
<section class="cta-band"><div class="wrap">
  <h2>Ready for your Raya photos?</h2>
  <div class="actions"><a class="btn" href="{RAYA_URL}">Book a Raya slot</a><a class="btn btn-line" href="contact.html">Contact us</a></div>
</div></section>
""")

# ---------------- QR CREATOR ----------------
# Runs in the browser only (js/qr.js). Nothing is uploaded to the server.
page("qr.html",
     "Free QR Code Creator with Logo | JohorStudio.com",
     "Make a QR code with your own logo in the middle, a title above and the link below. Download a high resolution PNG, free.",
     """
<section class="page-head"><div class="wrap">
  <h1>QR Creator</h1>
  <p class="lead">Turn any link into a QR code with your logo in the middle. Download a high resolution PNG for print or screen. Everything runs in your browser, nothing is uploaded.</p>
</div></section>
<section class="wrap" style="padding-bottom:72px">
  <div class="qr-app" data-qr>
    <div class="qr-preview"><canvas aria-label="QR code preview" role="img"></canvas></div>
    <div class="form">
      <label>Link<input id="qr-link" type="url" inputmode="url" spellcheck="false" placeholder="https://" value="https://johorstudio.com"></label>
      <label>Title<input id="qr-title" type="text" value="SOFTCOPY DOWNLOAD"></label>
      <div style="display:grid;gap:6px">
        <span style="font-weight:500;font-size:15px">Logo</span>
        <button class="qr-logo-pick" type="button">Choose a logo (PNG, JPG or SVG)</button>
        <input id="qr-logo" type="file" accept="image/*" hidden>
        <button class="qr-clear" type="button" data-qr-clear hidden>Remove logo</button>
      </div>
      <div class="qr-actions">
        <button class="btn btn-line" type="button" data-qr-update>Update QR</button>
        <button class="btn" type="button" data-qr-save>Save QR</button>
      </div>
      <div class="qr-log" aria-live="polite"></div>
    </div>
  </div>
    <p class="qr-legal">QR Creator is a free service provided by JohorStudio.com on an &ldquo;as is&rdquo; basis, without warranty of any kind. You are solely responsible for the links and content you encode and for how the QR codes you create are used. JohorStudio.com and PROMEDIA CREATIVE SOLUTIONS (JR0113470-V) accept no liability for any loss, damage or misuse arising from the use of this service. Free to use, have fun.</p>
</section>
""",
     extra_head='<script src="js/vendor/qrcode.min.js" defer></script>\n<script src="js/vendor/jsQR.min.js" defer></script>\n<script src="js/qr.js" defer></script>')

# ---------------- ABOUT ----------------
page("about.html",
     "About | JohorStudio.com",
     "JohorStudio.com has provided photography, videography, multicamera production and livestreaming in Johor since 2014.",
     f"""
<section class="page-head"><div class="wrap">
  <h1>About JohorStudio.com</h1>
  <p class="lead">A professional digital media provider since 2014, based in Bandar Putra, Kulai.</p>
</div></section>
<section class="section bg-white"><div class="wrap split">
  {img("bts-team-photo-adtec2026", "The JohorStudio.com crew at ADTEC JTM convocation", sm=False)}
  <div>
    <h2>Technical by nature</h2>
    <p>We started with a passion for cameras and grew into live production. Today we run multicamera shows, livestreams and hybrid events for government agencies, hospitals, universities and companies.</p>
    <p>Our core team is small and hands-on, and we bring in trusted crew for larger events. The person who plans your event is the person running the switcher on the day.</p>
    <p>We work closely with your organiser, from the site visit to the hand-over, and we deliver edited photos in one to three days and full recordings of every stream.</p>
  </div>
</div></section>
<section class="section"><div class="wrap">
  <div class="section-head"><h2>How a job runs</h2></div>
  <ol class="services">
    <li class="service" style="grid-template-columns:1fr"><div><h3>1. WhatsApp us your date and venue</h3><p>We reply with questions about your programme and screens.</p></div></li>
    <li class="service" style="grid-template-columns:1fr"><div><h3>2. Quotation and deposit</h3><p>A written quotation, then a 30 to 50 percent deposit to lock the date.</p></div></li>
    <li class="service" style="grid-template-columns:1fr"><div><h3>3. Site visit for large events</h3><p>We check power, internet, camera positions and the LED feed before the day.</p></div></li>
    <li class="service" style="grid-template-columns:1fr"><div><h3>4. Event day and hand-over</h3><p>Same-day edit if booked, photos in one to three days, recordings delivered through our private cloud.</p></div></li>
  </ol>
</div></section>
<section class="cta-band"><div class="wrap">
  <h2>Planning an event?</h2>
  <div class="actions"><a class="btn" href="contact.html">Get a quotation</a></div>
</div></section>
""")

# ---------------- CONTACT ----------------
page("contact.html",
     "Contact | JohorStudio.com",
     "WhatsApp 012-798 3745 or email johorstudio@gmail.com. Studio at Bandar Putra, Kulai, Johor, by appointment.",
     f"""
<section class="page-head"><div class="wrap">
  <h1>Get a quotation</h1>
  <p class="lead">Send your event details and we will reply on WhatsApp.</p>
</div></section>
<section class="wrap contact-grid" style="padding-bottom:72px">
  <form class="form" id="enquiry">
    <div class="row">
      <label>Your name<input name="name" required autocomplete="name"></label>
      <label>Organisation<input name="company" autocomplete="organization"></label>
    </div>
    <label>Service
      <select name="service" required>
        <option>Multicamera production</option><option>Livestreaming</option><option>Videography</option>
        <option>Event photography</option><option>Convocation or school photos</option><option>Studio photography</option>
        <option>Not sure yet</option>
      </select>
    </label>
    <div class="row">
      <label>Event date<input name="date" type="date"></label>
      <label>Location<input name="location" required placeholder="Venue, town"></label>
    </div>
    <div class="row">
      <label>Number of guests<input name="guests" inputmode="numeric" placeholder="e.g. 800"></label>
      <label>Budget (optional)<input name="budget" placeholder="e.g. RM 5,000"></label>
    </div>
    <label>Anything else<textarea name="message" placeholder="Programme, screens, streaming platform"></textarea></label>
    <button class="btn" type="submit">{WA_ICON}Send on WhatsApp</button>
    <p class="hint">This opens WhatsApp with your details filled in. Nothing is stored on this website.</p>
  </form>
  <div class="details">
    <div><h3>WhatsApp or call</h3><p><a href="{WA}">{PHONE}</a></p></div>
    <div><h3>Email</h3><p><a href="mailto:{EMAIL}">{EMAIL}</a></p></div>
    <div><h3>Studio, by appointment</h3><p>{ADDRESS}</p><p><a href="{MAPS}">Open in Google Maps</a></p></div>
    <div><h3>Raya photoshoot</h3><p><a href="raya.html">Raya studio photoshoot</a></p></div>
    <iframe class="map" title="Studio location" loading="lazy" referrerpolicy="no-referrer-when-downgrade"
      src="https://www.google.com/maps?q={ADDRESS.replace(' ', '+')}&output=embed"></iframe>
  </div>
</section>
""")
print("built")
