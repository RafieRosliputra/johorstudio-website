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
  document.querySelectorAll("[data-year]").forEach(function (el) { el.textContent = new Date().getFullYear(); });

  function getJSON(url) {
    return fetch(url, { cache: "no-cache" }).then(function (r) { if (!r.ok) throw new Error(url); return r.json(); });
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

  // Hero multiview: program window cycles; preview tiles cut to a shot
  var mv = document.querySelector(".multiview");
  if (mv) {
    var shots = Array.prototype.slice.call(mv.querySelectorAll(".pgm img"));
    var cap = mv.querySelector(".pgm .caption");
    var tiles = Array.prototype.slice.call(mv.querySelectorAll(".pvw"));
    var current = 0, timer = null;
    var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    function cut(i) {
      shots[current].classList.remove("is-live");
      current = (i + shots.length) % shots.length;
      shots[current].classList.add("is-live");
      if (cap) cap.textContent = shots[current].dataset.caption || "";
      // previews always show the next three shots
      tiles.forEach(function (t, k) {
        var n = (current + 1 + k) % shots.length;
        var img = t.querySelector("img");
        img.src = shots[n].dataset.thumb;
        img.alt = "";
        t.dataset.target = n;
        t.setAttribute("aria-label", "Show: " + (shots[n].dataset.caption || "next shot"));
      });
    }
    function play() { if (!reduce) timer = setInterval(function () { cut(current + 1); }, 5000); }
    tiles.forEach(function (t) {
      t.addEventListener("click", function () { clearInterval(timer); cut(parseInt(t.dataset.target, 10)); play(); });
    });
    mv.addEventListener("mouseenter", function () { clearInterval(timer); });
    mv.addEventListener("mouseleave", function () { clearInterval(timer); play(); });
    cut(0); play();
  }

  // Portfolio gallery with filters and lightbox
  var gallery = document.querySelector(".gallery");
  if (gallery) {
    var dlg = document.querySelector(".lightbox");
    var dlgImg = dlg.querySelector("img"), dlgCap = dlg.querySelector("p");
    dlg.querySelector(".close").addEventListener("click", function () { dlg.close(); });
    dlg.addEventListener("click", function (e) { if (e.target === dlg) dlg.close(); });

    getJSON("data/portfolio.json").then(function (data) {
      data.items.forEach(function (it) {
        var b = document.createElement("button");
        b.type = "button";
        b.dataset.category = it.category;
        b.setAttribute("aria-label", "Open photo: " + it.caption);
        var img = document.createElement("img");
        img.src = "img/gallery/" + it.file + "-sm.webp";
        img.alt = it.caption;
        img.loading = "lazy";
        b.appendChild(img);
        b.addEventListener("click", function () {
          dlgImg.src = "img/gallery/" + it.file + ".webp";
          dlgImg.alt = it.caption;
          dlgCap.textContent = it.caption;
          dlg.showModal();
        });
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
