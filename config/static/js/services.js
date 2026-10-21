/* Страница услуг (docs/dop-stranicy/11-uslugi.md): предварительный расчёт часов.
   Почасовые объекты бронируются в виджете Контура — здесь только оценка суммы. */
(function () {
  "use strict";
  var MIN = 1, MAX = 12;

  function money(value) {
    return String(value).replace(/\B(?=(\d{3})+(?!\d))/g, "\u00a0") + "\u00a0₽";
  }

  Array.prototype.forEach.call(document.querySelectorAll("[data-hours]"), function (box) {
    var price = parseInt(box.getAttribute("data-price"), 10) || 0;
    var hours = MIN;
    var value = box.querySelector("[data-hours-value]");
    var total = box.querySelector("[data-hours-total]");
    var minus = box.querySelector('[data-hours-step="-1"]');
    var plus = box.querySelector('[data-hours-step="1"]');

    function render() {
      value.textContent = hours + " ч";
      total.textContent = money(price * hours);
      minus.disabled = hours <= MIN;
      plus.disabled = hours >= MAX;
    }

    box.addEventListener("click", function (event) {
      var step = event.target.closest("[data-hours-step]");
      if (!step) return;
      hours = Math.min(MAX, Math.max(MIN, hours + parseInt(step.getAttribute("data-hours-step"), 10)));
      render();
    });
    render();
  });
})();
