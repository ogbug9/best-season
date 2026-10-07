/* Д10 (docs/dop-stranicy/01-komponenty.md): чип-фильтр.

   <div class="chips" data-chips="season" role="group" aria-label="Сезон">
     <button type="button" class="chip" data-chip="">Всё</button>
     <button type="button" class="chip" data-chip="summer">Лето</button>
   </div>
   <ul data-chips-for="season"><li data-tags="summer autumn">…</li></ul>

   Пустой data-chip — «всё». Выбор пишется в адрес (?season=summer), чтобы
   ссылкой можно было поделиться. Лишние элементы гаснут 0,2 с и скрываются. */
(function () {
  "use strict";
  var FADE_MS = 200;

  function apply(name, value, instant) {
    var group = document.querySelector('[data-chips="' + name + '"]');
    if (!group) return;
    Array.prototype.forEach.call(group.querySelectorAll("[data-chip]"), function (chip) {
      chip.setAttribute("aria-pressed", chip.getAttribute("data-chip") === value ? "true" : "false");
    });
    Array.prototype.forEach.call(document.querySelectorAll('[data-chips-for="' + name + '"] [data-tags]'), function (item) {
      var match = !value || (" " + item.getAttribute("data-tags") + " ").indexOf(" " + value + " ") !== -1;
      clearTimeout(item._chipTimer);
      if (match) {
        item.hidden = false;
        item.classList.remove("is-fading");
      } else if (instant) {
        item.hidden = true;
      } else {
        item.classList.add("is-fading");
        item._chipTimer = setTimeout(function () { item.hidden = true; }, FADE_MS);
      }
    });
  }

  Array.prototype.forEach.call(document.querySelectorAll("[data-chips]"), function (group) {
    var name = group.getAttribute("data-chips");
    var params = new URLSearchParams(window.location.search);
    var known = Array.prototype.map.call(group.querySelectorAll("[data-chip]"), function (chip) {
      return chip.getAttribute("data-chip");
    });
    var initial = params.get(name);
    apply(name, known.indexOf(initial) !== -1 ? initial : (group.getAttribute("data-chips-default") || ""), true);

    group.addEventListener("click", function (event) {
      var chip = event.target.closest("[data-chip]");
      if (!chip || !group.contains(chip)) return;
      var value = chip.getAttribute("data-chip");
      apply(name, value, false);
      var next = new URLSearchParams(window.location.search);
      if (value) next.set(name, value); else next.delete(name);
      var query = next.toString();
      window.history.replaceState(null, "", window.location.pathname + (query ? "?" + query : "") + window.location.hash);
    });
  });
})();
