/* Временные страницы 09.10.2026 (core/temp_pages.py): небольшой интерактив.
   Всё необязательное: без JS страница остаётся читаемой. */
(function () {
  "use strict";
  var reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function store(key, value) {
    try {
      if (value === undefined) return window.localStorage.getItem(key);
      window.localStorage.setItem(key, value);
    } catch (e) { return null; }
    return null;
  }

  function plural(n, one, few, many) {
    var m10 = n % 10, m100 = n % 100;
    if (m10 === 1 && m100 !== 11) return one;
    if (m10 >= 2 && m10 <= 4 && (m100 < 12 || m100 > 14)) return few;
    return many;
  }

  // «Кто вы из пушистиков?»: больше ответов «0» — первый питомец, иначе второй.
  Array.prototype.forEach.call(document.querySelectorAll("[data-quiz]"), function (form) {
    form.addEventListener("submit", function (event) {
      event.preventDefault();
      var score = 0, total = 0;
      Array.prototype.forEach.call(form.querySelectorAll("input:checked"), function (input) {
        score += parseInt(input.value, 10) || 0;
        total += 1;
      });
      var winner = score * 2 > total ? 1 : 0;
      Array.prototype.forEach.call(form.querySelectorAll("[data-quiz-result]"), function (node) {
        node.hidden = node.getAttribute("data-quiz-result") !== String(winner);
      });
    });
  });

  // «Погладить»: счётчик на устройстве гостя и сердечки.
  Array.prototype.forEach.call(document.querySelectorAll("[data-pat]"), function (box) {
    var key = "bs-pat-" + box.getAttribute("data-pat-key");
    var count = parseInt(store(key), 10) || 0;
    var output = box.querySelector("[data-pat-count]");
    function render() {
      output.textContent = count ? "Мурчит уже " + count + " " + plural(count, "раз", "раза", "раз") : "";
    }
    box.querySelector("[data-pat-btn]").addEventListener("click", function () {
      count += 1;
      store(key, String(count));
      render();
      if (reduced) return;
      var heart = document.createElement("span");
      heart.className = "t-heart";
      heart.textContent = ["♥", "🐾", "♡"][count % 3];
      heart.style.setProperty("--dx", (Math.random() * 80 - 40).toFixed(0) + "px");
      box.appendChild(heart);
      window.setTimeout(function () { heart.remove(); }, 1500);
    });
    render();
  });

  // «Поделиться»: системное меню, иначе копируем ссылку.
  Array.prototype.forEach.call(document.querySelectorAll("[data-share]"), function (button) {
    var label = button.textContent;
    button.addEventListener("click", function () {
      var data = { title: button.getAttribute("data-share-title") || document.title, url: window.location.href };
      if (navigator.share) { navigator.share(data).catch(function () {}); return; }
      if (navigator.clipboard) {
        navigator.clipboard.writeText(data.url).then(function () {
          button.textContent = "Ссылка скопирована";
          window.setTimeout(function () { button.textContent = label; }, 2000);
        }).catch(function () {});
      }
    });
  });

  // Полоса прогресса чтения статьи.
  var progress = document.querySelector("[data-read-progress]");
  var article = document.querySelector(".t-article");
  if (progress && article) {
    var ticking = false;
    var update = function () {
      var rect = article.getBoundingClientRect();
      var range = rect.height - window.innerHeight;
      var value = range > 0 ? Math.min(1, Math.max(0, -rect.top / range)) : 1;
      progress.style.setProperty("--read", value.toFixed(3));
      ticking = false;
    };
    window.addEventListener("scroll", function () {
      if (!ticking) { ticking = true; window.requestAnimationFrame(update); }
    }, { passive: true });
    update();
  }

  // Дней до Нового года.
  Array.prototype.forEach.call(document.querySelectorAll("[data-countdown]"), function (box) {
    var now = new Date();
    var target = new Date(now.getFullYear() + 1, 0, 1);
    var days = Math.ceil((target - now) / 86400000);
    box.querySelector("[data-countdown-days]").textContent = days;
    box.querySelector("[data-countdown-label]").textContent = plural(days, "день", "дня", "дней");
  });

  // «Поместитесь все?»: точки-гости и ответ про беседку и ночёвку.
  Array.prototype.forEach.call(document.querySelectorAll("[data-fit]"), function (box) {
    var capacity = parseInt(box.getAttribute("data-capacity"), 10) || 50;
    var overnight = parseInt(box.getAttribute("data-overnight"), 10) || 16;
    var range = box.querySelector("[data-fit-range]");
    var value = box.querySelector("[data-fit-value]");
    var seats = box.querySelector("[data-fit-seats]");
    var answer = box.querySelector("[data-fit-answer]");
    function render() {
      var guests = parseInt(range.value, 10);
      value.textContent = guests;
      seats.innerHTML = "";
      for (var i = 0; i < guests; i += 1) {
        var dot = document.createElement("i");
        if (i >= capacity) dot.className = "is-over";
        seats.appendChild(dot);
      }
      if (guests > capacity) {
        answer.textContent = "В беседку помещается до " + capacity + " гостей — напишите нам, подумаем вместе.";
      } else if (guests > overnight) {
        answer.textContent = "В беседке поместитесь все. С ночёвкой — до " + overnight + " гостей, остальные могут приехать на праздник.";
      } else {
        answer.textContent = "Поместитесь все — и в беседке, и с ночёвкой в домиках.";
      }
    }
    range.addEventListener("input", render);
    render();
  });

  // Рассвет и закат по координатам (упрощённая формула NOAA, точность ±несколько минут).
  function sunTimes(date, lat, lon) {
    var rad = Math.PI / 180;
    var start = new Date(date.getFullYear(), 0, 0);
    var day = Math.floor((date - start) / 86400000);
    var gamma = 2 * Math.PI / 365 * (day - 1);
    var eqtime = 229.18 * (0.000075 + 0.001868 * Math.cos(gamma) - 0.032077 * Math.sin(gamma)
      - 0.014615 * Math.cos(2 * gamma) - 0.040849 * Math.sin(2 * gamma));
    var decl = 0.006918 - 0.399912 * Math.cos(gamma) + 0.070257 * Math.sin(gamma) - 0.006758 * Math.cos(2 * gamma)
      + 0.000907 * Math.sin(2 * gamma) - 0.002697 * Math.cos(3 * gamma) + 0.00148 * Math.sin(3 * gamma);
    var cosHa = Math.cos(90.833 * rad) / (Math.cos(lat * rad) * Math.cos(decl)) - Math.tan(lat * rad) * Math.tan(decl);
    if (cosHa > 1 || cosHa < -1) return null;
    var ha = Math.acos(cosHa) / rad;
    var noonUtc = 720 - 4 * lon - eqtime;
    return { rise: noonUtc - 4 * ha, set: noonUtc + 4 * ha };
  }
  function clock(minutesUtc) {
    // Глэмпинг в московском времени (UTC+3) — показываем его, а не время устройства.
    var m = Math.round(minutesUtc + 180);
    m = ((m % 1440) + 1440) % 1440;
    var h = Math.floor(m / 60), mm = m % 60;
    return h + ":" + (mm < 10 ? "0" : "") + mm;
  }
  Array.prototype.forEach.call(document.querySelectorAll("[data-sun]"), function (box) {
    var lat = parseFloat(box.getAttribute("data-lat"));
    var lon = parseFloat(box.getAttribute("data-lon"));
    var times = sunTimes(new Date(), lat, lon);
    if (!times) return;
    box.querySelector("[data-sun-rise]").textContent = clock(times.rise);
    box.querySelector("[data-sun-set]").textContent = clock(times.set);
    box.querySelector("[data-sun-golden]").textContent = clock(times.set - 60) + "–" + clock(times.set);
    var now = new Date();
    var nowUtc = now.getUTCHours() * 60 + now.getUTCMinutes();
    var share = (nowUtc - times.rise) / (times.set - times.rise);
    var disc = box.querySelector("[data-sun-disc]");
    if (share < 0 || share > 1) { disc.style.setProperty("--y", "-30%"); return; }
    disc.style.setProperty("--x", (share * 100).toFixed(1) + "%");
    disc.style.setProperty("--y", (Math.sin(share * Math.PI) * 80).toFixed(1) + "%");
  });

  // Чек-лист «что взять» запоминается на устройстве.
  Array.prototype.forEach.call(document.querySelectorAll("[data-pack]"), function (list) {
    var key = "bs-pack-" + list.getAttribute("data-pack");
    var saved = (store(key) || "").split(",");
    Array.prototype.forEach.call(list.querySelectorAll("input"), function (input) {
      input.checked = saved.indexOf(input.value) !== -1;
      input.addEventListener("change", function () {
        var checked = Array.prototype.map.call(list.querySelectorAll("input:checked"), function (i) { return i.value; });
        store(key, checked.join(","));
      });
    });
  });
})();
