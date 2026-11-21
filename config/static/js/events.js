(function () {
  "use strict";

  const gallery = document.querySelector("[data-events-gallery]");
  if (!gallery) return;
  const filters = gallery.querySelector('[data-chips="archive"]');
  const panels = Array.from(gallery.querySelectorAll("[data-events-panel]"), element => {
    const track = element.querySelector(".events-gallery__track");
    const list = track.querySelector(".events-archive");
    const previous = track.querySelector("[data-events-prev]");
    const next = track.querySelector("[data-events-next]");

    function canRotate() {
      return list.scrollWidth - list.clientWidth <= 1
        && list.querySelectorAll(".events-archive__media img").length >= 3;
    }

    function updateArrows() {
      const remaining = list.scrollWidth - list.clientWidth;
      const rotate = canRotate();
      previous.disabled = !rotate && list.scrollLeft < 1;
      next.disabled = !rotate && list.scrollLeft >= remaining - 1;
      track.classList.toggle("is-static", !rotate && remaining <= 1);
    }

    function move(direction) {
      if (canRotate()) {
        if (direction > 0) list.append(list.firstElementChild);
        else list.prepend(list.lastElementChild);
        return;
      }
      const gap = parseFloat(getComputedStyle(list).columnGap);
      const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      list.scrollBy({
        left: direction * (list.firstElementChild.offsetWidth + gap),
        behavior: reducedMotion ? "instant" : "smooth",
      });
    }

    previous.addEventListener("click", () => move(-1));
    next.addEventListener("click", () => move(1));
    list.addEventListener("scroll", updateArrows, { passive: true });
    if (window.ResizeObserver) new ResizeObserver(updateArrows).observe(list);
    return { element, updateArrows };
  });

  function showSelectedPanel() {
    const key = filters.querySelector('[aria-pressed="true"]').dataset.chip;
    panels.forEach(({ element, updateArrows }) => {
      element.hidden = element.dataset.eventsPanel !== key;
      if (!element.hidden) updateArrows();
    });
  }

  filters.addEventListener("click", showSelectedPanel);
  showSelectedPanel();
})();
