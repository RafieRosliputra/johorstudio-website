/* QR Creator (qr.html): QR code with a logo in the middle, a title above and the link below.
   Uses js/vendor/qrcode.min.js to make the code and js/vendor/jsQR.min.js to check it scans. */
(function () {
  var app = document.querySelector("[data-qr]");
  if (!app || typeof qrcode !== "function") return;

  // Saved PNG size. The preview is the same canvas scaled down by CSS.
  var W = 2000;
  var H = Math.round(W * 543 / 480);
  var QR_SIZE = Math.round(W * 0.75);
  var QR_TOP = Math.round(H * 0.17);
  var INK = "#20272b";
  var FONT = '"Archivo", system-ui, sans-serif';
  var STORE = "js-qr-creator";
  var DEFAULT_LOGO = (document.body.dataset.root || "") + "img/logo-dark.png";

  var canvas = app.querySelector("canvas");
  var ctx = canvas.getContext("2d");
  canvas.width = W; canvas.height = H;

  var linkEl = app.querySelector("#qr-link");
  var titleEl = app.querySelector("#qr-title");
  var fileEl = app.querySelector("#qr-logo");
  var pick = app.querySelector(".qr-logo-pick");
  var clearBtn = app.querySelector("[data-qr-clear]");
  var logEl = app.querySelector(".qr-log");
  var logoImg = null, logoData = null;
  var PICK_HINT = pick.innerHTML;

  function log(msg, cls) {
    var line = document.createElement("div");
    var t = document.createElement("span");
    t.className = "qr-t";
    t.textContent = new Date().toLocaleTimeString("en-GB") + " ";
    var m = document.createElement("span");
    if (cls) m.className = cls;
    m.textContent = msg;
    line.appendChild(t); line.appendChild(m);
    logEl.appendChild(line);
    logEl.scrollTop = logEl.scrollHeight;
  }

  function persist() {
    try { localStorage.setItem(STORE, JSON.stringify({ link: linkEl.value, title: titleEl.value, logo: logoData })); } catch (e) {}
  }

  function restore() {
    var s = null;
    try { s = JSON.parse(localStorage.getItem(STORE) || "null"); } catch (e) {}
    // First visit: start with the JohorStudio logo. A removed logo stays removed.
    if (!s) return fetch(DEFAULT_LOGO).then(function (r) { return r.blob(); }).then(function (b) {
      return new Promise(function (res) { var rd = new FileReader(); rd.onload = function () { res(rd.result); }; rd.readAsDataURL(b); });
    }).then(function (d) { return setLogo(d, true); }).catch(function () {});
    if (s.link) linkEl.value = s.link;
    if (s.title != null) titleEl.value = s.title;
    return s.logo ? setLogo(s.logo, true) : Promise.resolve();
  }

  function setLogo(dataUrl, quiet) {
    return new Promise(function (res) {
      var img = new Image();
      img.onload = function () {
        logoImg = img; logoData = dataUrl;
        pick.innerHTML = "";
        var p = new Image(); p.src = dataUrl; p.alt = "Selected logo";
        pick.appendChild(p);
        clearBtn.hidden = false;
        if (!quiet) log("Logo loaded (" + img.naturalWidth + "×" + img.naturalHeight + ")");
        res();
      };
      img.onerror = function () { log("Could not read that logo file", "qr-err"); res(); };
      img.src = dataUrl;
    });
  }

  function clearLogo() {
    logoImg = null; logoData = null;
    pick.innerHTML = PICK_HINT;
    clearBtn.hidden = true;
    log("Logo removed");
    render();
  }

  // Shrink the font until the text fits.
  function fitFont(text, maxSize, maxWidth) {
    var size = maxSize;
    do {
      ctx.font = "700 " + size + "px " + FONT;
      if (ctx.measureText(text).width <= maxWidth) break;
      size -= 2;
    } while (size > 10);
  }

  function render() {
    var link = linkEl.value.trim();
    var title = titleEl.value.trim();
    ctx.fillStyle = "#fff";
    ctx.fillRect(0, 0, W, H);

    if (!link) {
      ctx.fillStyle = "#66737a";
      ctx.font = "60px " + FONT;
      ctx.textAlign = "center";
      ctx.fillText("Enter a link", W / 2, H / 2);
      log("Link is empty", "qr-err");
      return false;
    }

    var qr;
    try {
      qr = qrcode(0, "H");   // H = ~30% error correction, so the logo in the middle still scans
      qr.addData(link, "Byte");
      qr.make();
    } catch (e) {
      log("Link is too long for a QR code", "qr-err");
      return false;
    }

    var n = qr.getModuleCount();
    var cell = QR_SIZE / n;
    var x0 = (W - QR_SIZE) / 2, y0 = QR_TOP;

    // Logo hole, snapped to the module grid and kept to ~7% of the code's area.
    var hole = null, box = null;
    if (logoImg) {
      var ar = logoImg.naturalWidth / logoImg.naturalHeight;
      var lw = QR_SIZE * 0.40, lh = lw / ar;
      if (lh > QR_SIZE * 0.24) { lh = QR_SIZE * 0.24; lw = lh * ar; }
      var maxArea = QR_SIZE * QR_SIZE * 0.07;
      if (lw * lh > maxArea) { var k = Math.sqrt(maxArea / (lw * lh)); lw *= k; lh *= k; }
      var hw = Math.min(n - 16, Math.ceil(lw / cell) + 2);
      var hh = Math.min(n - 16, Math.ceil(lh / cell) + 2);
      var hc = Math.floor((n - hw) / 2), hr = Math.floor((n - hh) / 2);
      hole = { c0: hc, c1: hc + hw, r0: hr, r1: hr + hh };
      box = { w: lw, h: lh, cx: x0 + (hc + hw / 2) * cell, cy: y0 + (hr + hh / 2) * cell };
    }

    ctx.fillStyle = "#000";
    for (var r = 0; r < n; r++) {
      for (var c = 0; c < n; c++) {
        if (hole && c >= hole.c0 && c < hole.c1 && r >= hole.r0 && r < hole.r1) continue;
        // Overdraw by a pixel so neighbouring modules show no seams.
        if (qr.isDark(r, c)) ctx.fillRect(Math.floor(x0 + c * cell), Math.floor(y0 + r * cell), Math.ceil(cell) + 1, Math.ceil(cell) + 1);
      }
    }
    if (box) {
      ctx.imageSmoothingQuality = "high";
      ctx.drawImage(logoImg, box.cx - box.w / 2, box.cy - box.h / 2, box.w, box.h);
    }

    ctx.fillStyle = INK;
    ctx.textAlign = "center";
    ctx.textBaseline = "alphabetic";
    if (title) {
      fitFont(title, 120, QR_SIZE * 1.05);
      ctx.fillText(title, W / 2, QR_TOP - 70);
    }
    var shown = link.length > 60 ? link.slice(0, 57) + "…" : link;
    fitFont(shown, 80, QR_SIZE * 1.05);
    ctx.fillText(shown, W / 2, y0 + QR_SIZE + 110);

    // Small credit line at the bottom of every saved image.
    ctx.fillStyle = "#66737a";
    ctx.font = "500 40px " + FONT;
    ctx.fillText("Created using johorstudio.com/qr", W / 2, H - 118);
    ctx.font = "400 34px " + FONT;
    ctx.fillText("It's free, have some fun!", W / 2, H - 68);

    log("QR made: " + n + "×" + n + " modules, " + link.length + " characters");
    verify(link);
    persist();
    return true;
  }

  // Decode the finished image to make sure it scans back to the link.
  function verify(link) {
    if (typeof jsQR !== "function") return;
    var c = document.createElement("canvas");
    c.width = 800; c.height = Math.round(H * 800 / W);
    var cx = c.getContext("2d");
    cx.drawImage(canvas, 0, 0, c.width, c.height);
    var d = cx.getImageData(0, 0, c.width, c.height);
    var res = jsQR(d.data, d.width, d.height);
    if (res && res.data === link) log("Scan check: OK ✓", "qr-ok");
    else if (res) log("Scan check: wrong data (" + res.data + ")", "qr-err");
    else log("Scan check: FAILED, try a smaller or simpler logo", "qr-err");
  }

  function save() {
    if (!render()) return;
    var base = (titleEl.value.trim() || "qr").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
    var slug = linkEl.value.trim().split("/").filter(Boolean).pop().replace(/[^a-z0-9]+/gi, "-");
    var name = (base || "qr") + "_" + (slug || "link") + ".png";
    canvas.toBlob(function (blob) {
      var a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = name;
      document.body.appendChild(a); a.click(); a.remove();
      setTimeout(function () { URL.revokeObjectURL(a.href); }, 2000);
      log("Saved " + name + " (" + W + "×" + H + "px)", "qr-ok");
    }, "image/png");
    // Umami: record the link only (not the image). Does nothing if Umami is blocked.
    try {
      if (window.umami && typeof window.umami.track === "function") window.umami.track("qr_save", { link: linkEl.value.trim().slice(0, 500) });
    } catch (e) {}
  }

  pick.addEventListener("click", function () { fileEl.click(); });
  fileEl.addEventListener("change", function () {
    var f = fileEl.files[0];
    if (!f) return;
    var rd = new FileReader();
    rd.onload = function () { setLogo(rd.result).then(render); };
    rd.readAsDataURL(f);
    fileEl.value = "";
  });
  clearBtn.addEventListener("click", clearLogo);
  app.querySelector("[data-qr-update]").addEventListener("click", render);
  app.querySelector("[data-qr-save]").addEventListener("click", save);
  [linkEl, titleEl].forEach(function (el) {
    el.addEventListener("keydown", function (e) { if (e.key === "Enter") { e.preventDefault(); render(); } });
  });

  log("QR Creator ready");
  // Wait for Archivo so the title is drawn in the site font.
  var fontReady = document.fonts && document.fonts.load ? document.fonts.load("700 100px Archivo").catch(function () {}) : Promise.resolve();
  Promise.all([fontReady, restore()]).then(render);
})();
