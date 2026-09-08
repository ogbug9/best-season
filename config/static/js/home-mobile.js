/* Мобильные карусели и разделы подвала; контент доступен и без JS. */
(function () {
  'use strict';
  const mobile = window.matchMedia('(max-width: 699px)');
  const cleanups = [];

  function carousel(track, label) {
    const slides = Array.from(track.children).filter(slide => getComputedStyle(slide).display !== 'none');
    if (slides.length < 2) return;
    const originalHeight = track.style.height;
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
      if (track.classList.contains('cards--nearby')) track.style.height = `${slides[active].getBoundingClientRect().height}px`;
    }
    function onScroll() { if (!frame) frame = requestAnimationFrame(update); }
    track.addEventListener('scroll', onScroll, { passive: true });
    if (track.classList.contains('photo-mosaic__tiles')) {
      track.scrollLeft = slides[1].getBoundingClientRect().left - track.getBoundingClientRect().left - (track.clientWidth - slides[1].clientWidth) / 2;
    }
    update();
    const resize = new ResizeObserver(onScroll);
    slides.forEach(slide => resize.observe(slide));
    cleanups.push(() => { track.removeEventListener('scroll', onScroll); cancelAnimationFrame(frame); resize.disconnect(); track.style.height = originalHeight; dots.remove(); });
  }

  function sync() {
    cleanups.splice(0).forEach(cleanup => cleanup());
    if (!mobile.matches) return;
    document.querySelectorAll('.cards--houses, .cards--nearby, .photo-mosaic__tiles').forEach(track => {
      carousel(track, track.classList.contains('cards--houses') ? 'Домики' : track.classList.contains('cards--nearby') ? 'Интересное рядом' : 'Фотогалерея');
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
  sync();
})();
