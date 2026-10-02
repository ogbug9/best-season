(function () {
  'use strict';
  var small = window.matchMedia('(max-width: 699px)');
  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
  document.querySelectorAll('[data-about-carousel]').forEach(function (carousel) {
    var track = carousel.querySelector('[data-about-track]');
    var dots = carousel.querySelector('[data-about-dots]');
    var cards = Array.from(track.children), count = 0, current = 0, frame = 0;
    function step() { return cards.length > 1 ? cards[1].offsetLeft - cards[0].offsetLeft : track.clientWidth; }
    function mark() {
      current = Math.min(count - 1, Math.max(0, Math.round(track.scrollLeft / step())));
      Array.from(dots.children).forEach(function (button, index) { button.setAttribute('aria-current', String(index === current)); });
    }
    function go(index, instant) {
      current = Math.max(0, Math.min(count - 1, index));
      track.scrollTo({left: current * step(), behavior: instant || reduced.matches ? 'instant' : 'smooth'});
      mark();
    }
    function setup(initial) {
      var visible = Number(getComputedStyle(track).getPropertyValue('--about-visible')) || 1;
      count = Math.max(1, cards.length - visible + 1);
      dots.replaceChildren();
      dots.hidden = count === 1;
      for (var index = 0; index < count; index++) {
        var button = document.createElement('button');
        button.type = 'button';
        button.setAttribute('aria-label', 'Показать карточку ' + (index + 1));
        button.dataset.index = String(index);
        dots.append(button);
      }
      go(initial && small.matches ? Number(carousel.dataset.mobileStart || 0) : current, true);
    }
    dots.addEventListener('click', function (event) { var button = event.target.closest('button'); if (button) go(Number(button.dataset.index)); });
    track.addEventListener('keydown', function (event) {
      if (event.target !== track || !['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
      event.preventDefault();
      go(event.key === 'Home' ? 0 : event.key === 'End' ? count - 1 : current + (event.key === 'ArrowRight' ? 1 : -1));
    });
    track.addEventListener('scroll', function () { if (!frame) frame = requestAnimationFrame(function () { frame = 0; mark(); }); }, {passive: true});
    var observer = new ResizeObserver(function () { setup(false); });
    observer.observe(track);
    setup(true);
  });
})();
