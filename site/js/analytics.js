// Umami event tracking for the buttons that matter (WhatsApp, booking, email, phone, enquiry form).
// Umami itself is loaded by the <script> tag in the page head. If it is blocked or not loaded,
// window.umami is undefined and nothing happens, so the site keeps working.
(function () {
  function track(name, data) {
    try {
      if (window.umami && typeof window.umami.track === "function") {
        window.umami.track(name, data || {});
      }
    } catch (err) { /* analytics must never break the page */ }
  }

  document.addEventListener("click", function (e) {
    var a = e.target && e.target.closest ? e.target.closest("a[href]") : null;
    if (!a) return;
    var href = a.getAttribute("href") || "";
    var name = "";
    if (href.indexOf("wa.me/") !== -1) name = "whatsapp_click";
    else if (href.indexOf("bookings.johorstudio.cc") !== -1) name = "booking_click";
    else if (href.indexOf("mailto:") === 0) name = "email_click";
    else if (href.indexOf("tel:") === 0) name = "phone_click";
    if (name) {
      track(name, {
        page: location.pathname,
        label: (a.textContent || "").trim().slice(0, 60)
      });
    }
  }, true);

  document.addEventListener("submit", function (e) {
    if (e.target && e.target.id === "enquiry") {
      track("enquiry_submit", { page: location.pathname });
    }
  }, true);
})();
