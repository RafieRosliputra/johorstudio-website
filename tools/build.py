"""Builds the HTML pages in site/ from the content below.
Header and footer are shared, so contact details are changed in one place.
Run:  python3 tools/build.py   (optional — the built pages are already in site/)
"""
import pathlib, html

ROOT = pathlib.Path(__file__).resolve().parent.parent / "site"
WA = "https://wa.me/60127983745"
PHONE = "012-798 3745"
EMAIL = "johorstudio@gmail.com"
ADDRESS = "3038-A, Jln Merbau Satu, Bandar Putra, 81000 Kulai, Johor"
COMPANY = "PROMEDIA CREATIVE SOLUTIONS (JR0113470-V)"
MAPS = "https://maps.app.goo.gl/e5CBbhgkZm5Z6fnW8"
IG = "https://instagram.com/johorstudio"
TT = "https://www.tiktok.com/@johorstudio"
YT = "https://www.youtube.com/@rafierosliputra"
SITE = "https://johorstudio.com"

WA_ICON = '<svg viewBox="0 0 24 24" aria-hidden="true" fill="currentColor"><path d="M12 2a10 10 0 0 0-8.6 15.1L2 22l5-1.3A10 10 0 1 0 12 2Zm0 18.2a8.2 8.2 0 0 1-4.2-1.2l-.3-.2-3 .8.8-2.9-.2-.3A8.2 8.2 0 1 1 12 20.2Zm4.5-6.1c-.2-.1-1.5-.7-1.7-.8s-.4-.1-.6.1-.6.8-.8 1-.3.2-.5.1a6.7 6.7 0 0 1-3.3-2.9c-.3-.4.3-.4.7-1.3.1-.2 0-.3 0-.4l-.8-1.8c-.2-.5-.4-.4-.6-.4h-.5a1 1 0 0 0-.7.3 3 3 0 0 0-.9 2.2 5.2 5.2 0 0 0 1.1 2.8 11.9 11.9 0 0 0 4.6 4c1.7.7 2.4.8 3.2.7a2.8 2.8 0 0 0 1.8-1.3 2.3 2.3 0 0 0 .2-1.3c-.1-.1-.3-.2-.5-.3Z"/></svg>'

NAV = [("index.html", "Home"), ("services.html", "Services"), ("portfolio.html", "Portfolio"),
       ("projects.html", "Projects"), ("about.html", "About"), ("contact.html", "Contact")]


def page(file, title, desc, body, extra_head=""):
    nav = "\n".join(
        f'<a href="{h}"{" aria-current=\"page\"" if h == file else ""}>{t}</a>' for h, t in NAV)
    canonical = SITE + "/" + ("" if file == "index.html" else file)
    out = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
<link rel="canonical" href="{canonical}">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(desc)}">
<meta property="og:image" content="{SITE}/img/hero/hero-07-mcp-led-crowd.webp">
<meta property="og:type" content="website">
<link rel="icon" href="img/favicon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,400..700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="css/style.css">
{extra_head}
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<div class="raya-bar"><div class="wrap"><span>Raya photoshoot season is open at our Bandar Putra studio.</span><a href="https://booking.johorstudio.cc">Book a Raya slot</a></div></div>
<header class="site-header">
  <div class="wrap">
    <a class="brand" href="index.html"><img src="img/logo-dark.png" alt="JohorStudio.com" width="131" height="46"></a>
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
        <img src="img/logo-light.png" alt="JohorStudio.com" width="154" height="54">
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
      <span>© <span data-year>2026</span> JohorStudio.com, {COMPANY}</span>
      <span>Serving Kulai, Johor Bahru, Pontian, Kota Tinggi, Kluang, Simpang Renggam and Batu Pahat</span>
    </div>
  </div>
