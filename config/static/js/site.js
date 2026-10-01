/* Минимальный скрипт сайта.

   Здесь намеренно нет фреймворка: задачи мелкие, а скорость на мобильных —
   предмет приёмки (п. 1.2 ТЗ), и библиотека ради них только утяжелила бы
   страницу. Каждый блок ниже самостоятелен и молча выключается, если своей
   разметки на странице нет.

   Виджет Контура подключается отдельно в Фазе 7.
*/

/* ---------- Цвет закреплённой шапки ---------- */
(function () {
  "use strict";
  var header = document.querySelector('.header');
  if (!header) return;
  var frame = 0;
  function update() {
    frame = 0;
    header.classList.toggle('header--scrolled', window.scrollY > header.offsetHeight);
  }
  window.addEventListener('scroll', function () {
    if (!frame) frame = window.requestAnimationFrame(update);
  }, { passive: true });
  window.addEventListener('pageshow', update);
  update();
})();

/* ---------- Переход с первого экрана главной ---------- */
(function () {
  "use strict";

  if (!document.body.classList.contains("page-home")) return;
  var hero = document.querySelector(".hero");
  var next = document.querySelector(".home-after-hero");
  if (!hero || !next) return;

  var sliding = false;
  var slideStartedAt = 0;
  var slideReleaseTimer = null;
  var touchStart = null;
  var wheelIntent = window.BSScrollIntent();
  var reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

  function targetFor(direction) {
    // Если содержимое первого экрана выше окна, оставляем обычную прокрутку:
    // прыжок иначе скрыл бы часть текста на небольшом телефоне.
    if (hero.getBoundingClientRect().height > window.innerHeight + 2) return null;
    var boundary = next.getBoundingClientRect().top + window.scrollY;
    var y = window.scrollY;
    if (direction > 0 && y < boundary - 2) return boundary;
    if (direction < 0 && y > 1 && y <= boundary + Math.min(120, window.innerHeight * 0.15)) return 0;
    return null;
  }

  function scheduleRelease() {
    window.clearTimeout(slideReleaseTimer);
    var now = window.performance.now();
    var delay = Math.max(slideStartedAt + 700, now + 250) - now;
    slideReleaseTimer = window.setTimeout(function () { sliding = false; }, delay);
  }

  function slideTo(y) {
    sliding = true;
    slideStartedAt = window.performance.now();
    wheelIntent.block(slideStartedAt);
    window.scrollTo({ top: Math.round(y), behavior: reducedMotion.matches ? "instant" : "smooth" });
    scheduleRelease();
  }

  function isBlocked(event) {
    return document.body.hasAttribute("data-modal-open") ||
      (event.target.closest && event.target.closest("dialog[open], .react-ui"));
  }

  window.addEventListener("wheel", function (event) {
    if (event.ctrlKey || event.metaKey || Math.abs(event.deltaX) > Math.abs(event.deltaY) || isBlocked(event)) return;
    if (sliding) { event.preventDefault(); scheduleRelease(); return; }
    var target = targetFor(Math.sign(event.deltaY));
    if (target === null) { wheelIntent.reset(); return; }
    event.preventDefault();
    var delta = event.deltaY * (event.deltaMode === 1 ? 16 : event.deltaMode === 2 ? window.innerHeight : 1);
    if (wheelIntent.push(delta, window.performance.now())) slideTo(target);
  }, { passive: false });

  window.addEventListener("touchstart", function (event) {
    if (event.touches.length !== 1 || isBlocked(event) ||
        (targetFor(1) === null && targetFor(-1) === null)) return;
    touchStart = { x: event.touches[0].clientX, y: event.touches[0].clientY };
  }, { passive: true });

  window.addEventListener("touchmove", function (event) {
    if (!touchStart || event.touches.length !== 1) return;
    var dx = touchStart.x - event.touches[0].clientX;
    var dy = touchStart.y - event.touches[0].clientY;
    if (Math.abs(dy) >= 80 && Math.abs(dy) > Math.abs(dx) &&
        (sliding || targetFor(Math.sign(dy)) !== null) && event.cancelable) {
      event.preventDefault();
    }
  }, { passive: false });

  window.addEventListener("touchend", function (event) {
    if (!touchStart || !event.changedTouches.length) return;
    var dx = touchStart.x - event.changedTouches[0].clientX;
    var dy = touchStart.y - event.changedTouches[0].clientY;
    touchStart = null;
    if (sliding || Math.abs(dy) < 80 || Math.abs(dy) <= Math.abs(dx)) return;
    var target = targetFor(Math.sign(dy));
    if (target !== null) slideTo(target);
  }, { passive: true });
  window.addEventListener("touchcancel", function () { touchStart = null; }, { passive: true });

  document.addEventListener("keydown", function (event) {
    if (event.defaultPrevented || event.ctrlKey || event.metaKey || event.altKey || isBlocked(event) ||
        (event.target.closest && event.target.closest("a, button, input, select, textarea, summary, [contenteditable]"))) return;
    var direction = 0;
    if (event.key === "ArrowDown" || event.key === "PageDown" || event.key === " ") direction = event.shiftKey ? -1 : 1;
    if (event.key === "ArrowUp" || event.key === "PageUp") direction = -1;
    if (!direction) return;
    if (sliding) { event.preventDefault(); scheduleRelease(); return; }
    var target = targetFor(direction);
    if (target === null) return;
    event.preventDefault();
    slideTo(target);
  });
})();

