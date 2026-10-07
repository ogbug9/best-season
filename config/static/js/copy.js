/* Копирование по нажатию: телефон на «Контактах», адрес на «Как добраться».

   <a href="tel:+7…" data-copy="+7 …" data-copy-desktop>…<span data-copy-label="Номер скопирован">Позвонить</span></a>
   <button type="button" data-copy="село Страхово, Заречная ул., 44">…</button>

   data-copy-desktop: на телефоне ссылка работает как обычно (звонок), копируем
   только там, где есть мышь. Подпись меняется на 2 с, класс is-success — общее
   состояние «успех» кнопок (Д3). Без Clipboard API — запасной путь через textarea. */
(function () {
  "use strict";
  var desktop = window.matchMedia && window.matchMedia("(hover: hover) and (pointer: fine)").matches;

  function fallbackCopy(text) {
    var area = document.createElement("textarea");
    area.value = text;
    area.setAttribute("readonly", "");
    area.style.position = "fixed";
    area.style.opacity = "0";
    document.body.appendChild(area);
    area.select();
    var ok = false;
    try { ok = document.execCommand("copy"); } catch (_) { ok = false; }
    document.body.removeChild(area);
    return ok;
  }

  function copy(text) {
    if (navigator.clipboard && window.isSecureContext) {
      return navigator.clipboard.writeText(text).then(function () { return true; }, function () { return fallbackCopy(text); });
    }
    return Promise.resolve(fallbackCopy(text));
  }

  document.addEventListener("click", function (event) {
    var target = event.target.closest("[data-copy]");
    if (!target) return;
    if (target.hasAttribute("data-copy-desktop") && !desktop) return;
    event.preventDefault();
    copy(target.getAttribute("data-copy")).then(function (ok) {
      if (!ok) return;
      var label = target.querySelector("[data-copy-label]") || (target.hasAttribute("data-copy-label") ? target : null);
      var previous = label ? label.textContent : "";
      if (label) label.textContent = label.getAttribute("data-copy-label");
      target.classList.add("is-success");
      clearTimeout(target._copyTimer);
      target._copyTimer = setTimeout(function () {
        target.classList.remove("is-success");
        if (label) label.textContent = previous;
      }, 2000);
    });
  });
})();
