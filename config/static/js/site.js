/* Минимальный скрипт сайта.

   Здесь намеренно нет фреймворка: задачи мелкие, а скорость на мобильных —
   предмет приёмки (п. 1.2 ТЗ), и библиотека ради них только утяжелила бы
   страницу. Каждый блок ниже самостоятелен и молча выключается, если своей
   разметки на странице нет.

   Виджет Контура подключается отдельно в Фазе 7.
*/

/* ---------- Цвет закреплённой шапки ---------- */
(function () {
  'use strict';
  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
  var animations = new WeakMap();
  function set(item, open) {
    var button = item.querySelector('.faq__question');
    var answer = item.querySelector('.faq__answer');
    var previous = animations.get(answer);
    var height = answer.hidden ? 0 : answer.getBoundingClientRect().height;
    if (previous) previous.cancel();
    button.setAttribute('aria-expanded', String(open));
    item.classList.toggle('is-open', open);
    answer.hidden = false;
    if (reduced.matches || !answer.animate) { answer.hidden = !open; return; }
    var animation = answer.animate([
      {height: height + 'px', opacity: height ? 1 : 0},
      {height: (open ? answer.scrollHeight : 0) + 'px', opacity: open ? 1 : 0}
    ], {duration: 200, easing: 'ease-out'});
    animations.set(answer, animation);
    animation.onfinish = function () {
      answer.hidden = button.getAttribute('aria-expanded') !== 'true';
      animations.delete(answer);
    };
  }
  document.querySelectorAll('.faq').forEach(function (faq) {
    faq.querySelectorAll('.faq__question').forEach(function (button) {
      button.addEventListener('click', function () {
        var item = button.closest('.faq__item');
        var open = button.getAttribute('aria-expanded') !== 'true';
        if (open) faq.querySelectorAll('.faq__item.is-open').forEach(function (other) { if (other !== item) set(other, false); });
        set(item, open);
      });
    });
  });
  // Ссылка на конкретный ответ (#q-12): администратор присылает её гостю,
  // ответ раскрывается сам (docs/dop-stranicy/17-faq.md).
  function openFromHash() {
    var id = decodeURIComponent(window.location.hash.slice(1));
    if (!/^q-\d+$/.test(id)) return;
    var item = document.getElementById(id);
    if (!item || !item.classList.contains('faq__item')) return;
    item.hidden = false;
    item.classList.remove('is-fading');
    item.closest('.faq').querySelectorAll('.faq__item.is-open').forEach(function (other) { if (other !== item) set(other, false); });
    if (!item.classList.contains('is-open')) set(item, true);
    item.scrollIntoView({block: 'start', behavior: reduced.matches ? 'auto' : 'smooth'});
  }
  openFromHash();
  window.addEventListener('hashchange', openFromHash);
})();

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
    // Перед возвратом к герою оставляем 120 px обычной прокрутки вверх.
    if (direction < 0 && y > 1 && y <= boundary - 120) return 0;
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