</footer>
<a class="wa-float" href="{WA}" aria-label="WhatsApp JohorStudio.com">{WA_ICON}<span>WhatsApp</span></a>
<script src="js/main.js" defer></script>
</body>
</html>
"""
    (ROOT / file).write_text(out, encoding="utf-8")


def img(name, alt, folder="gallery", sm=True, cls="", lazy=True):
    src = f"img/{folder}/{name}{'-sm' if sm else ''}.webp"
    return f'<img src="{src}" alt="{html.escape(alt)}"{" loading=\"lazy\"" if lazy else ""}{f" class=\"{cls}\"" if cls else ""}>'


# ---------------- HOME ----------------
HERO = [
    ("hero-07-mcp-led-crowd", "Live camera on stage, Butterfly 22nd Convocation, Trove Hotel"),
    ("hero-01-live-control-adtec2026", "Live switching desk, ADTEC JTM 29th Convocation 2026"),
    ("hero-02-multicam-stage-adtec2026", "Stage camera, ADTEC JTM 29th Convocation 2026"),
    ("hero-03-crew-ballroom", "Our crew on the ballroom floor"),
    ("hero-04-corporate-symposium", "Primary Care Symposium, DoubleTree Johor Bahru"),
    ("hero-05-fashion-studio", "Fashion shoot by JohorStudio.com"),
    ("hero-06-motocross-action", "Motocross action photography"),
]
pgm = "\n".join(
    f'<img src="img/hero/{n}.webp" data-thumb="img/hero/{n}-sm.webp" data-caption="{html.escape(c)}" alt="{html.escape(c)}"{" class=\"is-live\"" if i == 0 else " loading=\"lazy\""}>'
    for i, (n, c) in enumerate(HERO))

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
<section class="hero">
  <div class="wrap">
    <div class="multiview" aria-label="Recent work">
      <div class="pgm">
        <span class="tag"><span class="dot"></span>Program</span>
        {pgm}
        <span class="caption"></span>
      </div>
      <ul class="pvw-list">
        <li><button class="pvw" type="button"><img alt=""><span>Preview</span></button></li>
        <li><button class="pvw" type="button"><img alt=""><span>Preview</span></button></li>
        <li><button class="pvw" type="button"><img alt=""><span>Preview</span></button></li>
      </ul>
    </div>
    <div class="hero-copy">
      <div>
        <h1>Your event, on every screen.</h1>
        <p class="lead">JohorStudio.com is a professional digital media provider since 2014. We run the cameras, the switcher and the stream, and work hand in hand with you and your event organiser.</p>
      </div>
      <div class="actions">
        <a class="btn" href="contact.html">Get a quotation</a>
        <a class="btn btn-line" href="portfolio.html">See our work</a>
      </div>
    </div>
  </div>
</section>

<section class="section bg-white">
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
    <div class="section-head"><h2>Recent projects</h2><a href="projects.html">All projects</a></div>
    <div class="projects">
      <a class="project wide" href="projects.html#butterfly">
        <figure>{img("bts-butterfly-operator-crowd", "Camera operator facing the audience at Trove Hotel")}</figure>
        <p class="client">Butterfly Education Centre, Trove Hotel JB</p>
        <h3>22nd Convocation, live to the LED wall</h3>
      </a>
      <a class="project text-only" href="projects.html#consal">
        <figure><p>Livestream and multicam to LED for a regional library congress</p></figure>
        <p class="client">CONSAL XIX, Kuala Lumpur 2025</p>
        <h3>Southeast Asian librarians, live</h3>
      </a>
      <a class="project" href="projects.html#adtec">
        <figure>{img("bts-adtec2026-camera-row", "Camera positions at ADTEC JTM convocation")}</figure>
        <p class="client">ADTEC JTM, 2026</p>
        <h3>29th Convocation coverage</h3>
      </a>
      <a class="project text-only" href="projects.html#hospital">
        <figure><p>Live procedure broadcasts from theatre to lecture hall</p></figure>
        <p class="client">Hospital Sultanah Aminah and Hospital Sultan Ismail</p>
        <h3>Live medical streaming</h3>
      </a>
      <a class="project text-only" href="projects.html#petronas">
        <figure><p>Livestream production for a corporate session</p></figure>
        <p class="client">Petronas</p>
        <h3>Corporate livestream</h3>
      </a>
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
    ("photography", "Event and corporate photography", ["photo-event-symposium-speaker", "photo-corporate-portrait-02", "photo-sports-motocross-01"],
     "Conferences, dinner functions, award ceremonies, sports and official portraits. Edited photos are delivered within one to three days through our private cloud.",
     ["Conferences and symposiums", "Dinner functions and award nights", "Official and corporate portraits", "Sports and motorsport"]),
    ("convocation", "Convocation and school photography", ["convo-graduation-stage-01", "school-class-photo-01", "school-class-photo-02"],
     "Scroll presentations on stage, a pop-up studio at the venue for families, and class and group photos for primary, secondary and tertiary institutions.",
     ["On-stage scroll moments", "Pop-up studio at your venue", "Class, prefect and club photos", "Prints in 4R, 8R and frames, or digital only"]),
    ("studio", "Studio photography", ["studio-fashion-06", "studio-product-01", "studio-corporate-01"],
     "Our studio in Bandar Putra, Kulai, is open by appointment for family and Raya portraits, corporate headshots, products, fashion and convocation shoots.",
     ["Family and Raya photoshoots", "Corporate headshots", "Product and fashion", "Convocation portraits"]),
]
svc = "\n".join(f"""<article class="svc-detail" id="{k}">
  <div class="svc-media">{"".join(img(i, t) for i in imgs)}</div>
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
  <p class="lead">Real jobs, real set-ups. Choose a service to filter.</p>
