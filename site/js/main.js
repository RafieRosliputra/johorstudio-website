// JohorStudio.com — site behaviour. No libraries, no tracking.
(function () {
  "use strict";
  var WA = "60127983745";

  // Mobile menu
  var toggle = document.querySelector(".menu-toggle");
  var nav = document.getElementById("nav");
  if (toggle && nav) {
    toggle.addEventListener("click", function () {
      var open = nav.classList.toggle("is-open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
  }

  // Year in footer
  document.querySelectorAll("[data-this-year]").forEach(function (el) { el.textContent = new Date().getFullYear(); });

  // Pages inside projects/<name>/ set data-root="../../" so shared files are found
  var ROOT = document.body.getAttribute("data-root") || "";
  function getJSON(url) {
    return fetch(ROOT + url, { cache: "no-cache" }).then(function (r) { if (!r.ok) throw new Error(url); return r.json(); });
  }

  // Raya studio booking: shown only during the season set in data/raya.json
  var rayaBar = document.querySelector(".raya-bar");
  if (rayaBar) {
    getJSON("data/raya.json").then(function (cfg) {
      var today = new Date().toISOString().slice(0, 10);
      var on = cfg.seasons.some(function (s) { return today >= s.start && today <= s.end; });
      if (on) {
        rayaBar.querySelectorAll("a").forEach(function (a) { a.href = cfg.url; });
        rayaBar.classList.add("is-on");
        document.querySelectorAll("[data-raya]").forEach(function (el) { el.hidden = false; el.href = cfg.url; });
      }
    }).catch(function () {});
  }

  // Home: transparent header over the hero, solid after scrolling past it
  var header = document.querySelector(".site-header");
  var heroEl = document.querySelector(".hero-full");
  if (header && heroEl) {
    var setSolid = function () { var past = window.scrollY > heroEl.offsetHeight - 90; header.classList.toggle("is-solid", past); document.body.classList.toggle("at-hero", !past); };
    window.addEventListener("scroll", setSolid, { passive: true });
    setSolid();
    toggle && toggle.addEventListener("click", function () { if (nav.classList.contains("is-open")) header.classList.add("is-solid"); else setSolid(); });
  }

  // Home: full-screen carousel (crossfade, swipe, keyboard)
  if (heroEl) {
    var slides = Array.prototype.slice.call(heroEl.querySelectorAll(".slide"));
    var dots = Array.prototype.slice.call(heroEl.querySelectorAll(".dot-btn"));
    var capEl = heroEl.querySelector(".hero-caption");
    var cur = 0, timer = null;
    var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    function show(i) {
      slides[cur].classList.remove("is-active");
      dots[cur] && dots[cur].removeAttribute("aria-current");
      cur = (i + slides.length) % slides.length;
      slides[cur].classList.add("is-active");
      dots[cur] && dots[cur].setAttribute("aria-current", "true");
      if (capEl) capEl.textContent = slides[cur].querySelector("img").alt;
    }
    function play() { clearInterval(timer); if (!reduce) timer = setInterval(function () { show(cur + 1); }, 6000); }
    function go(i) { show(i); play(); }
    heroEl.querySelector(".hc-prev").addEventListener("click", function () { go(cur - 1); });
    heroEl.querySelector(".hc-next").addEventListener("click", function () { go(cur + 1); });
    dots.forEach(function (d, i) { d.addEventListener("click", function () { go(i); }); });
    var x0 = null;
    heroEl.addEventListener("touchstart", function (e) { x0 = e.touches[0].clientX; }, { passive: true });
    heroEl.addEventListener("touchend", function (e) {
      if (x0 === null) return;
      var dx = e.changedTouches[0].clientX - x0; x0 = null;
      if (Math.abs(dx) > 45) go(cur + (dx < 0 ? 1 : -1));
    });
    heroEl.addEventListener("focusin", function () { clearInterval(timer); });
    document.addEventListener("visibilitychange", function () { if (document.hidden) clearInterval(timer); else play(); });
    show(0); play();
  }

  // Lightbox: shows the 1600px image at once, then swaps in full resolution
  var dlg = document.querySelector(".lightbox");
  var openLightbox = function () {};
  if (dlg) {
    var stage = dlg.querySelector(".lb-stage"), big = stage.querySelector("img");
    var cap = dlg.querySelector(".lb-cap"), res = dlg.querySelector(".lb-res");
    dlg.querySelector(".close").addEventListener("click", function () { dlg.close(); });
    dlg.addEventListener("close", function () { big.removeAttribute("src"); stage.classList.remove("is-zoomed"); });
    // Click or tap the full-resolution photo to zoom in; the spot you touched becomes the centre
    big.addEventListener("click", function (e) {
      if (big.dataset.full !== "1") return;
      if (stage.classList.contains("is-zoomed")) { stage.classList.remove("is-zoomed"); return; }
      var r = big.getBoundingClientRect();
      var fx = Math.min(1, Math.max(0, (e.clientX - r.left) / r.width));
      var fy = Math.min(1, Math.max(0, (e.clientY - r.top) / r.height));
      stage.classList.add("is-zoomed");
      stage.scrollLeft = fx * big.offsetWidth - stage.clientWidth / 2;
      stage.scrollTop = fy * big.offsetHeight - stage.clientHeight / 2;
    });
    // copyright: no right-click save or drag on the full-screen photo
    big.addEventListener("contextmenu", function (e) { e.preventDefault(); });
    big.addEventListener("dragstart", function (e) { e.preventDefault(); });
    openLightbox = function (src, full, caption, size) {
      stage.classList.remove("is-zoomed");
      big.dataset.full = "0";
      big.src = src; big.alt = caption; cap.textContent = caption;
      res.textContent = full ? "Loading full resolution…" : "";
      dlg.showModal();
      if (full) {
        var hi = new Image();
        hi.onload = function () {
          if (big.getAttribute("src") !== src) return;
          big.src = full; big.dataset.full = "1";
          res.textContent = "Full resolution " + size + ". Click the photo to zoom.";
        };
        hi.src = full;
      }
    };
    document.addEventListener("click", function (e) {
      var t = e.target.closest("[data-lightbox]");
      if (!t) return;
      openLightbox(t.dataset.src, t.dataset.full, t.dataset.caption, t.dataset.size);
    });
  }

  // Portfolio gallery with filters
  var gallery = document.querySelector(".gallery[data-portfolio]");
  if (gallery) {
    getJSON("data/portfolio.json").then(function (data) {
      data.items.forEach(function (it) {
        var b = document.createElement("button");
        b.type = "button";
        b.className = "lb-thumb";
        b.dataset.lightbox = "";
        b.dataset.category = it.category;
        b.dataset.src = "img/gallery/" + it.file + ".webp";
        b.dataset.caption = it.caption;
        if (it.full) { b.dataset.full = "img/gallery/" + it.file + "-full.webp"; b.dataset.size = it.size; }
        b.setAttribute("aria-label", "Open photo: " + it.caption);
        var img = document.createElement("img");
        img.src = "img/gallery/" + it.file + "-sm.webp";
        img.alt = it.caption;
        img.loading = "lazy";
        b.appendChild(img);
        gallery.appendChild(b);
      });
      var start = (location.hash || "").replace("#", "");
      if (start) filter(start);
    });

    var buttons = document.querySelectorAll(".filters button");
    function filter(cat) {
      buttons.forEach(function (x) { x.setAttribute("aria-pressed", x.dataset.filter === cat ? "true" : "false"); });
      gallery.querySelectorAll("button").forEach(function (g) {
        g.hidden = !(cat === "all" || g.dataset.category === cat);
      });
    }
    buttons.forEach(function (b) {
      b.addEventListener("click", function () {
        filter(b.dataset.filter);
        history.replaceState(null, "", b.dataset.filter === "all" ? location.pathname : "#" + b.dataset.filter);
      });
    });
  }

  // Home: recent projects from data/projects.json (made by tools/projects.py)
  var recent = document.querySelector("[data-recent-projects]");
  if (recent) {
    var esc = function (t) { return String(t || "").replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); };
    getJSON("data/projects.json").then(function (data) {
      var n = parseInt(recent.getAttribute("data-recent-projects"), 10) || 5;
      var list = data.items.slice(0, n);
      if (!list.length) return;
      recent.innerHTML = list.map(function (p, i) {
        var wide = i === 0 && p.cover;
        var fig = p.cover
          ? '<figure><img src="' + ROOT + (wide ? p.cover_md : p.cover) + '" alt="' + esc(p.title) + '" loading="lazy"></figure>'
          : '<figure><p>' + esc(p.summary || p.title) + '</p></figure>';
        var who = [p.client, p.location, p.date].filter(Boolean).slice(0, 2).join(", ");
        return '<a class="project' + (wide ? " wide" : "") + (p.cover ? "" : " text-only") + '" href="' + ROOT + p.url + '">' +
          fig + '<p class="client">' + esc(who) + '</p><h3>' + esc(p.title) + '</h3></a>';
      }).join("");
    }).catch(function () {
      recent.innerHTML = '<p><a href="' + ROOT + 'projects/">See all our projects</a></p>';
    });
  }

  // Projects page: filter by year
  var yf = document.querySelector("[data-year-filter]");
  if (yf) {
    var cards = document.querySelectorAll(".pj-card");
    yf.querySelectorAll("button").forEach(function (b) {
      b.addEventListener("click", function () {
        var y = b.getAttribute("data-year");
        yf.querySelectorAll("button").forEach(function (x) { x.setAttribute("aria-pressed", x === b ? "true" : "false"); });
        cards.forEach(function (c) { c.hidden = !(y === "all" || c.getAttribute("data-year") === y); });
      });
    });
  }

  // YouTube videos: thumbnail first, player loads only on click
  var videos = document.querySelector(".videos");
  if (videos) {
    getJSON("data/videos.json").then(function (data) {
      if (!data.items.length) { videos.hidden = true; return; }
      document.querySelectorAll("[data-videos-empty]").forEach(function (el) { el.hidden = true; });
      data.items.forEach(function (v) {
        var box = document.createElement("div");
        box.className = "video";
        var b = document.createElement("button");
        b.type = "button";
        b.innerHTML = '<img loading="lazy" alt="" src="https://i.ytimg.com/vi/' + v.id + '/hqdefault.jpg"><span>Play: ' + v.title.replace(/</g, "&lt;") + "</span>";
        b.addEventListener("click", function () {
          box.innerHTML = '<iframe src="https://www.youtube-nocookie.com/embed/' + v.id + '?autoplay=1" title="' + v.title.replace(/"/g, "&quot;") + '" allow="autoplay; encrypted-media; picture-in-picture" allowfullscreen></iframe>';
        });
        box.appendChild(b);
        videos.appendChild(box);
      });
    }).catch(function () { videos.hidden = true; });
  }

  // Enquiry form: opens WhatsApp with the details filled in
  var form = document.getElementById("enquiry");
  if (form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var f = new FormData(form);
      var lines = [
        "Hi JohorStudio.com, I'd like a quotation.",
        "Name: " + f.get("name"),
        f.get("company") ? "Organisation: " + f.get("company") : "",
        "Service: " + f.get("service"),
        "Event date: " + (f.get("date") || "not fixed yet"),
        "Location: " + f.get("location"),
        f.get("guests") ? "Guests: " + f.get("guests") : "",
        f.get("budget") ? "Budget: " + f.get("budget") : "",
        f.get("message") ? "Notes: " + f.get("message") : ""
      ].filter(Boolean).join("\n");
      window.open("https://wa.me/" + WA + "?text=" + encodeURIComponent(lines), "_blank", "noopener");
    });
  }
})();
