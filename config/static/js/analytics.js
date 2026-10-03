/* Общие цели сайта. Сетевой счётчик включается только после согласия. */
(function () {
  "use strict";
  function readConfig(id) {
    var node = document.getElementById(id);
    try { return node ? JSON.parse(node.textContent) : null; } catch (_) { return null; }
  }
  var counter = Number(readConfig("metrika-id"));
  var contacts = readConfig("analytics-config") || {};
  var accepted = false;
  try { accepted = window.localStorage.getItem("bs-cookie-consent-v1") === "accepted"; } catch (_) {}
  var loaded = document.readyState === "complete";
  var started = false;
  var scheduled = false;
  var pending = [];

  function send(goal, params) {
    try { window.ym(counter, "reachGoal", goal, params); } catch (_) {}
  }
  function track(goal, params) {
    params = params || {};
    window.dataLayer = window.dataLayer || [];
    window.dataLayer.push({ event: goal, params: params });
    if (!counter) return;
    if (started && accepted) send(goal, params);
    else pending.push({ goal: goal, params: params });
  }
  window.bsTrack = track;

  function start() {
    scheduled = false;
    if (!accepted || started || !counter) return;
    started = true;
    window.ym = window.ym || function () { (window.ym.a = window.ym.a || []).push(arguments); };
    window.ym.l = Date.now();
    var script = document.createElement("script");
    script.async = true;
    script.src = "https://mc.yandex.ru/metrika/tag.js";
    document.head.appendChild(script);
    window.ym(counter, "init", { webvisor: true, clickmap: true, trackLinks: true, accurateTrackBounce: true });
    pending.forEach(function (event) { send(event.goal, event.params); });
    pending = [];
  }
  function schedule() {
    if (!loaded || !accepted || !counter || started || scheduled) return;
    scheduled = true;
    if (window.requestIdleCallback) window.requestIdleCallback(start, { timeout: 2000 });
    else start();
  }
  window.addEventListener("load", function () { loaded = true; schedule(); }, { once: true });
  document.addEventListener("bs:cookie-consent", function (event) {
    accepted = event.detail === "accepted";
    schedule();
  });
  schedule();

  document.addEventListener("click", function (event) {
    var link = event.target.closest && event.target.closest("a[href]");
    if (!link) return;
    var url;
    try { url = new URL(link.href, window.location.href); } catch (_) { return; }
    if (link.matches && link.matches('[data-directions-link]')) track('directions_click');
    var channel = "";
    if (url.protocol === "tel:") channel = "phone";
    else if (url.hostname === "t.me" || url.hostname === "telegram.me" || sameContact(url, contacts.telegramUrl)) channel = "telegram";
    else if (url.hostname === "wa.me" || url.hostname === "api.whatsapp.com" || sameContact(url, contacts.whatsappUrl)) channel = "whatsapp";
    if (!channel) return;
    var place = "other";
    if (link.closest("[data-booking-fallback]")) place = "fallback";
    else if (link.closest("header")) place = "header";
    else if (link.closest("footer")) place = "footer";
    else if (link.closest(".contacts, .contacts-section") || document.body.classList.contains("page-contacts")) place = "contacts";
    track("contact_click", { channel: channel, place: place });
  });

  function sameContact(url, configured) {
    if (!configured) return false;
    try { var other = new URL(configured); return url.origin === other.origin && url.pathname === other.pathname; } catch (_) { return false; }
  }

  if (document.body.classList.contains("page-directions")) track("directions_view");
  var house = document.body.getAttribute("data-house-slug");
  if (house) {
    var scrolled = false;
    function checkScroll() {
      if (scrolled || (window.scrollY + window.innerHeight) / document.documentElement.scrollHeight <= 0.75) return;
      scrolled = true;
      track("house_scroll_75", { house: house });
      window.removeEventListener("scroll", checkScroll);
    }
    window.addEventListener("scroll", checkScroll, { passive: true });
    window.addEventListener("load", checkScroll, { once: true });
    if (loaded) checkScroll();
  }

  var formType = document.body.getAttribute("data-form-success");
  if (formType) {
    document.body.removeAttribute("data-form-success");
    track("form_submitted", { form_type: formType });
    if (formType === "fallback") track("booking_fallback_submitted", { form_type: formType });
    var cleanUrl = new URL(window.location.href);
    cleanUrl.searchParams.delete("form");
    cleanUrl.searchParams.delete("ft");
    window.history.replaceState(window.history.state, "", cleanUrl.pathname + cleanUrl.search + cleanUrl.hash);
  }
})();