</div></section>
<section class="wrap" style="padding-bottom:72px">
  <div class="filters" role="group" aria-label="Filter by service">
    {"".join(f'<button type="button" data-filter="{k}" aria-pressed="{"true" if k == "all" else "false"}">{t}</button>' for k, t in FILTERS)}
  </div>
  <div class="gallery"></div>
  <dialog class="lightbox" aria-label="Photo"><button class="close" type="button">Close</button><img alt=""><p></p></dialog>
</section>
<section class="section bg-white"><div class="wrap">
  <div class="section-head"><h2>Video</h2><a href="{YT}">Our YouTube channel</a></div>
  <p data-videos-empty class="muted">Watch our livestreams and event videos on <a href="{YT}">YouTube</a>.</p>
  <div class="videos"></div>
</div></section>
""")

# ---------------- PROJECTS ----------------
CASES = [
    ("butterfly", "Butterfly Education Centre", "22nd Convocation, “Let's Hunt and Hop!”",
     [("Venue", "Trove Hotel, Johor Bahru"), ("Date", "October 2026"), ("Services", "Multicam to LED, videography, photography")],
     "A packed ballroom of families. Our operators worked the stage and the floor while the live feed played on the LED wall, so every parent could see their child up close.",
     ["bts-butterfly-operator-crowd", "bts-butterfly-two-operators-wide", "bts-butterfly-control-room-mixer", "bts-butterfly-gimbal-monitor"]),
    ("consal", "CONSAL XIX", "Congress of Southeast Asian Librarians",
     [("Venue", "Kuala Lumpur"), ("Year", "2025"), ("Services", "Livestream, multicam to LED")],
     "Our proudest regional project: livestreaming and live camera switching to the LED screens for delegates from across Southeast Asia.", []),
    ("adtec", "ADTEC JTM", "29th Convocation",
     [("Year", "2026"), ("Services", "Multicam, livestream")],
     "Multiple camera positions along the hall with a live switching desk among the audience, covering every graduate on stage.",
     ["hero-01-live-control-adtec2026", "bts-adtec2026-camera-row", "bts-adtec2026-viewfinder", "bts-team-photo-adtec2026"]),
    ("hospital", "Hospital Sultanah Aminah and Hospital Sultan Ismail", "Live medical streaming",
     [("Location", "Johor Bahru"), ("Services", "Livestream, procedure recording")],
     "Live broadcasts and recordings of medical procedures for training sessions, sending the theatre feed to the lecture hall and to online participants.", []),
    ("petronas", "Petronas", "Corporate livestream",
     [("Services", "Livestream")], "Livestream production for a Petronas corporate session.", []),
    ("aata", "Asia Aeronautical Training Academy (AATA)", "Event photography",
     [("Services", "Photography")], "Event photography for AATA.", []),
]
cases = "\n".join(f"""<article class="case" id="{k}">
  <div>
    <p class="muted" style="margin:0">{c}</p>
    <h2>{t}</h2>
    <dl>{"".join(f"<dt>{a}</dt><dd>{b}</dd>" for a, b in meta)}</dl>
    <p>{d}</p>
  </div>
  <div class="case-media">{"".join(img(i, t, folder="hero" if i.startswith("hero") else "gallery") for i in imgs)}</div>
</article>""" for k, c, t, meta, d, imgs in CASES)
page("projects.html",
     "Projects | JohorStudio.com",
     "Selected projects: CONSAL XIX, Hospital Sultanah Aminah, Hospital Sultan Ismail, Petronas, ADTEC JTM, Butterfly Education Centre.",
     f"""
<section class="page-head"><div class="wrap">
  <h1>Projects</h1>
  <p class="lead">A few of the events we have produced, from regional congresses to hospital theatres.</p>
</div></section>
<div class="wrap" style="padding-bottom:72px">
{cases}
</div>
""")

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
    <div><h3>Raya photoshoot</h3><p><a href="https://booking.johorstudio.cc">booking.johorstudio.cc</a></p></div>
    <iframe class="map" title="Studio location" loading="lazy" referrerpolicy="no-referrer-when-downgrade"
      src="https://www.google.com/maps?q={ADDRESS.replace(' ', '+')}&output=embed"></iframe>
  </div>
</section>
""")
print("built")