/* ---------- Заявки на акции: существующие FeedbackForm/CertificateForm ---------- */
(function () {
  'use strict';
  var modal = document.querySelector('[data-promotion-request-modal]');
  var panel = document.querySelector('[data-promotion-request-panel]');
  if (!modal || !panel || typeof modal.showModal !== 'function') return;
  var opener = null;
  modal.appendChild(panel);
  document.addEventListener('click', function (event) {
    var button = event.target.closest('[data-promotion-request-open]');
    if (!button) return;
    var type = button.getAttribute('data-form-type');
    var selected = panel.querySelector('[data-promotion-form="' + type + '"]');
    if (!selected) return;
    event.preventDefault();
    opener = button;
    var topic = button.getAttribute('data-topic') || '';
    panel.querySelector('[data-promotion-request-title]').textContent = topic;
    panel.querySelectorAll('[data-promotion-form]').forEach(function (form) {
      form.hidden = form !== selected;
    });
    selected.querySelector('[name="topic"]').value = topic;
    document.body.setAttribute('data-modal-open', '');
    if (!modal.open) modal.showModal();
  });
  modal.querySelector('[data-promotion-request-close]').addEventListener('click', function () { modal.close(); });
  modal.addEventListener('click', function (event) { if (event.target === modal) modal.close(); });
  modal.addEventListener('close', function () {
    if (!document.querySelector('dialog[open]')) document.body.removeAttribute('data-modal-open');
    if (opener) opener.focus();
  });
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
  // Галерея (docs/dop-stranicy/14-galereya.md): счётчик «3 / 18» и переход
  // на домик; листаются только фото, не скрытые фильтром.
  var counter = dialog.querySelector("[data-lightbox-counter]");
  var link = dialog.querySelector("[data-lightbox-link]");
  var list = items;
  var current = 0;
  var opener = null;

  function visible() {
    return items.filter(function (item) { return !item.closest("[hidden]"); });
  }

  function show(index) {
    current = (index + list.length) % list.length;
    var item = list[current];
    image.src = item.getAttribute("data-full");
    image.alt = item.getAttribute("data-caption") || "";
    caption.textContent = item.getAttribute("data-caption") || "";
    if (counter) counter.textContent = list.length > 1 ? (current + 1) + " / " + list.length : "";
    if (link) {
      var href = item.getAttribute("data-link");
      link.hidden = !href;
      if (href) { link.href = href; link.textContent = item.getAttribute("data-link-label") || ""; }
    }
  }

  items.forEach(function (item) {
    item.addEventListener("click", function (event) {
      event.preventDefault();
      opener = item;
      list = visible();
      show(list.indexOf(item));
      if (!dialog.open) dialog.showModal();
    });
  });

  function animateStep(button) {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    button.classList.remove('is-stepping');
    void button.offsetWidth;
    button.classList.add('is-stepping');
  }
  dialog.querySelectorAll('.lightbox__nav').forEach(function (button) {
    button.addEventListener('animationend', function (event) { if (event.target === button) button.classList.remove('is-stepping'); });
  });
  dialog.querySelector("[data-lightbox-prev]").addEventListener("click", function (event) {
    show(current - 1);
    animateStep(event.currentTarget);
  });
  dialog.querySelector("[data-lightbox-next]").addEventListener("click", function (event) {
    show(current + 1);
    animateStep(event.currentTarget);
  });
  dialog.querySelector("[data-lightbox-close]").addEventListener("click", function () {
    dialog.close();
  });

  dialog.addEventListener("keydown", function (event) {
    if (event.key === "ArrowLeft") show(current - 1);
    if (event.key === "ArrowRight") show(current + 1);
  });

  var swipeStart = null;
  image.addEventListener('pointerdown', function (event) {
    if (event.pointerType !== 'touch') return;
    swipeStart = { x: event.clientX, y: event.clientY, id: event.pointerId };
    image.setPointerCapture(event.pointerId);
  });
  image.addEventListener('pointerup', function (event) {
    if (!swipeStart || swipeStart.id !== event.pointerId) return;
    var dx = event.clientX - swipeStart.x;
    var dy = event.clientY - swipeStart.y;
    swipeStart = null;
    if (Math.abs(dx) < 40 || Math.abs(dx) <= Math.abs(dy)) return;
    show(current + (dx < 0 ? 1 : -1));
  });
  image.addEventListener('pointercancel', function () { swipeStart = null; });

  // Только фон за рамкой закрывает окно; клики по кремовым полям его не закрывают.
  dialog.addEventListener("click", function (event) {
    if (event.target !== dialog) return;
    var box = dialog.getBoundingClientRect();
    if (event.clientX < box.left || event.clientX > box.right || event.clientY < box.top || event.clientY > box.bottom) dialog.close();
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

/* Фото карточек: ссылка, точки, drag/swipe и автолистание раз в 3 с. */
(function () {
  "use strict";
  document.querySelectorAll("[data-house-slider]").forEach(function (slider) {
    var slides = Array.prototype.slice.call(slider.children);
    if (slides.length < 2) return;
    var card = slider.closest(".house");
    var dots = Array.prototype.slice.call(card.querySelectorAll("[data-house-dot]"));
    var current = 0, start = null, suppressClick = false, timer = 0;
    var reduced = window.matchMedia("(prefers-reduced-motion: reduce)");
    function show(index) {
      current = (index + slides.length) % slides.length;
      slides.forEach(function (slide, i) {
        slide.classList.toggle("is-active", i === current);
        slide.setAttribute("aria-hidden", String(i !== current));
      });
      dots.forEach(function (dot, i) {
        dot.classList.toggle("is-active", i === current);
        dot.setAttribute("aria-selected", String(i === current));
        dot.tabIndex = i === current ? 0 : -1;
      });
    }
    function restart() {
      window.clearTimeout(timer);
      if (reduced.matches || document.hidden) return;
      timer = window.setTimeout(function tick() {
        // Не менять снимок во время чтения/перетаскивания или клавиатурного выбора.
        if (!start && !card.matches(':hover') && !card.querySelector(':focus-visible') && card.getBoundingClientRect().bottom > 0 && card.getBoundingClientRect().top < window.innerHeight) show(current + 1);
        timer = window.setTimeout(tick, 3000);
      }, 3000);
    }
    dots.forEach(function (dot, i) {
      dot.addEventListener("click", function (event) {
        event.preventDefault(); show(i); restart();
        // Pointer-переключение не оставляет фокус/увеличение на старой точке.
        if (event.detail > 0) dot.blur();
      });
      dot.addEventListener("keydown", function (event) {
        if (event.key !== "ArrowRight" && event.key !== "ArrowLeft") return;
        event.preventDefault(); show(current + (event.key === "ArrowRight" ? 1 : -1)); dots[current].focus(); restart();
      });
    });
    slider.addEventListener('dragstart', function (event) { event.preventDefault(); });
    slider.addEventListener('pointerdown', function (event) {
      if (!event.isPrimary || event.button !== 0) return;
      suppressClick = false;
      start = { x: event.clientX, y: event.clientY, id: event.pointerId, mouse: event.pointerType === 'mouse' };
    });
    slider.addEventListener('pointermove', function (event) {
      if (!start || event.pointerId !== start.id) return;
      var dx = event.clientX - start.x, dy = event.clientY - start.y;
      if (Math.abs(dx) > 12 && Math.abs(dx) > Math.abs(dy)) {
        suppressClick = true;
        if (start.mouse) slider.setPointerCapture(event.pointerId);
      }
    });
    slider.addEventListener('pointerup', function (event) {
      if (!start || event.pointerId !== start.id) return;
      var dx = event.clientX - start.x, dy = event.clientY - start.y;
      if (start.mouse && Math.abs(dx) > 40 && Math.abs(dx) > Math.abs(dy)) show(current + (dx < 0 ? 1 : -1));
      start = null; restart();
    });
    slider.addEventListener('pointercancel', function () { start = null; });
    slider.addEventListener('click', function (event) {
      if (suppressClick) { event.preventDefault(); suppressClick = false; }
    });
    document.addEventListener('visibilitychange', restart);
    reduced.addEventListener('change', restart);
    show(0); restart();
  });
})();

/* Карточки «Наша территория» на тач-устройствах.

   На десктопе описание и кнопка появляются при наведении, чистым CSS.
   Наведения на телефоне нет, поэтому там то же состояние включает
   нажатие: первый тап раскрывает карточку, второй (по ней или по кнопке
   «Подробнее») уводит на страницу. Тап по кнопке до карточки не
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
      // 06.10: второй тап по раскрытой карточке ведёт туда же, куда «Подробнее»
      var link = card.querySelector(".territory-card__link[href]");
      if (card.classList.contains("is-open") && link) { link.click(); return; }
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

/* Выезжающее меню: закрытие перед бронированием, Escape и цикл фокуса. */
(function () {
  var menu = document.querySelector('.nav-toggle');
  if (!menu) return;
  var toggle = menu.querySelector(':scope > summary');
  menu.querySelectorAll('.nav-section').forEach(function (section) {
    section.addEventListener('toggle', function () {
      if (!section.open) return;
      menu.querySelectorAll('.nav-section').forEach(function (other) {
        if (other !== section) other.open = false;
      });
    });
  });
  var inert = new Map();
  function sync() {
    var open = menu.open && window.matchMedia('(max-width: 1279px)').matches;
    document.body.classList.toggle('menu-open', open);
    document.querySelectorAll('main, .footer, [data-sticky-cta]').forEach(function (el) {
      if (open) { if (!inert.has(el)) inert.set(el, el.inert); el.inert = true; }
      else if (inert.has(el)) { el.inert = inert.get(el); inert.delete(el); }
    });
    toggle.setAttribute('aria-label', open ? 'Закрыть меню' : 'Меню');
  }
  menu.addEventListener('toggle', sync);
  menu.addEventListener('click', function (event) {
    if (event.target.closest('a, [data-booking-open]')) { menu.open = false; sync(); }
  });
  menu.addEventListener('keydown', function (event) {
    if (!menu.open) return;
    if (event.key === 'Escape') { menu.open = false; sync(); toggle.focus(); event.preventDefault(); }
    if (event.key !== 'Tab') return;
    var targets = Array.prototype.filter.call(menu.querySelectorAll('summary, a, button'), function (el) { return el.getClientRects().length; });
    var first = targets[0], last = targets[targets.length - 1];
    if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
    else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
  });
  window.matchMedia('(max-width: 1279px)').addEventListener('change', function () { menu.open = false; sync(); });
})();
(function () {
  // Assign a stable type; responsive CSS never chooses a different state.
  var selector = 'button, summary, .btn, [role="button"], a.socials__item';
  function assign(button) {
    if (button.hasAttribute('data-button-type') || button.closest('.kontur-host, .react-ui, .yarl__portal')) return;
    var type;
    if (button.matches('.hero .searchbar--cta-only, .hero .searchbar__cta')) type = 'c';
    else if (button.matches('.house__book, .territory-card__link')) type = 'd';
    else if (button.matches('.promo__book, .place__more, .about-pet__details > summary, .lightbox__nav')) type = 'e';
    else if (button.matches('.house__more')) type = 'f';
    else if (button.matches('.btn--outline, .btn--ghost, .socials__item')) type = 'b';
    else if (button.matches('.searchbar')) type = 'a';
    else {
      var style = getComputedStyle(button), background = style.backgroundColor;
      if (background === 'rgb(132, 127, 87)') type = 'd';
      else if (/^rgb\((155, 80, 38|35, 35, 35|73, 73, 73)\)$/.test(background)) type = 'a';
      else if (background === 'rgba(0, 0, 0, 0)') type = /247, 240, 230|255, 255, 255/.test(style.borderColor) && parseFloat(style.borderWidth) > 0 ? 'f' : 'b';
      else type = 'e';
    }
    button.dataset.buttonType = type;
    button.classList.add('button--type-' + type);
  }
  function scan(root) {
    if (root.nodeType !== 1) return;
    if (root.matches(selector)) assign(root);
    root.querySelectorAll(selector).forEach(assign);
  }
  scan(document.body);
  new MutationObserver(function (records) {
    records.forEach(function (record) { record.addedNodes.forEach(scan); });
  }).observe(document.body, { childList: true, subtree: true });
  document.addEventListener('touchstart', function () {}, { passive: true });
})();
(function () {
  var pressed = null;
  function release() {
    if (pressed) pressed.targets.forEach(function (button) { button.classList.remove('is-pressed'); });
    pressed = null;
  }
  document.addEventListener('pointerdown', function (event) {
    if (event.pointerType !== 'touch') return;
    var button = event.target.closest('[data-button-type]');
    if (!button || button.closest('.kontur-host, .react-ui, .yarl__portal, :disabled, [aria-disabled="true"]')) return;
    button = button.closest('button[data-button-type]') || button;
    release();
    var targets = [button].concat(Array.from(button.querySelectorAll('.btn[data-button-type]')));
    pressed = { targets: targets, id: event.pointerId, x: event.clientX, y: event.clientY };
    targets.forEach(function (target) { target.classList.add('is-pressed'); });
  }, { passive: true });
  document.addEventListener('pointermove', function (event) {
    if (pressed && event.pointerId === pressed.id && Math.hypot(event.clientX - pressed.x, event.clientY - pressed.y) > 12) release();
  }, { passive: true });
  ['pointerup', 'pointercancel'].forEach(function (name) {
    document.addEventListener(name, function (event) { if (pressed && event.pointerId === pressed.id) release(); }, { passive: true });
  });
  window.addEventListener('blur', release);
})();
