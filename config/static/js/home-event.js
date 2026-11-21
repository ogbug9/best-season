(() => {
  const banner = document.querySelector('[data-home-event]');
  const hero = document.querySelector('.page-home .hero');
  if (!banner || !hero) return;

  const storageKey = `home-event-dismissed:${banner.dataset.homeEvent}`;
  try {
    if (sessionStorage.getItem(storageKey)) {
      banner.hidden = true;
      return;
    }
  } catch {
    // Закрытие работает и при недоступном хранилище.
  }

  const observer = new IntersectionObserver(([entry]) => {
    banner.classList.toggle('is-visible', !entry.isIntersecting && entry.boundingClientRect.bottom <= 0);
  });
  observer.observe(hero);

  const close = banner.querySelector('.home-event__close');
  close.hidden = false;
  close.addEventListener('click', () => {
    banner.hidden = true;
    observer.disconnect();
    try {
      sessionStorage.setItem(storageKey, '1');
    } catch {
      // Баннер уже закрыт на текущей странице.
    }
  });
})();
