(function () {
  'use strict';
  var small = window.matchMedia('(max-width: 699px)');
  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
  // The 1.4 MB desktop artwork is fetched only where it is shown (≥700 px), never on phones.
  var art = document.querySelector('[data-about-art]');
  var wide = window.matchMedia('(min-width: 700px)');
  function loadArt() {
    if (!art || !wide.matches || art.dataset.loaded) return;
    art.dataset.loaded = 'true';
    fetch(art.dataset.aboutArt).then(function (response) {
      if (!response.ok) throw new Error(response.status);
      return response.text();
    }).then(function (svg) {
      art.insertAdjacentHTML('afterbegin', svg);
    }).catch(function () { delete art.dataset.loaded; });
  }
  wide.addEventListener('change', loadArt);
  loadArt();
  if (!window.Swiper) return; // Native scrolling remains usable if the asset fails.
  document.querySelectorAll('[data-about-carousel]').forEach(function (carousel) {
    var track = carousel.querySelector('[data-about-track]');
    var dots = carousel.querySelector('[data-about-dots]');
    var pillars = !!carousel.closest('.about-pillars');
    // 06.10: «Наши ценности» листаются сами раз в 3 с — только в поле зрения,
    // без наведения мыши, касания и prefers-reduced-motion.
    var auto = !!carousel.closest('.about-values');
    var visible = !('IntersectionObserver' in window), hovered = false, touching = false;
    var instance = null;
    function run() {
      if (!instance || !auto || !instance.autoplay) return;
      if (visible && !hovered && !touching && !reduced.matches) {
        if (!instance.autoplay.running) instance.autoplay.start();
      } else if (instance.autoplay.running) {
        instance.autoplay.stop();
      }
    }
    track.classList.add('swiper-wrapper');
    Array.from(track.children).forEach(function (card) { card.classList.add('swiper-slide'); });
    function mark(swiper) {
      dots.querySelectorAll('button').forEach(function (button) {
        button.setAttribute('aria-current', String(button.classList.contains('swiper-pagination-bullet-active')));
      });
      dots.hidden = swiper.isLocked;
    }
    function setup() {
      if (instance) { instance.destroy(true, true); instance = null; }
      dots.replaceChildren();
      if (pillars && !small.matches) { dots.hidden = true; return; }
      dots.hidden = false;
      instance = new Swiper(carousel, {
        slidesPerView: pillars ? 'auto' : 1, spaceBetween: 10, loop: pillars,
        initialSlide: pillars ? Number(carousel.dataset.mobileStart || 0) : 0,
        rewind: auto,
        autoplay: auto && !reduced.matches ? {delay: 3000, disableOnInteraction: false, pauseOnMouseEnter: true} : false,
        speed: reduced.matches ? 0 : 250,
        grabCursor: true, simulateTouch: true,
        preventClicks: true, preventClicksPropagation: true,
        threshold: 6, watchOverflow: true,
        breakpoints: pillars ? {} : {
          700: {slidesPerView: 2, spaceBetween: 20},
          1000: {slidesPerView: 3, spaceBetween: 20}
        },
        pagination: {
          el: dots, clickable: true,
          renderBullet: function (index, className) {
            return '<button type="button" class="' + className + '" aria-label="Показать карточку ' + (index + 1) + '"></button>';
          }
        },
        a11y: {enabled: true, containerMessage: track.getAttribute('aria-label'), paginationBulletMessage: 'Показать карточку {{index}}'},
        on: {
          init: mark, paginationUpdate: mark, lock: mark, unlock: mark,
          touchStart: function () { touching = true; run(); },
          // After release the timer restarts, so the next slide comes 3 s later.
          touchEnd: function () { touching = false; run(); }
        }
      });
      run();
    }
    if (auto) {
      carousel.addEventListener('pointerenter', function (event) { if (event.pointerType === 'mouse') { hovered = true; run(); } });
      carousel.addEventListener('pointerleave', function (event) { if (event.pointerType === 'mouse') { hovered = false; run(); } });
      if ('IntersectionObserver' in window) {
        new IntersectionObserver(function (entries) {
          visible = entries[entries.length - 1].isIntersecting;
          run();
        }, {threshold: 0.25}).observe(carousel);
      }
    }
    track.addEventListener('keydown', function (event) {
      if (!instance || event.target !== track) return;
      if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') {
        event.preventDefault();
        instance[event.key === 'ArrowRight' ? 'slideNext' : 'slidePrev']();
      }
    });
    small.addEventListener('change', setup);
    reduced.addEventListener('change', function () { if (instance) instance.params.speed = reduced.matches ? 0 : 250; if (auto) setup(); });
    setup();
  });
})();
