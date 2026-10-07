/* Д8 и Д9 (docs/dop-stranicy/01-komponenty.md): появление при прокрутке
   и прорисовка пунктира. Без JS, без IntersectionObserver и при
   prefers-reduced-motion блоки сразу стоят на месте — скрывает их только
   класс reveal-ready, который ставит этот скрипт. */
(function () {
  "use strict";
  var items = document.querySelectorAll("[data-reveal], [data-draw]");
  if (!items.length || !("IntersectionObserver" in window)) return;
  if (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

  Array.prototype.forEach.call(items, function (el) {
    // Соседние карточки появляются с шагом 60 мс, не больше шести шагов.
    var parent = el.parentElement;
    if (el.hasAttribute("data-reveal") && parent) {
      var siblings = Array.prototype.filter.call(parent.children, function (child) {
        return child.hasAttribute("data-reveal");
      });
      var index = siblings.indexOf(el);
      if (index > 0) el.style.setProperty("--reveal-delay", Math.min(index, 6) * 60 + "ms");
    }
    // Пунктир рисуется маской: data-draw ставится на сплошной путь внутри <mask>.
    if (el.hasAttribute("data-draw") && typeof el.getTotalLength === "function") {
      el.style.setProperty("--draw-length", Math.ceil(el.getTotalLength()));
    }
  });

  document.documentElement.classList.add("reveal-ready");
  var observer = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (!entry.isIntersecting) return;
      entry.target.classList.add("is-visible");
      observer.unobserve(entry.target);
    });
  }, { rootMargin: "0px 0px -10% 0px" });
  Array.prototype.forEach.call(items, function (el) { observer.observe(el); });
})();
