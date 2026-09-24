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

  restore();
  updateGuestLabel();
  validateSelection();

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
    if (!state.dateFrom || state.dateTo || iso <= state.dateFrom) {
      // Клик до заезда — не ошибка, а новый выбор: гость передумал
      state.dateFrom = iso;
      state.dateTo = "";
    } else {
      state.dateTo = iso;
    }
    save();
    drawCalendar();
    recalc();
  }

  function drawCalendar() {
    var revision = ++calendarRevision;
    request(calendarUrl, { start: state.start })
      .then(function (response) { return response.text(); })
      .then(function (html) { if (revision === calendarRevision) months.innerHTML = html; })
      .catch(function () { /* сеть отвалилась — на экране остаётся прежний месяц */ });
  }

  /* ---------- Счётчики гостей ---------- */

  panel.addEventListener("click", function (event) {
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

    validateSelection(data.error || "");
    var error = panel.querySelector("[data-error]");
    if (error) {
      error.textContent = data.error || "";
      error.hidden = !data.error;
    }

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
    var now = new Date();
    return now.getFullYear() + "-" + String(now.getMonth() + 1).padStart(2, "0") + "-" + String(now.getDate()).padStart(2, "0");
  }

  function validateSelection(serverError) {
    var error = serverError || "";
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