/* ---------- Липкая кнопка бронирования ----------
   Точка входа №6 из таблицы п. 5.1 ТЗ: появляется после прокрутки первого экрана. */
(function () {
  "use strict";

  var cta = document.querySelector("[data-sticky-cta]");
  if (!cta) return;

  var heroGone = false;
  var inlineVisible = false;
  function updateSticky(gone) {
    heroGone = gone;
    cta.setAttribute("data-visible", heroGone && !inlineVisible ? "true" : "false");
  }
  var inlineCta = document.querySelector("[data-house-booking-cta]");
  if (inlineCta && "IntersectionObserver" in window) {
    new IntersectionObserver(function (entries) {
      inlineVisible = entries[0].isIntersecting;
      updateSticky(heroGone);
    }).observe(inlineCta);
  }

  var hero =
    document.querySelector(".hero, .house-hero, .page-hero") ||
    document.querySelector("main");
  if (!hero || !("IntersectionObserver" in window)) {
    updateSticky(true);
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
    updateSticky(true);
    return;
  }

  new IntersectionObserver(
    function (entries) {
      // Кнопка появляется, когда первый экран ушёл из вида
      updateSticky(!entries[0].isIntersecting);
    },
    { rootMargin: "-10% 0px 0px 0px" }
  ).observe(hero);
})();

/* ---------- Уведомление о cookie ---------- */
(function () {
  "use strict";
  var banner = document.querySelector("[data-cookie-banner]");
  if (!banner) return;
  var key = "bs-cookie-consent-v1";
  var choice = null;
  try { choice = window.localStorage.getItem(key); } catch (_) {}
  if (!choice) banner.hidden = false;

  function finish(value) {
    try { window.localStorage.setItem(key, value); } catch (_) {}
    banner.hidden = true;
    document.dispatchEvent(new CustomEvent("bs:cookie-consent", { detail: value }));
  }
  banner.querySelector("[data-cookie-accept]").addEventListener("click", function () {
    finish("accepted");
  });
  banner.querySelector("[data-cookie-close]").addEventListener("click", function () {
    finish("dismissed");
  });
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
  var galleryScope = gallery.closest('.house-mosaic-section') || gallery;
  var items = Array.prototype.slice.call(
    galleryScope.querySelectorAll("[data-gallery-item]")
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
      // На мобильной главной свайп листает домики; фотографии — по точкам.
      if (document.body.matches(".page-home, .page-houses") && window.matchMedia("(max-width: 699px)").matches) return;
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

/* Карточки «Наша территория» на тач-устройствах.

   На десктопе описание и кнопка появляются при наведении, чистым CSS.
   Наведения на телефоне нет, поэтому там то же состояние включает
   нажатие: первый тап раскрывает карточку, второй по кнопке
   «Подробнее» уводит на страницу. Тап по кнопке до карточки не
   всплывает — иначе первое же нажатие и раскрывало бы, и уводило. */
(function () {
  "use strict";

  var cards = document.querySelectorAll(".territory-card");
  if (!cards.length) return;
  if (!window.matchMedia) return;
  var touchLayout = window.matchMedia("(hover: none), (max-width: 699px)");

  function close(except) {
    cards.forEach(function (card) {
      if (card !== except) {
        card.classList.remove("is-open");
        card.setAttribute("aria-expanded", "false");
      }
    });
  }

  cards.forEach(function (card) {
    card.setAttribute("aria-expanded", "false");

    card.addEventListener("click", function (event) {
      if (!touchLayout.matches) return;
      // Ссылка внутри карточки работает сама: раскрытие ей не мешает
      if (event.target.closest("a, button")) return;
      var open = !card.classList.contains("is-open");
      close(card);
      card.classList.toggle("is-open", open);
      card.setAttribute("aria-expanded", String(open));
    });

    card.addEventListener("keydown", function (event) {
      if (event.key !== "Enter" && event.key !== " ") return;
      if (event.target !== card) return;
      event.preventDefault();
      card.click();
    });
  });

  // Нажатие мимо карточек закрывает раскрытую
  document.addEventListener("click", function (event) {
    if (!event.target.closest(".territory-card")) close(null);
  });
  touchLayout.addEventListener("change", function () { close(null); });
})();
