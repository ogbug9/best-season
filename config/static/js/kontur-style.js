/* Оформление только HotelWidget: не меняет действия SDK и данные брони. */
(function () {
  "use strict";
  var modal = document.querySelector("[data-booking-modal]");
  if (!modal || typeof MutationObserver === "undefined") return;
  var pending = false;
  var descriptionId = 0;
  var selectedTariff = null;
  var calendarLayout = "";
  var calendarFrame = false;
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

  // Keep SDK-owned nodes intact; readable copies never alter provider data.
  function formatDescription(description, link, expanded) {
    var copy = description.previousElementSibling;
    if (!copy || !copy.hasAttribute("data-bs-description-copy")) copy = null;
    var walker = document.createTreeWalker(description, NodeFilter.SHOW_TEXT);
    var text = [], node;
    while ((node = walker.nextNode())) {
      if (!link || !link.contains(node)) text.push(node.nodeValue);
    }
    var source = text.join("").trim();
    if (!source) return description.id;
    if (!copy) {
      copy = document.createElement("div");
      copy.setAttribute("data-bs-description-copy", "");
      copy.id = "bs-kontur-description-copy-" + (++descriptionId);
      copy.tabIndex = 0;
      copy.setAttribute("role", "region");
      copy.setAttribute("aria-label", "Описание домика");
      description.insertAdjacentElement("beforebegin", copy);
    }
    copy.setAttribute("data-bs-description-compact", String(!expanded));
    if (!link) copy.setAttribute("data-bs-room-description", "");
    var preview = !link && !expanded;
    var sourceKey = source + (preview ? ":preview" : ":full");
    if (copy.bsDescriptionSource !== sourceKey) {
      copy.bsDescriptionSource = sourceKey;
      var lines = source.replace(/([^\n])\s+([-•])\s+(?=[А-ЯЁA-Z])/g, "$1\n$2 ")
        .split(/\r?\n/).map(function (line) { return line.trim(); }).filter(Boolean);
      if (preview) lines = lines.slice(0, 4);
      var content = document.createElement("div"), list = null;
      lines.forEach(function (line) {
        var bullet = /^[-•]\s+/.test(line);
        var text = line.replace(/^[-•]\s+/, "");
        var item;
        if (bullet) {
          if (!list) { list = document.createElement("ul"); content.appendChild(list); }
          item = document.createElement("li"); list.appendChild(item);
        } else {
          list = null;
          item = document.createElement("p"); content.appendChild(item);
          if (/:$/.test(text) && text.length < 65) item.className = "booking-description-heading";
        }
        var heading = text.match(/^([^:]{2,45}:)(?:\s+(.*)|$)/);
        if (heading) {
          var title = document.createElement("strong"); title.textContent = heading[1];
          item.append(title, document.createTextNode(heading[2] ? " " + heading[2] : ""));
        } else item.textContent = text;
      });
      copy.replaceChildren(content);
    }
    description.setAttribute("data-bs-description-formatted", "true");
    return copy.id;
  }

  function refreshCalendarLayout() {
    var calendar = modal.querySelector("#BookingCalendarWidget");
    if (!calendar || !modal.open) return;
    var width = Math.round(calendar.getBoundingClientRect().width);
    if (!width) return;
    var signature = width + ":" + calendar.childElementCount + ":" + calendar.querySelectorAll('[data-tid="Loader__Idle"]').length;
    if (signature === calendarLayout || calendarFrame) return;
    calendarFrame = true;
    requestAnimationFrame(function () { requestAnimationFrame(function () {
      calendarFrame = false;
      if (!modal.open || !calendar.isConnected) return;
      calendarLayout = Math.round(calendar.getBoundingClientRect().width) + ":" + calendar.childElementCount + ":" + calendar.querySelectorAll('[data-tid="Loader__Idle"]').length;
      window.dispatchEvent(new Event("resize"));
    }); });
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
        toggle.setAttribute("aria-controls", formatDescription(description, link, expanded));
        var caption = expanded ? "Свернуть описание" : "Подробнее";
        if (toggle.textContent !== caption) toggle.textContent = caption;
        toggle.setAttribute("aria-expanded", String(expanded));
      });
      // Room details have a plain text node instead of the SDK ShowMoreLink.
      root.querySelectorAll('.A3OQYi .K2MWTk').forEach(function (heading) {
        var description = heading.nextElementSibling;
        // A previous pass has inserted the copy immediately after the heading.
        if (description && description.hasAttribute("data-bs-description-copy")) description = description.nextElementSibling;
        if (!description || description.querySelector('[data-tid="ShowMoreLink"]')
          || description.textContent.trim().length < 200) return;
        description.setAttribute("data-bs-description", "");
        description.setAttribute("data-bs-room-description", "");
        var toggle = description.nextElementSibling;
        if (!toggle || !toggle.hasAttribute("data-bs-description-toggle")) {
          toggle = document.createElement("button");
          toggle.type = "button";
          toggle.setAttribute("data-bs-description-toggle", "");
          toggle.addEventListener("click", function () {
            var paragraph = this.previousElementSibling;
            paragraph.setAttribute("data-bs-expanded", String(this.getAttribute("aria-expanded") !== "true"));
            schedule();
          });
          description.insertAdjacentElement("afterend", toggle);
        }
        var expanded = description.getAttribute("data-bs-expanded") === "true";
        toggle.setAttribute("aria-controls", formatDescription(description, null, expanded));
        var caption = expanded ? "Свернуть описание" : "Подробнее";
        if (toggle.textContent !== caption) toggle.textContent = caption;
        toggle.setAttribute("aria-expanded", String(expanded));
      });
      root.querySelectorAll('[data-bs-description-copy]').forEach(function (copy) {
        if (!copy.nextElementSibling || !copy.nextElementSibling.hasAttribute('data-bs-description')) copy.remove();
      });
      root.querySelectorAll('[data-bs-description-toggle]').forEach(function (toggle) {
        var description = toggle.previousElementSibling;
        if (!description || !description.hasAttribute("data-bs-description")
          || (!description.hasAttribute("data-bs-room-description") && !description.querySelector('[data-tid="ShowMoreLink"]'))) toggle.remove();
      });
      root.querySelectorAll('[data-bs-comforts-toggle]').forEach(function (toggle) {
        if (!toggle.previousElementSibling || !toggle.previousElementSibling.matches('[data-tid="Comforts"]')) toggle.remove();
      });
    });
    refreshCalendarLayout();
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
        attributes: true, attributeFilter: ["disabled", "hidden"] });
      schedule();
    } else {
      pending = false;
      selectedTariff = null;
      calendarLayout = "";
    }
  }
  window.addEventListener("resize", schedule);
  new MutationObserver(sync).observe(modal, { attributes: true, attributeFilter: ["open"] });
  sync();
})();
