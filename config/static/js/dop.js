/* Интерактив доп. страниц (docs/dop-stranicy): планировщик дня, чек-лист,
   калькуляторы выходных, отмены, питомца и компании. Каждый виджет
   ищется по своему data-атрибуту; без JS страница остаётся читаемой. */
(function () {
  "use strict";

  function money(value) {
    return String(Math.round(value)).replace(/\B(?=(\d{3})+(?!\d))/g, " ") + " ₽";
  }
  function plural(n, one, few, many) {
    var m10 = n % 10, m100 = n % 100;
    if (m10 === 1 && m100 !== 11) return one;
    if (m10 >= 2 && m10 <= 4 && (m100 < 10 || m100 >= 20)) return few;
    return many;
  }
  function isoDate(date) {
    var tz = date.getTimezoneOffset() * 60000;
    return new Date(date - tz).toISOString().slice(0, 10);
  }
  function store(key, value) {
    try {
      if (value === undefined) return JSON.parse(window.localStorage.getItem(key) || "null");
      window.localStorage.setItem(key, JSON.stringify(value));
    } catch (_) { return null; }
  }

  /* ---------- Планировщик дня: «Интересное рядом» ---------- */
  Array.prototype.forEach.call(document.querySelectorAll("[data-dayplan]"), function (box) {
    var day = box.querySelector("[data-dayplan-day]");
    var out = box.querySelector("[data-dayplan-out]");
    var checks = box.querySelectorAll("[data-plan-item]");
    var names = ["понедельник", "вторник", "среду", "четверг", "пятницу", "субботу", "воскресенье"];
    if (day && day.value === "") day.value = String((new Date().getDay() + 6) % 7);

    function render() {
      var weekday = parseInt(day.value, 10);
      var chosen = [], closed = [], minutes = 0;
      Array.prototype.forEach.call(checks, function (input) {
        var days = input.getAttribute("data-days").split(",").map(Number);
        var card = input.closest("[data-guide-card]");
        var open = days.indexOf(weekday) !== -1;
        if (card) card.classList.toggle("is-closed", !open);
        if (!input.checked) return;
        var title = input.getAttribute("data-title");
        chosen.push(title);
        minutes = Math.max(minutes, parseInt(input.getAttribute("data-minutes"), 10) || 0);
        if (!open) closed.push(title);
      });
      if (!chosen.length) {
        out.innerHTML = "Отметьте места — соберём день и предупредим, если что-то закрыто в " + names[weekday] + ".";
        return;
      }
      var html = "<b>Ваш день, " + names[weekday] + ":</b> " + chosen.join(" → ") + ".";
      html += " Дальше всего ехать ≈" + minutes + " мин в одну сторону.";
      if (closed.length) html += ' <span class="dayplan__warn">Закрыто в этот день: ' + closed.join(", ") + ".</span>";
      else html += " Всё открыто — хорошего дня!";
      out.innerHTML = html;
    }
    box.addEventListener("change", render);
    render();
  });

  /* ---------- Чек-лист «что взять» (запоминается в браузере) ---------- */
  Array.prototype.forEach.call(document.querySelectorAll("[data-checklist]"), function (list) {
    var key = "bs-checklist-" + list.getAttribute("data-checklist");
    var saved = store(key) || {};
    var counter = list.querySelector("[data-checklist-count]");
    var inputs = list.querySelectorAll("input[type=checkbox]");
    function count() {
      var done = Array.prototype.filter.call(inputs, function (i) { return i.checked; }).length;
      if (counter) counter.textContent = done + " из " + inputs.length;
    }
    Array.prototype.forEach.call(inputs, function (input) {
      input.checked = !!saved[input.value];
      input.addEventListener("change", function () {
        saved[input.value] = input.checked;
        store(key, saved);
        count();
      });
    });
    count();
  });

  /* ---------- Калькулятор выходных: «Доп. услуги» ---------- */
  Array.prototype.forEach.call(document.querySelectorAll("[data-weekend-calc]"), function (form) {
    var out = form.querySelector("[data-weekend-out]");
    var start = form.elements.date_from;
    if (start && !start.value) {
      var friday = new Date();
      friday.setDate(friday.getDate() + ((5 - friday.getDay() + 7) % 7 || 7));
      start.value = isoDate(friday);
      start.min = isoDate(new Date());
    }
    var timer = null;
    function render() {
      clearTimeout(timer);
      timer = setTimeout(function () {
        var house = form.elements.house.value;
        var nights = parseInt(form.elements.nights.value, 10) || 1;
        var from = new Date(form.elements.date_from.value);
        if (!house || isNaN(from)) return;
        var to = new Date(from); to.setDate(to.getDate() + nights);
        var params = new URLSearchParams({
          date_from: form.elements.date_from.value, date_to: isoDate(to),
          adults: form.elements.adults.value, children: 0, pets: form.elements.pets.value,
        });
        out.textContent = "Считаем…";
        fetch("/api/domik/" + house + "/raschet/?" + params, { headers: { Accept: "application/json" } })
          .then(function (r) { return r.json(); })
          .then(function (data) {
            if (data.error) { out.textContent = data.error; return; }
            var banya = (parseInt(form.elements.banya.value, 10) || 0) * (parseInt(form.getAttribute("data-banya"), 10) || 0);
            var besedka = (parseInt(form.elements.besedka.value, 10) || 0) * (parseInt(form.getAttribute("data-besedka"), 10) || 0);
            var total = data.total + banya + besedka;
            out.innerHTML = "<span>Домик: " + money(data.total) + " за " + data.nights_label + "</span>" +
              (banya ? "<span>Баня: " + money(banya) + "</span>" : "") +
              (besedka ? "<span>Беседка: " + money(besedka) + "</span>" : "") +
              "<b>Итого ≈ " + money(total) + "</b><span>Предоплата 50%: " + money(total / 2) + "</span>";
          })
          .catch(function () { out.textContent = "Не получилось посчитать — откройте окно брони или напишите нам."; });
      }, 250);
    }
    form.addEventListener("input", render);
    form.addEventListener("submit", function (event) { event.preventDefault(); render(); });
    render();
  });

  /* ---------- Калькулятор отмены и питомца: «Правила бронирования» ---------- */
  Array.prototype.forEach.call(document.querySelectorAll("[data-cancel-calc]"), function (form) {
    var out = form.querySelector("[data-cancel-out]");
    if (!form.elements.cancel_date.value) form.elements.cancel_date.value = isoDate(new Date());
    function render() {
      var arrival = new Date(form.elements.arrival.value);
      var cancel = new Date(form.elements.cancel_date.value);
      var paid = parseFloat(form.elements.paid.value) || 0;
      if (isNaN(arrival) || isNaN(cancel)) { out.textContent = "Укажите дату заезда."; return; }
      var days = Math.round((arrival - cancel) / 86400000);
      if (days < 0) { out.textContent = "Дата отмены позже заезда — проверьте даты."; return; }
      var share = days >= 7 ? 1 : days >= 4 ? 0.5 : 0;
      var text = "До заезда " + days + " " + plural(days, "день", "дня", "дней") + ": вернём " + share * 100 + "% предоплаты";
      if (paid) text += " — " + money(paid * share);
      out.textContent = text + ".";
    }
    form.addEventListener("input", render);
    render();
  });
  Array.prototype.forEach.call(document.querySelectorAll("[data-pet-calc]"), function (form) {
    var out = form.querySelector("[data-pet-out]");
    function render() {
      var fee = parseInt(form.elements.size.value, 10) || 0;
      var nights = parseInt(form.elements.nights.value, 10) || 1;
      out.textContent = "Доплата за питомца: " + money(fee * nights) + " за " + nights + " " + plural(nights, "ночь", "ночи", "ночей") + ".";
    }
    form.addEventListener("input", render);
    render();
  });

  /* ---------- Сколько домиков нужно: «Выезды компаний» ---------- */
  Array.prototype.forEach.call(document.querySelectorAll("[data-group-calc]"), function (form) {
    var out = form.querySelector("[data-group-out]");
    function render() {
      var guests = parseInt(form.elements.guests.value, 10) || 0;
      if (guests < 1) { out.textContent = ""; return; }
      var houses = Math.ceil(guests / 4);
      var text;
      if (houses <= 4) {
        text = guests + " " + plural(guests, "гость", "гостя", "гостей") + " — " + houses + " " + plural(houses, "домик", "домика", "домиков") + " на ночь.";
        text += houses === 4 ? " Это весь глэмпинг — тариф «Только свои»." : " Можно занять и весь глэмпинг, чтобы рядом никого не было.";
      } else {
        text = "На ночь размещаем до 16 гостей (4 домика по 4). Днём в беседке «Корабль» — до 50 гостей: остальные могут приехать на праздник без ночёвки.";
      }
      out.textContent = text;
    }
    form.addEventListener("input", render);
    render();
  });
})();

/* ---------- «Когда едете?»: приглушить то, что не работает в выбранный месяц ---------- */
(function () {
  "use strict";
  Array.prototype.forEach.call(document.querySelectorAll("[data-month-dim]"), function (select) {
    var hint = select.parentElement.querySelector("[data-month-out]");
    function render() {
      var tag = "m" + select.value, off = 0;
      Array.prototype.forEach.call(document.querySelectorAll("[data-months]"), function (item) {
        var available = (" " + item.getAttribute("data-months") + " ").indexOf(" " + tag + " ") !== -1;
        item.classList.toggle("is-off-season", !available);
        if (!available) off += 1;
      });
      if (hint) hint.textContent = off ? "Приглушено то, что в этом месяце не работает." : "В этом месяце доступно всё.";
    }
    select.addEventListener("change", render);
    render();
  });
})();
