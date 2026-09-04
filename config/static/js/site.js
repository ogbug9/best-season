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

  // Короткая страница (контакты, правовые, 404) прокручивается меньше чем
  // на экран — «после прокрутки первого экрана» на ней не наступает никогда,
  // и точка входа №6 из таблицы п. 5.1 просто пропала бы. Показываем сразу:
  // прокрутке кнопка не мешает, а запас снизу у подвала уже заложен в стилях.
  // Считаем не «мало ли прокрутки», а может ли первый экран вообще уйти из
  // вида: если он выше, чем экран плюс вся доступная прокрутка, наблюдатель
  // не сработает никогда и кнопка не появится ни разу.
  function heroCannotLeaveView() {
    var maxScroll = document.documentElement.scrollHeight - window.innerHeight;
    var heroBottom = hero.getBoundingClientRect().bottom + window.scrollY;
    // 10% — тот же запас, что в rootMargin наблюдателя ниже: именно
    // столько первому экрану нужно недокрутить, чтобы считаться ушедшим.
    return heroBottom > maxScroll + window.innerHeight * 0.1;
  }
  if (heroCannotLeaveView()) {
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

/* Отложенная загрузка карты.

   Карта Яндекса подставляется только по нажатию: iframe тянет чужие
   скрипты, портит замер скорости (п. 1.2 ТЗ) и отдаёт IP посетителя
   стороннему сервису ещё до того, как тот согласился (раздел 11 ТЗ).
   До нажатия на месте карты лежит обычная картинка-превью.
*/
(function () {
  "use strict";

  document.addEventListener("click", function (event) {
    var button = event.target.closest("[data-map-load]");
    if (!button) return;

    var box = button.closest("[data-map]");
    if (!box) return;

    var src = box.getAttribute("data-map-src");
    if (!src) return;

    var frame = document.createElement("iframe");
    frame.src = src;
    frame.loading = "lazy";
    frame.title = "Карта проезда";
    frame.setAttribute("allowfullscreen", "");
    frame.className = "map__frame";

    box.innerHTML = "";
    box.appendChild(frame);
  });
})();

/* Карусель фотографий в карточке домика.
   Без библиотеки: три кадра, точки, свайп и стрелки с клавиатуры.
   Без JS показывается первый слайд — карточка остаётся рабочей. */
(function () {
  document.querySelectorAll("[data-house-slider]").forEach(function (slider) {
    var slides = Array.prototype.slice.call(slider.children);
    if (slides.length < 2) return;

    var card = slider.closest(".house");
    var dots = card ? Array.prototype.slice.call(card.querySelectorAll("[data-house-dot]")) : [];
    var current = 0;

    function show(index) {
      current = (index + slides.length) % slides.length;
      slides.forEach(function (slide, i) {
        var active = i === current;
        slide.classList.toggle("is-active", active);
        if (active) slide.removeAttribute("aria-hidden");
        else slide.setAttribute("aria-hidden", "true");
      });
      dots.forEach(function (dot, i) {
        dot.classList.toggle("is-active", i === current);
        dot.setAttribute("aria-selected", i === current ? "true" : "false");
      });
    }

    dots.forEach(function (dot, i) {
      dot.addEventListener("click", function (event) {
        event.preventDefault();
        show(i);
      });
      dot.addEventListener("keydown", function (event) {
        if (event.key === "ArrowRight") { event.preventDefault(); show(current + 1); dots[current].focus(); }
        if (event.key === "ArrowLeft") { event.preventDefault(); show(current - 1); dots[current].focus(); }
      });
    });

    // Свайп на телефоне. Горизонтальный жест переключает кадр,
    // вертикальный не трогаем — иначе ломается прокрутка страницы.
    var startX = null, startY = null;
    slider.addEventListener("touchstart", function (event) {
      startX = event.touches[0].clientX;
      startY = event.touches[0].clientY;
    }, { passive: true });
    slider.addEventListener("touchend", function (event) {
      if (startX === null) return;
      var dx = event.changedTouches[0].clientX - startX;
      var dy = event.changedTouches[0].clientY - startY;
      if (Math.abs(dx) > 40 && Math.abs(dx) > Math.abs(dy)) show(current + (dx < 0 ? 1 : -1));
      startX = startY = null;
    }, { passive: true });
  });
})();
