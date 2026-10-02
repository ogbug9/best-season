/* Виджет Контур.Отеля — раздел 5 ТЗ.

   Порядок работы: до первого нажатия на кнопку бронирования на странице нет
   ничего от Контура — ни скрипта, ни запросов. Это прямое требование п. 5.2:
   виджет грузится по действию гостя и не влияет на замер скорости (п. 1.2).

   Если виджет не поднялся за 5 секунд или сообщил об ошибке — на его месте
   показывается резервный блок с формой заявки (п. 5.6). Резервный блок
   обязателен к сдаче и проверяется на приёмке блокировкой домена виджета,
   поэтому он не зависит от кода Контура вообще: разметка уже в странице,
   скрипт её только показывает.
*/
(function () {
  "use strict";

  var modal = document.querySelector("[data-booking-modal]");
  if (!modal) return;
  var layers = window.BookingLayers ? window.BookingLayers(modal) : null;

  // Настройки приходят из шаблона отдельным блоком JSON, а не инлайновым
  // скриптом: так значения из админки экранируются самим Django и кавычка
  // в тексте настроек не может сломать страницу.
  var config = {};
  try {
    var configNode = document.getElementById("booking-config");
    if (configNode) config = JSON.parse(configNode.textContent) || {};
  } catch (e) {
    config = {};
  }
  var host = modal.querySelector("[data-booking-host]");
  var fallback = modal.querySelector("[data-booking-fallback]");
  var spinner = modal.querySelector("[data-booking-loading]");
  var noteBox = modal.querySelector("[data-booking-note]");
  var retryButton = modal.querySelector("[data-booking-retry]");
  var help = modal.querySelector("[data-booking-help]");
  var catalog = modal.querySelector("[data-booking-catalog]");
  var selection = modal.querySelector("[data-booking-selection]");

  // Сколько ждём инициализации, прежде чем показать резервный блок — п. 5.6.1.
  var TIMEOUT_MS = 5000;
  var WIDGET_SRC = "https://bookonline24.ru/widget.js";

  var state = {
    requested: false, // скрипт уже запрошен
    ready: false, // HotelWidget.init отработал
    failed: false, // ушли в резервный сценарий
    reported: false, // о сбое уже сообщили на сервер
    entryPoint: "",
    contextHouse: null,
    timer: null,
    opener: null,
    script: null,
    attempt: 0,
    initializing: false,
    initialized: false,
    registered: false,
    initSignalled: false,
    renderObserver: null,
  };

  /* ---------- Общая аналитика сайта (п. 5.5) ---------- */
  function track(goal, params) {
    if (typeof window.bsTrack === "function") window.bsTrack(goal, params);
  }

  /* ---------- Сообщение о сбое владельцу (п. 5.6.4) ----------
     Сервер пишет событие в лог и шлёт уведомление в Telegram. Отправляем
     не чаще одного раза на страницу: если гость несколько раз нажмёт
     кнопку при лежащем Контуре, владельцу не нужен поток одинаковых
     сообщений. */
  function reportFailure(reason) {
    if (state.reported || !config.errorUrl) return;
    state.reported = true;

    try {
      var body = new FormData();
      body.append("reason", reason);
      body.append("page", window.location.pathname);
      body.append("entry_point", state.entryPoint || "");
      body.append("csrfmiddlewaretoken", config.csrfToken || "");
      // keepalive: сообщение должно уйти, даже если гость сразу закроет вкладку
      fetch(config.errorUrl, { method: "POST", body: body, keepalive: true }).catch(function () {});
    } catch (e) {
      /* не смогли сообщить — гость всё равно увидит форму заявки */
    }
  }

  /* ---------- Резервный сценарий (п. 5.6) ---------- */
  function showFallback(reason) {
    if (state.failed) return;
    state.failed = true;
    clearTimeout(state.timer);
    if (state.renderObserver) state.renderObserver.disconnect();

    if (spinner) spinner.hidden = true;
    if (host) host.hidden = true;
    if (catalog) catalog.hidden = true;
    if (noteBox) noteBox.hidden = true;
    if (fallback) fallback.hidden = false;
    if (help) help.hidden = true;
    modal.removeAttribute("aria-busy");
    if (retryButton) {
      retryButton.hidden = !config.hotelId;
      // The vendor has no verified teardown API. Never register a second
      // singleton over a partially initialized widget.
      retryButton.textContent = state.initialized ? "Перезагрузить страницу" : "Повторить загрузку";
    }

    // «Ещё не подключено» и «сломалось» — разные ситуации, и гостю они
    // должны читаться по-разному. Пустой hotelId это штатное состояние
    // до запуска, а не сбой.
    var broken = reason !== "hotel_id_missing";
    var idleNote = modal.querySelector("[data-fallback-note-idle]");
    var errorNote = modal.querySelector("[data-fallback-note-error]");
    if (idleNote) idleNote.hidden = broken;
    if (errorNote) errorNote.hidden = !broken;

    track("booking_fallback_shown", { reason: reason });
    reportFailure(reason);
  }

  function showWidget() {
    if (state.failed || state.ready || !state.registered || !state.initSignalled) return;
    // onInit confirms SDK initialization, not that a usable booking form was
    // rendered. An unavailable organization can signal init and leave empty
    // containers behind; keep the five-second fallback active in that case.
    if (!host || !host.querySelector("input, button, select, textarea, [role='button']")) return;
    state.ready = true;
    clearTimeout(state.timer);
    if (state.renderObserver) state.renderObserver.disconnect();
    if (spinner) spinner.hidden = true;
    if (host) host.hidden = false;
    if (noteBox) noteBox.hidden = false;
    if (help) help.hidden = false;
    modal.removeAttribute("aria-busy");
    track("booking_widget_ready", {});
  }

  /* ---------- Хуки виджета ----------
     ⚠️ onBooking отдаёт ФИО, телефон и почту гостя. В аналитику уходят
     только идентификатор брони и сумма: персональные данные в чужие
     системы не передаём (раздел 12 договора, раздел 11 ТЗ). */
  function bookingHooks(attempt) {
    return {
      onInit: function () {
        if (attempt !== state.attempt || state.failed) return;
        state.initSignalled = true;
        showWidget();
      },
      onError: function (error) {
        if (attempt !== state.attempt) return;
        // Vendor errors may include guest details; send only a fixed code.
        showFallback("widget_error");
      },
      onBooking: function (bookings) {
        sendBookingGoal(bookings, "booking_completed");
      },
      onHourlyBooking: function (bookings) {
        sendBookingGoal(bookings, "hourly_booking_completed");
      },
    };
  }

  function sendBookingGoal(bookings, goal) {
    var list = [].concat(bookings || []);
    var sum = 0;
    var ids = [];
    list.forEach(function (item) {
      if (!item) return;
      sum += Number(item.price) || 0;
      if (item.id) ids.push(item.id);
    });
    track(goal, {
      price: sum,
      currency: "RUB",
      bookings: ids.join(","),
      entry_point: state.entryPoint,
    });
  }

  function initWidget() {
    if (state.failed || state.ready || state.initializing || state.initialized) return;
    // The script can finish downloading after the guest has closed the dialog.
    // Defer init/add until the next opening, including the layout frame.
    if (!modal.open) return;
    if (typeof window.HotelWidget === "undefined") {
      showFallback("hotelwidget_undefined");
      return;
    }
    try {
      // Контур валидирует контейнер в момент add(). Скрытый контейнер
      // (hidden) считается недоступным, даже если модальное окно уже открыто.
      // Показываем его до регистрации виджета, а при ошибке showFallback()
      // снова скроет его.
      if (host) host.hidden = false;
      if (catalog) catalog.hidden = false;
      if (!host || !host.getClientRects().length || !host.getBoundingClientRect().width) {
        showFallback("container_not_visible");
        return;
      }
      state.initializing = true;
      state.initialized = true;
      if (typeof MutationObserver !== "undefined") {
        state.renderObserver = new MutationObserver(showWidget);
        state.renderObserver.observe(host, { childList: true, subtree: true });
      }
      window.HotelWidget.init({
        hotelId: config.hotelId,
        version: "2",
        baseUrl: "https://bookonline24.ru",
        hooks: bookingHooks(state.attempt),
      });
      if (state.failed) return;
      window.HotelWidget.add({
        type: "bookingForm",
        inline: true,
        appearance: { container: host.id },
      });
      if (state.failed) return;
      modal.querySelectorAll("[data-kontur-type]").forEach(function (container) {
        if (state.failed) return;
        if (!container.getClientRects().length || !container.getBoundingClientRect().width) {
          throw new Error("Widget container is not visible");
        }
        var widget = {
          type: container.getAttribute("data-kontur-type"),
          appearance: { container: container.id },
        };
        if (widget.type === "availabilityCalendar") widget.months = 2;
        window.HotelWidget.add(widget);
      });
      state.registered = true;
      state.initializing = false;
      showWidget();
    } catch (e) {
      showFallback("init_exception");
    }
  }

  function loadScript() {
    if (window.HotelWidget) {
      initWidget();
      return;
    }
    if (state.requested) return;
    state.requested = true;

    var script = document.createElement("script");
    var attempt = state.attempt;
    state.script = script;
    script.src = WIDGET_SRC;
    script.async = true;
    script.onload = function () {
      // setTimeout, а не requestAnimationFrame: если скрипт догрузился, пока
      // страница скрыта (гость свернул вкладку), кадр не наступит и виджет
      // не поднимется никогда. Таймер срабатывает в обоих состояниях.
      if (attempt === state.attempt && !state.failed) setTimeout(initWidget, 0);
    };
    // Сетевые ошибки загрузки скрипта. Запрет домена со стороны SDK
    // обрабатывается отдельно через onError или таймаут.
    script.onerror = function () {
      if (attempt !== state.attempt) return;
      state.requested = false;
      showFallback("script_load_failed");
    };
    document.head.appendChild(script);
  }

  /* ---------- Открытие и закрытие окна (п. 5.2) ---------- */
  function showSelection(button, panel, form, houseId) {
    if (!selection) return;
    var source = button.hasAttribute("data-house-title") ? button : panel;
    var parts = [];
    if (houseId && source) {
      var title = source.getAttribute("data-house-title");
      var category = source.getAttribute("data-pms-name");
      if (title) parts.push("Дом: " + title);
      if (category && category !== title) parts.push("Категория: " + category);
    }
    function value(name) {
      return form && form.elements[name] ? String(form.elements[name].value || "") : "";
    }
    function dateLabel(name) {
      var date = value(name);
      return /^\d{4}-\d{2}-\d{2}$/.test(date) ? date.split("-").reverse().join(".") : "";
    }
    var start = dateLabel("date_from"), end = dateLabel("date_to");
    if (start) parts.push("Заезд: " + start);
    if (end) parts.push("Выезд: " + end);
    var guests = Number(value("guests")), children = Number(value("children"));
    if (guests > 0) parts.push("Гостей: " + guests);
    if (children > 0) parts.push("Из них детей: " + children);
    var pets = Number(value("pets"));
    if (pets > 0) parts.push("Питомцев: " + pets);
    // Это памятка гостю и контекст заявки, а не параметры HotelWidget.
    // Названия из CMS вставляем как текст, чтобы они не стали HTML.
    selection.textContent = parts.length ? "Ваш выбор — " + parts.join(" · ") + "." : "";
    selection.hidden = !parts.length;
  }

  function openModal(button) {
    if (modal.open) return;
    if (button.disabled) return;
    var form = modal.querySelector("[data-fallback-form] form");
    var panel = document.querySelector("[data-booking-panel]");
    var houseId = button.hasAttribute("data-house-id")
      ? button.getAttribute("data-house-id")
      : panel && panel.dataset ? panel.dataset.houseId : "";
    var previous = {};
    if (form && houseId !== state.contextHouse) {
      ["house", "date_from", "date_to", "guests", "children", "pets"].forEach(function (name) {
        if (form.elements[name]) previous[name] = form.elements[name].value;
      });
      ["date_from", "date_to", "guests", "children", "pets"].forEach(function (name) {
        if (form.elements[name]) form.elements[name].value = "";
      });
      if (form.elements.house) form.elements.house.value = houseId || "";
    }
    var prepare = new CustomEvent("booking:prepare", {cancelable: true, detail: {button: button}});
    if (!document.dispatchEvent(prepare)) {
      Object.keys(previous).forEach(function (name) { form.elements[name].value = previous[name]; });
      return;
    }
    showSelection(button, panel, form, houseId);
    state.contextHouse = houseId;
    state.entryPoint = button.getAttribute("data-entry-point") || "";
    state.opener = button;

    track("booking_widget_open", { entry_point: state.entryPoint });

    // Прокрутку страницы фиксируем: п. 5.2 требует, чтобы при закрытии гость
    // вернулся на то же место. Без этого фон уезжает наверх на мобильных.
    document.body.style.top = "-" + window.scrollY + "px";
    document.body.setAttribute("data-modal-open", "true");
    if (typeof modal.showModal === "function") {
      modal.showModal();
    } else {
      modal.setAttribute("open", "");
    }
    if (layers) layers.open();

    if (state.failed || state.ready) return;

    if (!config.hotelId) {
      // Идентификатор ещё не заведён в настройках сайта: ждать нечего,
      // сразу показываем форму заявки. Гость всё равно может обратиться.
      showFallback("hotel_id_missing");
      return;
    }

    startLoading();
  }

  function startLoading() {
    clearTimeout(state.timer);
    if (spinner) spinner.hidden = false;
    if (host) host.hidden = false;
    modal.setAttribute("aria-busy", "true");
    var attempt = state.attempt;
    state.timer = setTimeout(function countdown() {
      if (attempt !== state.attempt || state.failed || state.ready) return;
      // Пока страница не на экране, отсчёт не идёт: гость свернул вкладку или
      // переключился в другое приложение, и «не успели за 5 секунд» к его
      // опыту отношения не имеет. Досчитываем, когда он вернётся — п. 5.6.1
      // про ожидание гостя, а не про время в фоне.
      if (document.visibilityState === "hidden") {
        state.timer = setTimeout(countdown, TIMEOUT_MS);
        return;
      }
      showFallback("timeout_5s");
    }, TIMEOUT_MS);
    // Раньше загрузка висела на requestAnimationFrame. Пока страница не
    // перерисовывается (фоновая вкладка, свёрнутое окно, переключение
    // приложения на телефоне), rAF не вызывается вообще: скрипт Контура не
    // запрашивался НИ РАЗУ, а таймер при этом шёл и через 5 секунд показывал
    // «онлайн-бронирование временно недоступно» — плюс уходило ложное
    // уведомление владельцу о сбое. Кадр здесь не нужен: loadScript только
    // добавляет <script>, а проверка размеров контейнера живёт в initWidget
    // и отрабатывает на скрытой странице тоже (замер: 1161×100 при
    // visibilityState === "hidden"). Сам скрипт грузится за ~55 мс.
    setTimeout(function () {
      if (attempt === state.attempt && modal.open && !state.failed) loadScript();
    }, 0);
  }

  function retry() {
    if (!state.failed || !modal.open) return;
    if (state.initialized) {
      // A page reload is the only verified way to reset the vendor singleton.
      window.location.reload();
      return;
    }
    state.attempt += 1;
    state.failed = false;
    state.requested = false;
    if (state.script) {
      state.script.onload = null;
      state.script.onerror = null;
      state.script.remove();
      state.script = null;
    }
    // Do not replace the fallback DOM: typed values survive load retries.
    if (fallback) fallback.hidden = true;
    if (noteBox) noteBox.hidden = false;
    startLoading();
  }

  function closeModal() {
    if (layers && !layers.close()) return;
    clearTimeout(state.timer);
    var offset = Math.abs(parseInt(document.body.style.top || "0", 10)) || 0;
    document.body.removeAttribute("data-modal-open");
    document.body.style.top = "";
    window.scrollTo(0, offset);
    // preventScroll обязателен: браузер подкручивает страницу к элементу,
    // который получает фокус, и без этого гость улетает к кнопке в первом
    // экране вместо того места, где закрыл окно (п. 5.2 ТЗ).
    if (state.opener) {
      try {
        state.opener.focus({ preventScroll: true });
      } catch (e) {
        state.opener.focus();
      }
    }
  }

  document.addEventListener("click", function (event) {
    var opener = event.target.closest("[data-booking-open]");
    if (opener) {
      event.preventDefault();
      openModal(opener);
      return;
    }
    if (event.target.closest("[data-booking-close]")) {
      if (typeof modal.close === "function") modal.close();
      else {
        modal.removeAttribute("open");
        closeModal();
      }
    }
    if (event.target.closest("[data-booking-retry]")) retry();
    if (event.target.closest("[data-booking-request]")) {
      if (fallback) fallback.hidden = false;
      var idle = modal.querySelector("[data-fallback-note-idle]");
      var error = modal.querySelector("[data-fallback-note-error]");
      if (idle) idle.hidden = false;
      if (error) error.hidden = true;
      var field = fallback && fallback.querySelector("input:not([type='hidden'])");
      if (field) field.focus();
    }
  });

  // close срабатывает и на Esc, и на кнопке — восстановление прокрутки
  // вешаем сюда, чтобы не дублировать в двух местах.
  modal.addEventListener("close", closeModal);
  modal.addEventListener("cancel", function (event) {
    // Let the SDK handle Esc for its active popup, including before the next frame.
    if (layers && layers.ownsPopup()) event.preventDefault();
  });

  // Клик по подложке закрывает окно. Проверяем именно сам <dialog>:
  // у него подложка — это его собственная площадь вне содержимого.
  modal.addEventListener("click", function (event) {
    if (event.target === modal && typeof modal.close === "function") modal.close();
  });

})();
