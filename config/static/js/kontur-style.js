/* Оформление только HotelWidget: не меняет действия SDK и данные брони. */
(function () {
  "use strict";
  var modal = document.querySelector("[data-booking-modal]");
  if (!modal || typeof MutationObserver === "undefined") return;
  var pending = false;
  var descriptionId = 0;
  var selectedTariff = null;
  var contentObserver = new MutationObserver(schedule);

  document.addEventListener("click", function (event) {
    if (!modal.open) return;
    var button = event.target.closest('[data-tid="Button__rootElement"]');
    if (button && button.textContent.trim() === "Выбрать") {
      selectedTariff = button.closest(".zB7qpf");
      schedule();
    }
  }, true);

  function scrollToTariff(tariff) {
    if (!modal.open || !tariff.isConnected) return;
    var frame = tariff.parentElement;
    while (frame && frame !== document.body) {
      if (/auto|scroll/.test(getComputedStyle(frame).overflowY) && frame.scrollHeight > frame.clientHeight) break;
      frame = frame.parentElement;
    }
    if (!frame || frame === document.body) return;
    var header = frame.querySelector('[data-tid="ModalHeader__root"]');
    var offset = header ? header.getBoundingClientRect().height : 0;
    frame.scrollTo({ top: frame.scrollTop + tariff.getBoundingClientRect().top - frame.getBoundingClientRect().top - offset - 16,
      behavior: "instant" });
  }

  function decorate() {
    pending = false;
    if (!modal.open) return;
    var roots = Array.from(modal.querySelectorAll(".kontur-host"))
      .concat(Array.from(document.querySelectorAll("body > .react-ui")));
    roots.forEach(function (root) {
      root.setAttribute("data-bs-kontur", "");
      root.querySelectorAll('[data-tid="modal-content"]').forEach(function (dialog) {
        var heading = dialog.querySelector('[data-tid="ModalHeader__root"]');
        if (heading && heading.textContent.trim().indexOf("Корзина") === 0) {
          dialog.setAttribute("data-bs-booking-cart", "");
        } else if (dialog.hasAttribute("data-bs-booking-cart")) {
          dialog.removeAttribute("data-bs-booking-cart");
        }
      });
      root.querySelectorAll('[data-tid="Comforts"]').forEach(function (comforts) {
        var toggle = comforts.nextElementSibling;
        if (!toggle || !toggle.hasAttribute("data-bs-comforts-toggle")) {
          comforts.setAttribute("data-bs-comforts-expanded", "false");
          toggle = document.createElement("button");
          toggle.type = "button";
          toggle.setAttribute("data-bs-comforts-toggle", "");
          if (!comforts.id) comforts.id = "bs-kontur-comforts-" + (++descriptionId);
          toggle.setAttribute("aria-controls", comforts.id);
          toggle.addEventListener("click", function () {
            var list = this.previousElementSibling;
            var expanded = this.getAttribute("aria-expanded") !== "true";
            list.setAttribute("data-bs-comforts-expanded", String(expanded));
            var nativeLink = list.querySelector('[data-tid="ComfortsShowLink"]');
            if (expanded && nativeLink && /Показать/.test(nativeLink.textContent)) nativeLink.click();
            this.setAttribute("aria-expanded", String(expanded));
            this.textContent = expanded ? "Свернуть удобства" : "Показать удобства";
          });
          comforts.insertAdjacentElement("afterend", toggle);
          toggle.setAttribute("aria-expanded", "false");
          toggle.textContent = "Показать удобства";
        }
      });
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
      root.querySelectorAll('[data-bs-comforts-toggle]').forEach(function (toggle) {
        if (!toggle.previousElementSibling || !toggle.previousElementSibling.matches('[data-tid="Comforts"]')) toggle.remove();
      });
    });
    if (selectedTariff && !selectedTariff.isConnected) selectedTariff = null;
    if (selectedTariff && selectedTariff.isConnected && selectedTariff.querySelector(".WidgetNumberInputButton")) {
      var tariff = selectedTariff;
      selectedTariff = null;
      requestAnimationFrame(function () { requestAnimationFrame(function () { scrollToTariff(tariff); }); });
    }
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
      selectedTariff = null;
    }
  }
  new MutationObserver(sync).observe(modal, { attributes: true, attributeFilter: ["open"] });
  sync();
})();
