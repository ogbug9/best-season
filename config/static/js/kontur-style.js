/* Оформление только HotelWidget: не меняет действия SDK и данные брони. */
(function () {
  "use strict";
  var modal = document.querySelector("[data-booking-modal]");
  if (!modal || typeof MutationObserver === "undefined") return;
  var pending = false;
  var descriptionId = 0;
  var contentObserver = new MutationObserver(schedule);

  function decorate() {
    pending = false;
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
        var expanded = link.textContent.trim() === "Коротко";
        description.setAttribute("data-bs-expanded", String(expanded));
        var toggle = description.nextElementSibling;
        if (!toggle || !toggle.hasAttribute("data-bs-description-toggle")) {
          toggle = document.createElement("button");
          toggle.type = "button";
          toggle.setAttribute("data-bs-description-toggle", "");
          if (!description.id) description.id = "bs-kontur-description-" + (++descriptionId);
          toggle.setAttribute("aria-controls", description.id);
          toggle.addEventListener("click", function () {
            var paragraph = this.previousElementSibling;
            var nativeLink = paragraph.querySelector('[data-tid="ShowMoreLink"]');
            // Bound the paragraph before React inserts the full description.
            if (this.getAttribute("aria-expanded") !== "true") paragraph.setAttribute("data-bs-expanded", "true");
            if (nativeLink) nativeLink.click();
          });
          description.insertAdjacentElement("afterend", toggle);
        }
        var caption = expanded ? "Свернуть описание" : "Подробнее";
        if (toggle.textContent !== caption) toggle.textContent = caption;
        toggle.setAttribute("aria-expanded", String(expanded));
      });
      root.querySelectorAll('[data-bs-description-toggle]').forEach(function (toggle) {
        var description = toggle.previousElementSibling;
        if (!description || !description.hasAttribute("data-bs-description") || !description.querySelector('[data-tid="ShowMoreLink"]')) toggle.remove();
      });
    });
  }
  function schedule() {
    if (!pending) { pending = true; queueMicrotask(decorate); }
  }
  function sync() {
    contentObserver.disconnect();
    if (modal.open) {
      contentObserver.observe(document.body, { childList: true, subtree: true, characterData: true,
        attributes: true, attributeFilter: ["disabled"] });
      schedule();
    } else {
      pending = false;
    }
  }
  new MutationObserver(sync).observe(modal, { attributes: true, attributeFilter: ["open"] });
  sync();
})();
