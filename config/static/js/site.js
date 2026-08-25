/* Минимальный скрипт сайта.

   Здесь намеренно нет фреймворка: единственная задача — показывать липкую
   кнопку бронирования после прокрутки первого экрана (точка входа №6,
   п. 5.1 ТЗ). Тянуть ради этого библиотеку значит утяжелить страницу,
   а скорость на мобильных — предмет приёмки (п. 1.2).

   Виджет Контура подключается отдельно в Фазе 7.
*/
(function () {
  "use strict";

  var cta = document.querySelector("[data-sticky-cta]");
  if (!cta) return;

  var hero = document.querySelector(".hero") || document.querySelector("main");
  if (!hero || !("IntersectionObserver" in window)) {
    cta.setAttribute("data-visible", "true");
    return;
  }

  new IntersectionObserver(
    function (entries) {
      // Кнопка появляется, когда первый экран ушёл из вида
      cta.setAttribute("data-visible", entries[0].isIntersecting ? "false" : "true");
    },
    { rootMargin: "-10% 0px 0px 0px" }
  ).observe(hero);
})();
