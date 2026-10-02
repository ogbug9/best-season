/* Оформление только HotelWidget: не меняет действия SDK и данные брони. */
(function () {
  "use strict";
  var modal = document.querySelector("[data-booking-modal]");
  if (!modal || typeof MutationObserver === "undefined") return;
  var timer = null;
  var contentObserver = new MutationObserver(schedule);

  function decorate() {
    timer = null;
    if (!modal.open) return;
    var roots = Array.from(modal.querySelectorAll(".kontur-host"))
      .concat(Array.from(document.querySelectorAll("body > .react-ui")));
    roots.forEach(function (root) {
      root.setAttribute("data-bs-kontur", "");
      root.querySelectorAll('[data-tid="Button__rootElement"]').forEach(function (button) {
        var label = button.textContent.replace(/\s+/g, " ").trim();
        var kind = !label ? "icon" : "neutral";
        if (button.closest('[data-tid="Select__root"]')) kind = "control";
        else if (button.closest('[data-tid="AddLink"]')) kind = "link";
        else if (/^(Проверить наличие|Выбрать|Добавить|Применить|Продолжить|Забронировать|Оплатить)(\s|$)/.test(label)
          || /^\d+\s+номер/.test(label)) kind = "primary";
        if (button.getAttribute("data-bs-kind") !== kind) button.setAttribute("data-bs-kind", kind);
      });
      root.querySelectorAll('[data-tid="ShowMoreLink"]').forEach(function (link) {
        var description = link.parentElement;
        description.setAttribute("data-bs-description", "");
        description.setAttribute("data-bs-expanded", String(link.textContent.trim() === "Коротко"));
      });
    });
  }
  function schedule() {
    if (!timer) timer = setTimeout(decorate, 0);
  }
  function sync() {
    contentObserver.disconnect();
    if (modal.open) {
      contentObserver.observe(document.body, { childList: true, subtree: true, characterData: true,
        attributes: true, attributeFilter: ["disabled"] });
      schedule();
    } else {
      clearTimeout(timer);
      timer = null;
    }
  }
  new MutationObserver(sync).observe(modal, { attributes: true, attributeFilter: ["open"] });
  sync();
})();
