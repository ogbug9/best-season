/* Д10 (docs/dop-stranicy/01-komponenty.md): чип-фильтр и поиск по списку.

   <div class="chips" data-chips="season" role="group" aria-label="Сезон">
     <button type="button" class="filter-chip" data-chip="">Всё</button>
     <button type="button" class="filter-chip" data-chip="summer">Лето</button>
   </div>
   <input type="search" data-chips-search="season">          — необязательно
   <ul data-chips-for="season"><li data-tags="summer autumn">…</li></ul>
   <p data-chips-empty="season" hidden>Ничего не нашли</p>   — необязательно

   Пустой data-chip — «всё». Выбор пишется в адрес (?season=summer), чтобы
   ссылкой можно было поделиться. Лишние элементы гаснут 0,2 с и скрываются.
   Поиск без учёта регистра и «ё/е», работает вместе с чипом. */
(function () {
  "use strict";
  var FADE_MS = 200;
  var state = {};

  function norm(text) {
    return (text || "").toLowerCase().replace(/ё/g, "е").replace(/\s+/g, " ").trim();
  }

  function apply(name, instant) {
    var current = state[name] || { chip: "", query: "" };
    var group = document.querySelector('[data-chips="' + name + '"]');
    if (group) {
      Array.prototype.forEach.call(group.querySelectorAll("[data-chip]"), function (chip) {
        chip.setAttribute("aria-pressed", chip.getAttribute("data-chip") === current.chip ? "true" : "false");
      });
    }
    var shown = 0;
    Array.prototype.forEach.call(document.querySelectorAll('[data-chips-for="' + name + '"] [data-tags]'), function (item) {
      var byChip = !current.chip || (" " + item.getAttribute("data-tags") + " ").indexOf(" " + current.chip + " ") !== -1;
      var byText = !current.query || norm(item.textContent).indexOf(current.query) !== -1;
      var match = byChip && byText;
      clearTimeout(item._chipTimer);
      if (match) {
        // Пункты FAQ чередуют тёмный и оливковый фон — пересчитываем по видимым.
        if (item.classList.contains("faq__item")) {
          item.classList.toggle("faq__item--dark", shown % 2 === 0);
          item.classList.toggle("faq__item--olive", shown % 2 === 1);
        }
        if (item.classList.contains("place")) {
          item.classList.toggle("place--dark", shown % 2 === 0);
          item.classList.toggle("place--olive", shown % 2 === 1);
        }
        shown += 1;
        // Показанное по выбору чипа не ждёт прокрутки (reveal.js), иначе
        // карточки у низа экрана остаются прозрачными.
        if (!instant && item.hidden) {
          [item].concat(Array.prototype.slice.call(item.querySelectorAll("[data-reveal]"))).forEach(function (el) {
            if (el.hasAttribute("data-reveal")) el.classList.add("is-visible");
          });
        }
        item.hidden = false;
        item.classList.remove("is-fading");
      } else if (instant) {
        item.hidden = true;
      } else {
        item.classList.add("is-fading");
        item._chipTimer = setTimeout(function () { item.hidden = true; }, FADE_MS);
      }
    });
    var empty = document.querySelector('[data-chips-empty="' + name + '"]');
    if (empty) empty.hidden = shown > 0;
  }

  function remember(name, value) {
    var next = new URLSearchParams(window.location.search);
    if (value) next.set(name, value); else next.delete(name);
    var query = next.toString();
    window.history.replaceState(null, "", window.location.pathname + (query ? "?" + query : "") + window.location.hash);
  }

  Array.prototype.forEach.call(document.querySelectorAll("[data-chips]"), function (group) {
    var name = group.getAttribute("data-chips");
    var known = Array.prototype.map.call(group.querySelectorAll("[data-chip]"), function (chip) {
      return chip.getAttribute("data-chip");
    });
    var initial = new URLSearchParams(window.location.search).get(name);
    state[name] = { chip: known.indexOf(initial) !== -1 ? initial : (group.getAttribute("data-chips-default") || ""), query: "" };
    apply(name, true);

    group.addEventListener("click", function (event) {
      var chip = event.target.closest("[data-chip]");
      if (!chip || !group.contains(chip)) return;
      state[name].chip = chip.getAttribute("data-chip");
      apply(name, false);
      remember(name, state[name].chip);
    });
  });

  Array.prototype.forEach.call(document.querySelectorAll("[data-chips-search]"), function (input) {
    var name = input.getAttribute("data-chips-search");
    state[name] = state[name] || { chip: "", query: "" };
    input.addEventListener("input", function () {
      state[name].query = norm(input.value);
      apply(name, true);
    });
  });
})();
