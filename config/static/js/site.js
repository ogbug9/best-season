/* Минимальный скрипт сайта.

   Здесь намеренно нет фреймворка: задачи мелкие, а скорость на мобильных —
   предмет приёмки (п. 1.2 ТЗ), и библиотека ради них только утяжелила бы
   страницу. Каждый блок ниже самостоятелен и молча выключается, если своей
   разметки на странице нет.

   Виджет Контура подключается отдельно в Фазе 7.
*/

/* ---------- Липкая кнопка бронирования ----------
   Точка входа №6 из таблицы п. 5.1 ТЗ: появляется после прокрутки первого экрана. */
(function () {
  "use strict";

  var cta = document.querySelector("[data-sticky-cta]");
  if (!cta) return;

  var hero =
    document.querySelector(".hero, .house-hero, .page-hero") ||
    document.querySelector("main");
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

/* ---------- Галерея дома (п. 4.1.2) ----------
   Свёртывание и просмотрщик включает скрипт, а не разметка: при выключенном
   JS видны все кадры, и каждый остаётся обычной ссылкой на полный размер. */
(function () {
  "use strict";

  var gallery = document.querySelector("[data-gallery]");
  if (!gallery) return;

  var more = document.querySelector("[data-gallery-more]");
  if (more) {
    gallery.setAttribute("data-collapsed", "true");
    more.hidden = false;
    more.addEventListener("click", function () {
      gallery.removeAttribute("data-collapsed");
      more.hidden = true;
      var revealed = gallery.querySelector(".gallery__item--rest .gallery__link");
      if (revealed) revealed.focus();
    });
  }

  var dialog = document.querySelector("[data-lightbox]");
  var items = Array.prototype.slice.call(
    gallery.querySelectorAll("[data-gallery-item]")
  );
  // Без поддержки <dialog> просмотрщика не будет: ссылки откроют фото сами
  if (!dialog || !items.length || typeof dialog.showModal !== "function") return;

  var image = dialog.querySelector("[data-lightbox-image]");
  var caption = dialog.querySelector("[data-lightbox-caption]");
  var current = 0;
  var opener = null;

  function show(index) {
    current = (index + items.length) % items.length;
    var item = items[current];
    image.src = item.getAttribute("data-full");
    image.alt = item.getAttribute("data-caption") || "";
    caption.textContent = item.getAttribute("data-caption") || "";
  }

  items.forEach(function (item, index) {
    item.addEventListener("click", function (event) {
      event.preventDefault();
      opener = item;
      show(index);
      if (!dialog.open) dialog.showModal();
    });
  });

  dialog.querySelector("[data-lightbox-prev]").addEventListener("click", function () {
    show(current - 1);
  });
  dialog.querySelector("[data-lightbox-next]").addEventListener("click", function () {
    show(current + 1);
  });
  dialog.querySelector("[data-lightbox-close]").addEventListener("click", function () {
    dialog.close();
  });

  dialog.addEventListener("keydown", function (event) {
    if (event.key === "ArrowLeft") show(current - 1);
    if (event.key === "ArrowRight") show(current + 1);
  });

  // Клик мимо картинки закрывает просмотрщик
  dialog.addEventListener("click", function (event) {
    if (event.target === dialog) dialog.close();
  });

  // Возврат фокуса на кадр, с которого открыли — иначе с клавиатуры
  // пользователь после закрытия оказывается в начале страницы.
  // Именно на исходный, а не на текущий: текущий может быть в свёрнутой
  // части галереи и фокус тогда просто потеряется.
  dialog.addEventListener("close", function () {
    if (opener) opener.focus();
  });
})();
