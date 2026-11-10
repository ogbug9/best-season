(function () {
  "use strict";

  var gallery = document.querySelector("[data-events-gallery]");
  if (!gallery) return;
  var list = gallery.querySelector(".events-archive");
  var previous = gallery.querySelector("[data-events-prev]");
  var next = gallery.querySelector("[data-events-next]");

  function updateArrows() {
    previous.disabled = list.scrollLeft < 1;
    next.disabled = list.scrollLeft + list.clientWidth >= list.scrollWidth - 1;
  }

  function move(direction) {
    var card = list.querySelector(".events-archive__item:not([hidden])");
    if (!card) return;
    var gap = parseFloat(getComputedStyle(list).columnGap);
    var reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    list.scrollBy({ left: direction * (card.offsetWidth + gap), behavior: reducedMotion ? "instant" : "smooth" });
  }

  previous.addEventListener("click", function () { move(-1); });
  next.addEventListener("click", function () { move(1); });
  list.addEventListener("scroll", updateArrows, { passive: true });
  new ResizeObserver(updateArrows).observe(list);
  new MutationObserver(function () {
    list.scrollLeft = 0;
    updateArrows();
  }).observe(list, { subtree: true, attributes: true, attributeFilter: ["hidden"] });
  updateArrows();
})();
