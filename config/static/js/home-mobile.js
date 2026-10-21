/* Мобильные карусели и разделы подвала; контент доступен и без JS. */
(function () {
  'use strict';
  const mobile = window.matchMedia('(max-width: 699px)');
  const cleanups = [];
  const breaks = Array.from(document.querySelectorAll('.home-mobile-copy br, .mobile-catalog-services__intro br, .equipment__list br'));
  const spaces = breaks.map(() => document.createTextNode(' '));
  const fixedParagraphs = Array.from(document.querySelectorAll('[data-preserve-breaks] p, [data-fit-nearby-copy]')).map(paragraph => {
    const lines = [''];
    paragraph.childNodes.forEach(node => {
      if (node.nodeName === 'BR') lines.push('');
      else lines[lines.length - 1] += node.textContent;
    });
    return { paragraph, lines };
  });
  const measure = document.createElement('canvas').getContext('2d');
  function syncBreaks() {
    const narrow = document.documentElement.clientWidth < 390;
    breaks.forEach((br, index) => {
      const preserve = br.closest('[data-preserve-breaks]') || spaces[index].parentElement?.closest('[data-preserve-breaks]');
      if (narrow && !preserve && br.isConnected) br.replaceWith(spaces[index]);
      else if (!narrow && spaces[index].isConnected) spaces[index].replaceWith(br);
    });
    fixedParagraphs.forEach(({ paragraph, lines }) => {
      const reserve = paragraph.hasAttribute('data-fit-nearby-copy') ? 1 : 4;
      const width = Math.min(paragraph.clientWidth - reserve, Number(paragraph.dataset.lineWidth) || Infinity);
      if (!mobile.matches || width <= 0 || !measure) return;
      const style = getComputedStyle(paragraph);
      measure.font = `${style.fontStyle} ${style.fontWeight} ${style.fontSize} ${style.fontFamily}`;
      const tracking = parseFloat(style.letterSpacing) || 0;
      const length = text => measure.measureText(text).width + tracking * Math.max(0, text.length - 1);
      let fitted = lines;
      if (lines.some(line => length(line.trimEnd()) > width)) {
        // Переносим весь абзац: остаток строки не становится отдельным словом.
        // Исходные пробелы внутри строк, включая двойные, сохраняются.
        const words = lines.map(line => line.trimEnd()).join(' ').trim().match(/\S+\s*/g) || [];
        const referenceEnds = new Set();
        let count = 0;
        lines.forEach(line => { count += (line.match(/\S+/g) || []).length; referenceEnds.add(count); });
        const best = Array(words.length + 1).fill(null);
        best[0] = { cost: 0, start: -1 };
        for (let start = 0; start < words.length; start++) {
          if (!best[start]) continue;
          let text = '';
          for (let end = start + 1; end <= words.length; end++) {
            text += words[end - 1];
            const size = length(text.trimEnd());
            if (size > width) break;
            if (end - start === 1 && words.length > 1) continue;
            const cost = best[start].cost + width * width * words.length
              + (width - size) ** 2 + (referenceEnds.has(end) ? 0 : width * width / 4);
            if (!best[end] || cost < best[end].cost) best[end] = { cost, start };
          }
        }
        if (best[words.length]) {
          fitted = [];
          for (let end = words.length; end > 0;) {
            const start = best[end].start;
            fitted.unshift(words.slice(start, end).join('').trimEnd());
            end = start;
          }
        }
      }
      paragraph.replaceChildren(...fitted.flatMap((line, index) => index
        ? [document.createElement('br'), document.createTextNode(line)] : [document.createTextNode(line)]));
    });
  }
  window.addEventListener('resize', syncBreaks);
  document.fonts?.ready.then(syncBreaks);
  syncBreaks();

  // Один доступный паттерн для подвала и комплектации домиков.
  function disclosure(title, links, id, temporary = true) {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'footer__toggle';
    button.textContent = title.textContent;
    const oldId = links.id;
    const oldHidden = links.hidden;
    links.id = id;
    button.setAttribute('aria-controls', id);
    button.setAttribute('aria-expanded', 'false');
    links.hidden = true;
    button.addEventListener('click', () => {
      const opening = links.hidden;
      // 06.10: в подвале, как в мобильном меню, раскрыт только один раздел.
      const group = opening && button.closest('.footer__columns');
      if (group) {
        group.querySelectorAll('.footer__toggle[aria-expanded="true"]').forEach(other => {
          if (other === button) return;
          other.setAttribute('aria-expanded', 'false');
          const list = document.getElementById(other.getAttribute('aria-controls'));
          if (list) list.hidden = true;
        });
      }
      links.hidden = !opening;
      button.setAttribute('aria-expanded', String(opening));
    });
    const original = Array.from(title.childNodes);
    title.replaceChildren(button);
    if (temporary) cleanups.push(() => { links.hidden = oldHidden; links.id = oldId; title.replaceChildren(...original); });
  }

  // Комплектация раскрывается по группам на любой ширине, как на мобильной.
  document.querySelectorAll('.equipment').forEach((equipment, index) => {
    equipment.classList.add('equipment--accordion');
    equipment.querySelectorAll('.equipment__title').forEach((title, group) => {
      const list = title.nextElementSibling;
      if (list) disclosure(title, list, `equipment-${index}-${group}`, false);
    });
  });

  const header = document.querySelector('.header');
  const menu = header?.querySelector('.nav-toggle');
  let previousY = window.scrollY;
  let scrollFrame = 0;
  function updateHeader() {
    scrollFrame = 0;
    const y = Math.max(0, Math.min(window.scrollY, document.documentElement.scrollHeight - window.innerHeight));
    const pinned = !mobile.matches || menu?.open || header?.querySelector(':focus-visible') ||
      document.body.hasAttribute('data-modal-open') || document.querySelector('dialog[open]');
    if (pinned || y <= header?.offsetHeight) {
      header?.classList.remove('header--hidden');
      previousY = y;
    } else if (Math.abs(y - previousY) >= 8) {
      header?.classList.toggle('header--hidden', y > previousY);
      previousY = y;
    }
  }
  window.addEventListener('scroll', () => {
    if (!scrollFrame) scrollFrame = requestAnimationFrame(updateHeader);
  }, { passive: true });
  header?.addEventListener('focusin', updateHeader);
  menu?.addEventListener('toggle', updateHeader);
  menu?.addEventListener('keydown', event => {
    if (event.key === 'Escape' && menu.open) {
      menu.open = false;
      menu.querySelector('summary')?.focus();
      event.preventDefault();
    }
  });
  mobile.addEventListener('change', updateHeader);

  function carousel(track, label) {
    const slides = Array.from(track.children).filter(slide => getComputedStyle(slide).display !== 'none');
    if (slides.length < 2) return;
    const originalHeight = track.style.height;
    const heads = slides.map(slide => slide.querySelector('.place__head')).filter(Boolean);
    const originalHeadHeights = heads.map(head => head.style.minHeight);
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
    // Для мест высоту всех слайдов выравнивает flex: она остаётся общей
    // при свайпе и автоматически уменьшается после переноса текста.
    // Фиксированный размер сохраняем только у ряда отзывов.
    function fixHeight() {
      if (!track.matches('.cards--nearby, .reviews')) return;
      track.style.height = '';
      heads.forEach((head, index) => { head.style.minHeight = originalHeadHeights[index]; });
      const headHeight = heads.reduce((max, head) => Math.max(max, head.getBoundingClientRect().height), 0);
      heads.forEach(head => { head.style.minHeight = `${headHeight}px`; });
      if (track.classList.contains('reviews')) {
        const tallest = slides.reduce((max, slide) => Math.max(max, slide.getBoundingClientRect().height), 0);
        if (tallest) track.style.height = `${tallest}px`;
      }
    }
    function onScroll() { if (!frame) frame = requestAnimationFrame(update); }
    track.addEventListener('scroll', onScroll, { passive: true });
    if (loop) loop.start(); else if (track.classList.contains('photo-mosaic__tiles')) {
      track.scrollLeft = slides[1].getBoundingClientRect().left - track.getBoundingClientRect().left - (track.clientWidth - slides[1].clientWidth) / 2;
    }
    fixHeight();
    update();
    let active = true;
    function refresh() { if (active) { fixHeight(); onScroll(); } }
    const resize = new ResizeObserver(refresh);
    slides.forEach(slide => resize.observe(slide));
    heads.forEach(head => resize.observe(head.querySelector('.place__title')));
    if (heads.length) document.fonts?.ready.then(refresh);
    cleanups.push(() => {
      active = false;
      track.removeEventListener('scroll', onScroll);
      cancelAnimationFrame(frame);
      resize.disconnect();
      track.style.height = originalHeight;
      heads.forEach((head, index) => { head.style.minHeight = originalHeadHeights[index]; });
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
    cleanups.splice(0).reverse().forEach(cleanup => cleanup());
    if (!mobile.matches) return;
    const photoTrack = document.querySelector('.photo-mosaic__tiles');
    const firstPhoto = photoTrack?.querySelector('[data-mobile-gallery-first]');
    if (firstPhoto) {
      const originalPhotos = Array.from(photoTrack.children);
      photoTrack.prepend(firstPhoto);
      cleanups.push(() => photoTrack.replaceChildren(...originalPhotos));
    }
    document.querySelectorAll('.amenity-tags').forEach(tags => {
      const items = Array.from(tags.children);
      const columns = [0, 1].map(() => {
        const column = document.createElement('li');
        column.className = 'amenity-tags__column';
        const list = document.createElement('ul');
        list.className = 'amenity-tags__column-items';
        column.append(list);
        return column;
      });
      items.forEach((item, index) => columns[index % 2].firstElementChild.append(item));
      tags.replaceChildren(...columns);
      cleanups.push(() => tags.replaceChildren(...items));
    });
    const tracks = document.body.matches('.page-home, .page-houses, .page-promotions, .page-house, .page-nearby, .page-reviews')
      ? document.querySelectorAll('.cards--houses, .cards--nearby, .photo-mosaic__tiles, .house-mosaic:not(.house-mosaic--empty), .reviews') : [];
    tracks.forEach(track => {
      carousel(track, track.classList.contains('cards--houses') ? 'Домики' : track.classList.contains('cards--nearby') ? 'Интересное рядом' : track.classList.contains('reviews') ? 'Отзывы' : 'Фотогалерея');
    });
    document.querySelectorAll('.footer__column-title').forEach((title, index) => {
      const links = title.nextElementSibling;
      if (!links) return;
      disclosure(title, links, `mobile-footer-links-${index}`);
    });
  }
  mobile.addEventListener('change', sync);
  document.querySelector('[data-mobile-gallery-open]')?.addEventListener('click', () => {
    document.querySelector('.house-mosaic [data-gallery-item]')?.click();
  });
  sync();
})();
