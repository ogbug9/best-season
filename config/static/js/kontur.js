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

  // Сколько ждём инициализации, прежде чем показать резервный блок — п. 5.6.1.
  var TIMEOUT_MS = 5000;
  var WIDGET_SRC = "https://bookonline24.ru/widget.js";

  var state = {
    requested: false, // скрипт уже запрошен
    ready: false, // HotelWidget.init отработал
    failed: false, // ушли в резервный сценарий
    reported: false, // о сбое уже сообщили на сервер
    entryPoint: "",
    timer: null,
    opener: null,
  };

  /* ---------- Аналитика точек входа (п. 5.5) ----------
     Метрика может быть не подключена — тогда просто молчим. Слой данных
     заполняем всегда: он пригодится, если счётчик поставят позже. */
  function track(goal, params) {
    window.dataLayer = window.dataLayer || [];
    window.dataLayer.push({ event: goal, params: params || {} });

    var counter = config.metrikaId;
    if (!counter || typeof window.ym !== "function") return;
    try {
      window.ym(Number(counter), "reachGoal", goal, params || {});
    } catch (e) {
      /* аналитика не должна ломать бронирование */
    }
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
      fetch(config.errorUrl, { method: "POST", body: body, keepalive: true });
    } catch (e) {
      /* не смогли сообщить — гость всё равно увидит форму заявки */
    }
  }

  /* ---------- Резервный сценарий (п. 5.6) ---------- */
  function showFallback(reason) {
    if (state.failed) return;
    state.failed = true;
    clearTimeout(state.timer);

    if (spinner) spinner.hidden = true;
    if (host) host.hidden = true;
    if (noteBox) noteBox.hidden = true;
    if (fallback) fallback.hidden = false;

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
    state.ready = true;
    clearTimeout(state.timer);
    if (spinner) spinner.hidden = true;
    if (host) host.hidden = false;
    if (noteBox) noteBox.hidden = false;
    track("booking_widget_ready", {});
  }

  /* ---------- Хуки виджета ----------
     ⚠️ onBooking отдаёт ФИО, телефон и почту гостя. В аналитику уходят
     только идентификатор брони и сумма: персональные данные в чужие
     системы не передаём (раздел 12 договора, раздел 11 ТЗ). */
  function bookingHooks() {
    return {
      onInit: function () {
        showWidget();
      },
      onError: function (error) {
        var text = "";
        try {
          text = String((error && (error.message || error.code)) || error || "");
        } catch (e) {
          text = "unknown";
        }
        showFallback("widget_error: " + text.slice(0, 200));
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

  /* ---------- Тема виджета (п. 5.4.1) ----------
     Настраиваем то, что Контур разрешает настраивать. Шрифт в моделях темы
     не предусмотрен вовсе — типографика виджета останется системной, это
     зафиксированное ограничение. */
  function widgetTheme() {
    return {
      common: {
        btnBackgroundColor: config.colorAccent || "#9B5026",
        btnTextColor: config.colorLight || "#F7F0E6",
        btnBorderRadius: 100,
        inputBorderRadius: 10,
        modalBorderRadius: 20,
        // По умолчанию у Контура 425px, а п. 5.2 ТЗ требует полный экран
        // до 768px. Поднимаем порог до требования ТЗ — проверить вживую,
        // когда придёт hotelId: параметр влияет на лайтбоксы виджета,
        // наше собственное окно и так раскрывается на весь экран.
        modalAdaptiveThreshold: 768,
      },
    };
  }

  function initWidget() {
    if (typeof window.HotelWidget === "undefined") {
      showFallback("hotelwidget_undefined");
      return;
    }
    try {
      window.HotelWidget.init({
        hotelId: config.hotelId,
        version: "2",
        baseUrl: "https://bookonline24.ru",
        hooks: bookingHooks(),
        theme: widgetTheme(),
      });
      window.HotelWidget.add({
        type: "bookingForm",
        appearance: { container: host.id, inline: false },
      });
      // Подстраховка: если Контур почему-то не позовёт onInit, но разметку
      // всё же вставит — считаем виджет живым, как только в контейнере
      // что-то появилось.
      setTimeout(function () {
        if (!state.ready && !state.failed && host.children.length) showWidget();
      }, 1200);
    } catch (e) {
      showFallback("init_exception");
    }
  }

  function loadScript() {
    if (state.requested) return;
    state.requested = true;

    var script = document.createElement("script");
    script.src = WIDGET_SRC;
    script.async = true;
    script.onload = initWidget;
    // Домен заблокирован, нет сети, домен сайта не добавлен в разрешённые
    // у Контура — во всех случаях сюда. Ждать оставшиеся секунды таймера
    // незачем, гость получает форму заявки сразу.
    script.onerror = function () {
      showFallback("script_load_failed");
    };
    document.head.appendChild(script);
  }

  /* ---------- Открытие и закрытие окна (п. 5.2) ---------- */
  function openModal(button) {
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

    if (state.failed || state.ready) return;

    if (!config.hotelId) {
      // Идентификатор ещё не заведён в настройках сайта: ждать нечего,
      // сразу показываем форму заявки. Гость всё равно может обратиться.
      showFallback("hotel_id_missing");
      return;
    }

    if (spinner) spinner.hidden = false;
    state.timer = setTimeout(function () {
      showFallback("timeout_5s");
    }, TIMEOUT_MS);
    loadScript();
  }

  function closeModal() {
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
      else modal.removeAttribute("open");
    }
  });

  // close срабатывает и на Esc, и на кнопке — восстановление прокрутки
  // вешаем сюда, чтобы не дублировать в двух местах.
  modal.addEventListener("close", closeModal);

  // Клик по подложке закрывает окно. Проверяем именно сам <dialog>:
  // у него подложка — это его собственная площадь вне содержимого.
  modal.addEventListener("click", function (event) {
    if (event.target === modal && typeof modal.close === "function") modal.close();
  });

  /* ---------- Цель на отправку резервной формы (п. 5.6.3) ---------- */
  var fallbackForm = modal.querySelector("[data-fallback-form] form, form[data-fallback-form]");
  if (fallbackForm) {
    fallbackForm.addEventListener("submit", function () {
      track("booking_fallback_submitted", { entry_point: state.entryPoint });
    });
  }
})();
