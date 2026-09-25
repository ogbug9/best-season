/* Блок бронирования на странице дома: выбор дат, счётчики гостей, расчёт.
 *
 * Прогрессивное улучшение. Без этого файла панель остаётся рабочей:
 * календарь и цена «от» приходят с сервера, кнопка открывает модалку
 * Контура. Скрипт добавляет выбор диапазона и пересчёт на лету.
 *
 * Разметку календаря скрипт не собирает: перелистывание и подсветка
 * приходят готовым HTML с сервера. Иначе шаблон и скрипт держали бы две
 * копии одной сетки, и однажды они бы разъехались. */
(function () {
  "use strict";

  var panel = document.querySelector("[data-booking-panel]");
  if (!panel) return;

  // Подсказка у цены: показ — стилями (:hover, :focus-within). Здесь только
  // закрытие по Esc (WCAG 1.4.13) — подсказка прячется, пока курсор или
  // фокус не уйдут с неё.
  var hint = panel.querySelector("[data-booking-hint]");
  if (hint && typeof hint.addEventListener === "function") {
    hint.addEventListener("keydown", function (event) {
      if (event.key === "Escape") hint.classList.add("is-dismissed");
    });
    hint.addEventListener("mouseleave", function () { hint.classList.remove("is-dismissed"); });
    hint.addEventListener("focusout", function () { hint.classList.remove("is-dismissed"); });
  }

  var months = panel.querySelector("[data-calendar-months]");
  var calendarUrl = panel.dataset.calendarUrl;
  var priceUrl = panel.dataset.priceUrl;
  if (!months || !calendarUrl || !priceUrl) return;

  var STORE_KEY = "booking:" + panel.dataset.house;

  var state = {
    start: "",
    dateFrom: "",
    dateTo: "",
    adults: count("adults"),
    children: count("children"),
    pets: count("pets")
  };

  var calendarRevision = 0, priceRevision = 0, pending = null;
  var activeField = "", quoteError = "";
  var calendarStatus = panel.querySelector("[data-calendar-status]");

  ["date_from", "date_to"].forEach(function (name) {
    var field = panel.querySelector('[data-input="' + name + '"]');
    if (field && validISO(field.value)) state[name === "date_from" ? "dateFrom" : "dateTo"] = field.value;
  });

  restore();
  updateGuestLabel();
  validateSelection();
  paintSelection();

  /* ---------- Выбор дат ---------- */

  // Делегирование: сетка перерисовывается целиком, и вешать обработчики
  // на каждую кнопку заново пришлось бы после каждого клика.
  months.addEventListener("click", function (event) {
    var day = event.target.closest("[data-day]");
    if (day) {
      pickDay(day.dataset.day);
      return;
    }
    var arrow = event.target.closest("[data-calendar-prev], [data-calendar-next]");
    if (arrow && arrow.dataset.start) {
      state.start = arrow.dataset.start;
      drawCalendar();
    }
  });

  function pickDay(iso) {
    if (!validISO(iso) || iso < todayISO()) return;
    if (activeField === "date_from") {
      state.dateFrom = iso;
      if (state.dateTo && state.dateTo <= iso) state.dateTo = "";
    } else if (activeField === "date_to" && state.dateFrom && iso > state.dateFrom) {
      state.dateTo = iso;
    } else if (!state.dateFrom || state.dateTo || iso <= state.dateFrom) {
      // Клик до заезда — не ошибка, а новый выбор: гость передумал
      state.dateFrom = iso;
      state.dateTo = "";
    } else {
      state.dateTo = iso;
    }
    activeField = state.dateTo ? "" : "date_to";
    save();
    paintSelection();
    recalc();
  }

  function paintSelection(preview) {
    // Selection is immediate and independent of the availability of the
    // month endpoint. Keep the existing grid and focus while picking dates.
    months.querySelectorAll("[data-calendar-date]").forEach(function (cell) {
      var iso = cell.dataset.calendarDate;
      var end = state.dateTo || (preview > state.dateFrom ? preview : "");
      var selected = iso === state.dateFrom || iso === state.dateTo;
      cell.classList.toggle("calendar__cell--selected", selected);
      cell.classList.toggle("calendar__cell--range", Boolean(state.dateFrom && end && iso > state.dateFrom && iso < end));
      cell.classList.toggle("calendar__cell--range-start", Boolean(end && iso === state.dateFrom));
      cell.classList.toggle("calendar__cell--range-end", Boolean(state.dateFrom && iso === end));
      var button = cell.querySelector("[data-day]");
      if (button) button.setAttribute("aria-pressed", String(selected));
    });
    panel.querySelectorAll("[data-field]").forEach(function (button) {
      var selected = button.dataset.field === activeField;
      button.classList.toggle("is-active", selected);
      button.setAttribute("aria-pressed", String(selected));
    });
    input("date_from", state.dateFrom);
    input("date_to", state.dateTo);
  }

  function drawCalendar(focusDate) {
    var revision = ++calendarRevision;
    months.setAttribute("aria-busy", "true");
    request(calendarUrl, { start: state.start })
      .then(function (response) { return response.text(); })
      .then(function (html) {
        if (revision !== calendarRevision) return;
        var oldFocus = document.activeElement;
        var ownedFocus = months.contains(oldFocus);
        var direction = oldFocus && oldFocus.hasAttribute("data-calendar-prev") ? "prev" : "next";
        months.innerHTML = html;
        paintSelection();
        if (calendarStatus) calendarStatus.textContent = "";
        if (ownedFocus) {
          var target = focusDate ? months.querySelector('[data-day="' + focusDate + '"]') :
            Array.from(months.querySelectorAll('[data-calendar-' + direction + ']:not([disabled])')).find(function (el) { return el.getClientRects().length; });
          if (!target) target = months.querySelector("[data-day]");
          if (target) target.focus({preventScroll: true});
        }
      })
      .catch(function () {
        if (revision === calendarRevision && calendarStatus) calendarStatus.textContent = "Не удалось загрузить месяц. Нажмите стрелку ещё раз.";
      })
      .finally(function () { if (revision === calendarRevision) months.removeAttribute("aria-busy"); });
  }

  months.addEventListener("pointerover", function (event) {
    var day = event.target.closest("[data-day]");
    if (day && state.dateFrom && !state.dateTo) paintSelection(day.dataset.day);
  });
  months.addEventListener("pointerleave", function () { paintSelection(); });
  months.addEventListener("keydown", function (event) {
    var day = event.target.closest("[data-day]");
    if (!day) return;
    if (event.key === "Escape") {
      var field = panel.querySelector('[data-field="' + (activeField || "date_from") + '"]');
      if (field) field.focus({preventScroll: true});
      return;
    }
    var date = new Date(day.dataset.day + "T12:00:00");
    var weekday = (date.getDay() + 6) % 7;
    var offsets = {ArrowLeft: -1, ArrowRight: 1, ArrowUp: -7, ArrowDown: 7, Home: -weekday, End: 6 - weekday};
    if (event.key === "PageUp" || event.key === "PageDown") {
      var number = date.getDate();
      date.setDate(1);
      date.setMonth(date.getMonth() + (event.key === "PageUp" ? -1 : 1));
      var last = new Date(date.getFullYear(), date.getMonth() + 1, 0).getDate();
      date.setDate(Math.min(number, last));
    } else if (Object.prototype.hasOwnProperty.call(offsets, event.key)) {
      date.setDate(date.getDate() + offsets[event.key]);
    } else return;
    event.preventDefault();
    var iso = localISO(date);
    if (iso < todayISO()) return;
    var target = months.querySelector('[data-day="' + iso + '"]');
    if (target && target.getClientRects().length) target.focus({preventScroll: true});
    else {
      var start = iso.slice(0, 7) + "-01";
      var limit = new Date(); limit.setDate(1); limit.setMonth(limit.getMonth() + 12);
      if (start > localISO(limit)) return;
      state.start = start;
      drawCalendar(iso);
    }
  });

  /* ---------- Счётчики гостей ---------- */

  panel.addEventListener("click", function (event) {
    var field = event.target.closest("[data-field]");
    if (field) {
      activeField = field.dataset.field;
      paintSelection();
      var selected = activeField === "date_to" ? state.dateTo || state.dateFrom : state.dateFrom;
      var target = selected && months.querySelector('[data-day="' + selected + '"]');
      if (!target || !target.getClientRects().length) target = months.querySelector("[data-day]");
      if (target) target.focus({preventScroll: true});
      return;
    }
    var step = event.target.closest("[data-step]");
    if (!step) return;
    var row = step.closest("[data-counter]");
    if (!row) return;

    var key = row.dataset.counter;
    var next = state[key] + Number(step.dataset.step);
    var min = Number(row.dataset.min);
    var max = Number(row.dataset.max);
    if (next < min || next > max) return;
    if (key !== "pets" && Number(step.dataset.step) > 0 && state.adults + state.children >= Number(panel.dataset.capacity)) return;

    state[key] = next;
    updateGuestLabel();
    row.querySelector("[data-value]").textContent = next;
    limits(row, next, min, max);
    save();
    recalc();
  });

  function updateGuestLabel() {
    ["adults", "children", "pets"].forEach(function (key) {
      var row = panel.querySelector('[data-counter="' + key + '"]');
      if (row) limits(row, state[key], Number(row.dataset.min), Number(row.dataset.max));
    });
    var total = Number(state.adults) + Number(state.children);
    var last = total % 10;
    var hundred = total % 100;
    var word = hundred >= 11 && hundred <= 14 ? "гостей"
      : last === 1 ? "гость" : last >= 2 && last <= 4 ? "гостя" : "гостей";
    text("[data-label-guests]", total + " " + word);
  }

  function limits(row, value, min, max) {
    row.querySelectorAll("[data-step]").forEach(function (button) {
      var target = value + Number(button.dataset.step);
      button.disabled = target < min || target > max || (row.dataset.counter !== "pets" && Number(button.dataset.step) > 0 && state.adults + state.children >= Number(panel.dataset.capacity));
    });
  }

  /* ---------- Расчёт ---------- */

  function recalc() {
    // Небольшая задержка: гость может нажать «плюс» несколько раз
    // подряд, и каждый клик не должен уходить отдельным запросом.
    var revision = ++priceRevision;
    quoteError = "";
    validateSelection();
    label("[data-label-date-from]", state.dateFrom, "Дата заезда");
    label("[data-label-date-to]", state.dateTo, "Дата выезда");
    text("[data-total]", "Уточняем расчёт…");
    clearTimeout(pending);
    pending = setTimeout(function () {
      request(priceUrl, {
        date_from: state.dateFrom,
        date_to: state.dateTo,
        adults: state.adults,
        children: state.children,
        pets: state.pets
      })
        .then(function (response) { return response.json(); })
        .then(function (data) { if (revision === priceRevision) render(data); })
        .catch(function () { if (revision === priceRevision) text("[data-total]", "Расчёт недоступен. Уточните стоимость при бронировании."); });
    }, 250);
  }

  function render(data) {
    text("[data-summary-nights]", data.nights_label);
    text("[data-summary-guests]", data.guests_label);

    var total = panel.querySelector("[data-total]");
    if (total) {
      total.textContent = data.total
        ? money(data.total) + " ₽"
        : "от " + money(data.price_from) + " ₽";
    }

    quoteError = data.error || "";
    validateSelection();

    label("[data-label-date-from]", data.date_from, "Дата заезда");
    label("[data-label-date-to]", data.date_to, "Дата выезда");

    input("date_from", data.date_from);
    input("date_to", data.date_to);
  }

  /* ---------- Передача выбранного в бронирование ---------- */

  // Виджет Контура не принимает даты при инициализации, поэтому
  // выбранное кладём в хранилище и подставляем в резервную форму: если
  // виджет не поднимется, гость не будет вводить даты заново.
  document.addEventListener("booking:prepare", function (event) {
    var button = event.detail.button;
    if (button.hasAttribute("data-house-id") && button.dataset.houseId !== panel.dataset.houseId) return;
    if (validateSelection()) { event.preventDefault(); return; }
    var form = document.querySelector("[data-booking-modal] [data-fallback-form] form");
    if (!form) return;
    var values = {date_from: state.dateFrom, date_to: state.dateTo,
      guests: state.adults + state.children, children: state.children,
      pets: state.pets, house: panel.dataset.houseId};
    Object.keys(values).forEach(function (key) {
      if (form.elements[key]) form.elements[key].value = values[key];
    });
  });

  function todayISO() {
    return localISO(new Date());
  }

  function localISO(now) {
    return now.getFullYear() + "-" + String(now.getMonth() + 1).padStart(2, "0") + "-" + String(now.getDate()).padStart(2, "0");
  }

  function validISO(value) {
    if (typeof value !== "string" || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return false;
    var parsed = new Date(value + "T12:00:00");
    return Number.isFinite(parsed.getTime()) && localISO(parsed) === value;
  }

  function validateSelection(serverError) {
    var error = serverError || quoteError;
    if ((state.dateFrom && !validISO(state.dateFrom)) || (state.dateTo && !validISO(state.dateTo))) error = "Выберите корректные даты в календаре.";
    if (state.adults + state.children > Number(panel.dataset.capacity)) error = "Превышена вместимость дома. Уменьшите число гостей.";
    if (state.dateFrom && state.dateFrom < todayISO()) error = "Заезд не может быть в прошлом.";
    if (state.dateTo && (!state.dateFrom || state.dateTo <= state.dateFrom)) error = "Дата выезда должна быть позже заезда.";
    if (state.dateFrom && state.dateTo && (Date.parse(state.dateTo) - Date.parse(state.dateFrom)) / 86400000 > 60) error = "Максимальный срок — 60 ночей.";
    panel.querySelectorAll("[data-booking-open]").forEach(function (button) { button.disabled = Boolean(error); });
    var note = panel.querySelector("[data-error]");
    if (note) { note.textContent = error; note.hidden = !error; }
    return error;
  }

  /* ---------- Хранилище ---------- */

  function save() {
    try {
      sessionStorage.setItem(STORE_KEY, JSON.stringify(state));
    } catch (e) {
      // Приватный режим запрещает запись — не повод ломать выбор дат
    }
  }

  function restore() {
    var saved = null;
    try {
      saved = JSON.parse(sessionStorage.getItem(STORE_KEY) || "null");
    } catch (e) {
      saved = null;
    }
    if (!saved) return;
    if ((saved.dateFrom && !validISO(saved.dateFrom)) || (saved.dateTo && !validISO(saved.dateTo))) return;

    // Прошлые даты после возврата на страницу уже не годятся
    var today = todayISO();
    if (saved.dateFrom && saved.dateFrom < today) return;

    Object.keys(state).forEach(function (key) {
      if (saved[key] !== undefined && saved[key] !== null) state[key] = saved[key];
    });

    ["adults", "children", "pets"].forEach(function (key) {
      var row = panel.querySelector('[data-counter="' + key + '"]');
      var value = Number(state[key]);
      state[key] = Number.isInteger(value) ? Math.max(Number(row.dataset.min), Math.min(value, Number(row.dataset.max))) : count(key);
    });
    if (state.dateTo && state.dateTo <= state.dateFrom) state.dateTo = "";
    if (state.dateFrom && !state.start) state.start = state.dateFrom.slice(0, 7) + "-01";

    // Счётчики в разметке пришли с сервера и о сохранённом не знают:
    // без этого на экране «0 питомцев», а сумма посчитана с питомцем.
    ["adults", "children", "pets"].forEach(function (key) {
      var row = panel.querySelector('[data-counter="' + key + '"]');
      if (!row) return;
      row.querySelector("[data-value]").textContent = state[key];
      limits(row, state[key], Number(row.dataset.min), Number(row.dataset.max));
    });

    drawCalendar();
    recalc();
  }

  /* ---------- Мелочи ---------- */

  function request(url, params) {
    var query = Object.keys(params)
      .filter(function (key) { return params[key] !== "" && params[key] !== undefined; })
      .map(function (key) {
        return encodeURIComponent(key) + "=" + encodeURIComponent(params[key]);
      })
      .join("&");
    if (state.dateFrom && url === calendarUrl) {
      query += (query ? "&" : "") + "date_from=" + state.dateFrom;
      if (state.dateTo) query += "&date_to=" + state.dateTo;
    }
    return fetch(url + (query ? "?" + query : ""), {
      headers: { "X-Requested-With": "XMLHttpRequest" }
    }).then(function (response) {
      if (response.ok === false) throw new Error("Booking request failed");
      return response;
    });
  }

  function count(key) {
    var row = panel.querySelector('[data-counter="' + key + '"] [data-value]');
    return row ? Number(row.textContent.trim()) || 0 : 0;
  }

  function text(selector, value) {
    var node = panel.querySelector(selector);
    if (node) node.textContent = value;
  }

  function input(name, value) {
    var node = panel.querySelector('[data-input="' + name + '"]');
    if (node) node.value = value || "";
  }

  function label(selector, iso, fallback) {
    if (selector === '[data-label-date-to]' && window.matchMedia('(max-width: 699px)').matches) fallback = 'выезда';
    var node = panel.querySelector(selector);
    if (!node) return;
    node.textContent = iso ? human(iso) : fallback;
  }

  var formatter = null;
  function human(iso) {
    var parts = iso.split("-");
    var date = new Date(Number(parts[0]), Number(parts[1]) - 1, Number(parts[2]));
    try {
      if (!formatter) {
        formatter = new Intl.DateTimeFormat("ru-RU", {
          day: "numeric",
          month: "long"
        });
      }
      return formatter.format(date);
    } catch (e) {
      return iso;
    }
  }

  function money(value) {
    // Неразрывный пробел, как на сервере: «8 000», а не «8000»
    return String(value || 0).replace(/\B(?=(\d{3})+(?!\d))/g, " ");
  }
})();
