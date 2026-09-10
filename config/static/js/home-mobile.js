/* Мобильные карусели и разделы подвала; контент доступен и без JS. */
(function () {
  'use strict';
  if (!document.body.matches('.page-home, .page-houses, .page-promotions, .page-house')) return;
  const mobile = window.matchMedia('(max-width: 699px)');
  const cleanups = [];

  function carousel(track, label) {
    const slides = Array.from(track.children).filter(slide => getComputedStyle(slide).display !== 'none');
    if (slides.length < 2) return;
    const originalHeight = track.style.height;
    const loop = track.classList.contains('photo-mosaic__tiles') ? makeLoop(track, slides) : null;
    const dots = document.createElement('div');
    dots.className = 'mobile-carousel-dots';
    dots.setAttribute('role', 'group');
    dots.setAttribute('aria-label', label);
    const buttons = slides.map((slide, index) => {
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'mobile-carousel-dot';
      button.setAttribute('aria-label', `${label}: ${index + 1}`);
      button.addEventListener('click', () => {
        const centered = track.classList.contains('photo-mosaic__tiles');
        track.scrollTo({
          left: track.scrollLeft + slide.getBoundingClientRect().left - track.getBoundingClientRect().left - (centered ? (track.clientWidth - slide.clientWidth) / 2 : 0),
          behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth'
        });
      });
      dots.append(button);
      return button;
    });
    track.after(dots);
    let frame = 0;
    function update() {
      frame = 0;
      const box = track.getBoundingClientRect();
      const center = box.left + box.width / 2;
      let active = 0;
      let distance = Infinity;
      slides.forEach((slide, index) => {
        const rect = slide.getBoundingClientRect();
        const delta = Math.abs(rect.left + rect.width / 2 - center);
        if (delta < distance) { distance = delta; active = index; }
      });
      buttons.forEach((button, index) => button.setAttribute('aria-current', String(index === active)));
    }
    // Высоту ряда закрепляем по самой высокой карточке и один раз.
    // Раньше она пересчитывалась под текущий слайд на каждом кадре
    // прокрутки, и при горизонтальном свайпе карточка ездила вверх-вниз.
    function fixHeight() {
      if (!track.matches('.cards--nearby, .reviews')) return;
      track.style.height = '';
      const tallest = slides.reduce((max, slide) => Math.max(max, slide.getBoundingClientRect().height), 0);
      if (tallest) track.style.height = `${tallest}px`;
    }
    function onScroll() { if (!frame) frame = requestAnimationFrame(update); }
    track.addEventListener('scroll', onScroll, { passive: true });
    if (loop) loop.start(); else if (track.classList.contains('photo-mosaic__tiles')) {
      track.scrollLeft = slides[1].getBoundingClientRect().left - track.getBoundingClientRect().left - (track.clientWidth - slides[1].clientWidth) / 2;
    }
    fixHeight();
    update();
    const resize = new ResizeObserver(() => { fixHeight(); onScroll(); });
    slides.forEach(slide => resize.observe(slide));
    cleanups.push(() => {
      track.removeEventListener('scroll', onScroll);
      cancelAnimationFrame(frame);
      resize.disconnect();
      track.style.height = originalHeight;
      dots.remove();
      if (loop) loop.stop();
    });
  }

  /* Бесконечная прокрутка фотогалереи: с последнего кадра свайп идёт на
     первый и наоборот. Библиотеки нет, поэтому по краям ряда лежат
     копии крайних кадров, а когда прокрутка на них останавливается,
     позиция без анимации переставляется на настоящий кадр.
     Лишние кадры (в мобильном макете их прячет nth-child) на время
     вынимаем из разметки: иначе копии сдвинули бы нумерацию правил. */
  function makeLoop(track, slides) {
    if (slides.length < 2) return null;
    const hidden = Array.from(track.children).filter(item => !slides.includes(item));
    const marks = hidden.map(item => {
      const mark = document.createComment('');
      item.replaceWith(mark);
      return mark;
    });
    const head = slides[0].cloneNode(true);
    const tail = slides[slides.length - 1].cloneNode(true);
    [head, tail].forEach(clone => {
      clone.setAttribute('aria-hidden', 'true');
      clone.dataset.clone = 'true';
    });
    track.prepend(tail);
    track.append(head);
    track.classList.add('is-loop');

    function offsetOf(slide) {
      return track.scrollLeft + slide.getBoundingClientRect().left - track.getBoundingClientRect().left
        - (track.clientWidth - slide.clientWidth) / 2;
    }
    function jump(slide) {
      const behavior = track.style.scrollBehavior;
      const snap = track.style.scrollSnapType;
      // Снятый snap обязателен: с ним браузер возвращает прокрутку
      // обратно на копию, и переход выглядит как рывок туда-обратно.
      track.style.scrollSnapType = 'none';
      track.style.scrollBehavior = 'auto';
      track.scrollLeft = offsetOf(slide);
      track.style.scrollBehavior = behavior;
      track.style.scrollSnapType = snap;
    }
    let timer = 0;
    function onScroll() {
      clearTimeout(timer);
      timer = setTimeout(() => {
        const box = track.getBoundingClientRect();
        const center = box.left + box.width / 2;
        const near = item => Math.abs(item.getBoundingClientRect().left + item.getBoundingClientRect().width / 2 - center) < item.clientWidth / 2;
        if (near(head)) jump(slides[0]);
        else if (near(tail)) jump(slides[slides.length - 1]);
      }, 120);
    }
    return {
      start() {
        track.addEventListener('scroll', onScroll, { passive: true });
        jump(slides[0]);
      },
      stop() {
        clearTimeout(timer);
        track.removeEventListener('scroll', onScroll);
        track.classList.remove('is-loop');
        head.remove();
        tail.remove();
        marks.forEach((mark, index) => mark.replaceWith(hidden[index]));
      }
    };
  }

  function sync() {
    cleanups.splice(0).forEach(cleanup => cleanup());
    if (!mobile.matches) return;
    document.querySelectorAll('.cards--houses, .cards--nearby, .photo-mosaic__tiles, .house-mosaic:not(.house-mosaic--empty), .reviews').forEach(track => {
      carousel(track, track.classList.contains('cards--houses') ? 'Домики' : track.classList.contains('cards--nearby') ? 'Интересное рядом' : track.classList.contains('reviews') ? 'Отзывы' : 'Фотогалерея');
    });
    document.querySelectorAll('.footer__column-title').forEach((title, index) => {
      const links = title.nextElementSibling;
      if (!links) return;
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'footer__toggle';
      button.textContent = title.textContent;
      const oldId = links.id;
      links.id = `mobile-footer-links-${index}`;
      button.setAttribute('aria-controls', links.id);
      button.setAttribute('aria-expanded', 'false');
      links.hidden = true;
      button.addEventListener('click', () => {
        links.hidden = !links.hidden;
        button.setAttribute('aria-expanded', String(!links.hidden));
      });
      const original = Array.from(title.childNodes);
      title.replaceChildren(button);
      cleanups.push(() => { links.hidden = false; links.id = oldId; title.replaceChildren(...original); });
    });
  }
  mobile.addEventListener('change', sync);
  document.querySelector('[data-mobile-gallery-open]')?.addEventListener('click', () => {
    document.querySelector('.house-mosaic [data-gallery-item]')?.click();
  });
  sync();
})();
