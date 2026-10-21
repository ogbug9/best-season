/* Временные страницы 09.10.2026 (core/temp_pages.py): небольшой интерактив.
   Всё необязательное: без JS страница остаётся читаемой. */
(function () {
  "use strict";
  // Скрипт может прийти дважды (страница + блок игр) — запускаем один раз.
  if (window.bsTempPages) return;
  window.bsTempPages = true;
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
  // ================= Волна 2: игры (core/temp_more.py) =================
  function each(selector, fn) { Array.prototype.forEach.call(document.querySelectorAll(selector), fn); }
  function pick(list) { return list[Math.floor(Math.random() * list.length)]; }
  function shuffle(list) {
    var a = list.slice();
    for (var i = a.length - 1; i > 0; i -= 1) { var j = Math.floor(Math.random() * (i + 1)); var t = a[i]; a[i] = a[j]; a[j] = t; }
    return a;
  }
  function burst(host) {
    if (reduced) return;
    for (var i = 0; i < 14; i += 1) {
      var bit = document.createElement("span");
      bit.className = "t-confetti";
      bit.textContent = pick(["✦", "●", "♥", "✿"]);
      bit.style.setProperty("--dx", (Math.random() * 240 - 120).toFixed(0) + "px");
      bit.style.setProperty("--dy", (-60 - Math.random() * 140).toFixed(0) + "px");
      bit.style.setProperty("--hue", pick(["#9B5026", "#847F57", "#F9B98A", "#3A3C15"]));
      host.appendChild(bit);
      window.setTimeout(function (node) { node.remove(); }, 1300, bit);
    }
  }

  // Бинго: линия по горизонтали, вертикали или диагонали.
  each('[data-game="bingo"]', function (game) {
    var grid = game.querySelector("[data-bingo]");
    var size = parseInt(grid.getAttribute("data-size"), 10) || 3;
    var cells = Array.prototype.slice.call(grid.querySelectorAll(".t-bingo__cell"));
    var done = game.querySelector("[data-game-done]");
    var key = "bs-bingo-" + game.getAttribute("data-game-key");
    var saved = (store(key) || "").split(",");
    function on(i) { return cells[i] && cells[i].getAttribute("aria-pressed") === "true"; }
    function check(celebrate) {
      var lines = [], r, c, line;
      for (r = 0; r < size; r += 1) { line = []; for (c = 0; c < size; c += 1) line.push(r * size + c); lines.push(line); }
      for (c = 0; c < size; c += 1) { line = []; for (r = 0; r < size; r += 1) line.push(r * size + c); lines.push(line); }
      line = []; for (r = 0; r < size; r += 1) line.push(r * size + r); lines.push(line);
      line = []; for (r = 0; r < size; r += 1) line.push(r * size + size - 1 - r); lines.push(line);
      var win = lines.some(function (l) { return l.every(on); });
      cells.forEach(function (cell) { cell.classList.remove("is-line"); });
      lines.forEach(function (l) { if (l.every(on)) l.forEach(function (i) { cells[i].classList.add("is-line"); }); });
      if (win && done.hidden && celebrate) burst(game);
      done.hidden = !win;
    }
    cells.forEach(function (cell, i) {
      if (saved.indexOf(String(i)) !== -1) cell.setAttribute("aria-pressed", "true");
      cell.addEventListener("click", function () {
        cell.setAttribute("aria-pressed", on(i) ? "false" : "true");
        store(key, cells.map(function (_, n) { return on(n) ? String(n) : ""; }).filter(Boolean).join(","));
        check(true);
      });
    });
    game.querySelector("[data-game-reset]").addEventListener("click", function () {
      cells.forEach(function (cell) { cell.setAttribute("aria-pressed", "false"); });
      store(key, "");
      check(false);
    });
    check(false);
  });

  // Кубик: перебор граней и итог.
  each('[data-game="dice"]', function (game) {
    var options = Array.prototype.map.call(game.querySelectorAll("[data-dice-options] li"), function (li) {
      return { title: li.getAttribute("data-title"), text: li.getAttribute("data-text") };
    });
    var faces = ["⚀", "⚁", "⚂", "⚃", "⚄", "⚅"];
    var cube = game.querySelector("[data-dice-cube]");
    var title = game.querySelector("[data-dice-title]");
    var text = game.querySelector("[data-dice-text]");
    var button = game.querySelector("[data-dice-roll]");
    game.classList.add("is-ready");
    button.addEventListener("click", function () {
      var spins = reduced ? 1 : 10, n = 0, last = -1;
      button.disabled = true;
      (function spin() {
        var i;
        do { i = Math.floor(Math.random() * options.length); } while (options.length > 1 && i === last);
        last = i;
        cube.textContent = faces[i % 6];
        title.textContent = options[i].title;
        text.textContent = n + 1 >= spins ? options[i].text : "";
        n += 1;
        if (n < spins) {
          window.setTimeout(spin, 60 + n * 12);
        } else {
          button.disabled = false;
          cube.classList.remove("is-rolled"); void cube.offsetWidth; cube.classList.add("is-rolled");
        }
      })();
    });
  });

  // Колода карточек без повторов, пока не кончится.
  each('[data-game="cards"]', function (game) {
    var source = game.querySelector("[data-deck-source]");
    var all = Array.prototype.map.call(source.content.querySelectorAll("p"), function (p) { return p.textContent; });
    var deck = [];
    var card = game.querySelector("[data-deck-card]");
    var text = game.querySelector("[data-deck-text]");
    var count = game.querySelector("[data-deck-count]");
    function next() {
      if (!deck.length) deck = shuffle(all);
      text.textContent = deck.pop();
      count.textContent = (all.length - deck.length) + " / " + all.length;
      card.classList.remove("is-flipped"); void card.offsetWidth; card.classList.add("is-flipped");
    }
    game.querySelector("[data-deck-next]").addEventListener("click", next);
    card.addEventListener("click", next);
  });

  // Делилка на команды.
  each('[data-game="teams"]', function (game) {
    var input = game.querySelector("[data-teams-input]");
    var out = game.querySelector("[data-teams-out]");
    var names = ["Лес", "Река", "Поляна", "Ферма"];
    game.querySelector("[data-teams-go]").addEventListener("click", function () {
      var people = input.value.split(/[,\n;]+/).map(function (s) { return s.trim(); }).filter(Boolean);
      var count = parseInt(game.querySelector("[data-teams-count]").value, 10) || 2;
      out.innerHTML = "";
      if (people.length < count) {
        var li = document.createElement("li"); li.textContent = "Нужно хотя бы " + count + " имени."; out.appendChild(li); return;
      }
      var teams = []; for (var t = 0; t < count; t += 1) teams.push([]);
      shuffle(people).forEach(function (person, i) { teams[i % count].push(person); });
      teams.forEach(function (team, i) {
        var item = document.createElement("li");
        var head = document.createElement("b"); head.textContent = "Команда «" + names[i] + "»";
        var list = document.createElement("span"); list.textContent = team.join(", ");
        item.appendChild(head); item.appendChild(list); out.appendChild(item);
      });
    });
  });

  // «Найди пару».
  each('[data-game="memory"]', function (game) {
    var board = game.querySelector("[data-memory]");
    var items = board.getAttribute("data-items").split(",");
    var movesOut = game.querySelector("[data-memory-moves]");
    var pairsOut = game.querySelector("[data-memory-pairs]");
    var done = game.querySelector("[data-game-done]");
    var open = [], moves = 0, pairs = 0, lock = false;
    function deal() {
      board.innerHTML = ""; open = []; moves = 0; pairs = 0; lock = false; done.hidden = true;
      movesOut.textContent = "0"; pairsOut.textContent = "0";
      shuffle(items.concat(items)).forEach(function (icon) {
        var li = document.createElement("li");
        var button = document.createElement("button");
        button.type = "button"; button.className = "t-memory__card"; button.setAttribute("data-icon", icon);
        button.setAttribute("aria-label", "Закрытая карточка");
        var back = document.createElement("span"); back.className = "t-memory__back"; back.textContent = "✿";
        var face = document.createElement("span"); face.className = "t-memory__face"; face.textContent = icon;
        back.setAttribute("aria-hidden", "true"); face.setAttribute("aria-hidden", "true");
        button.appendChild(back); button.appendChild(face);
        li.appendChild(button); board.appendChild(li);
      });
    }
    board.addEventListener("click", function (event) {
      var card = event.target.closest(".t-memory__card");
      if (!card || lock || card.classList.contains("is-open")) return;
      card.classList.add("is-open"); card.setAttribute("aria-label", card.getAttribute("data-icon"));
      open.push(card);
      if (open.length < 2) return;
      moves += 1; movesOut.textContent = moves;
      if (open[0].getAttribute("data-icon") === open[1].getAttribute("data-icon")) {
        open.forEach(function (c) { c.classList.add("is-matched"); });
        open = []; pairs += 1; pairsOut.textContent = pairs;
        if (pairs === items.length) { done.hidden = false; burst(game); }
      } else {
        lock = true;
        window.setTimeout(function () {
          open.forEach(function (c) { c.classList.remove("is-open"); c.setAttribute("aria-label", "Закрытая карточка"); });
          open = []; lock = false;
        }, 800);
      }
    });
    game.querySelector("[data-game-reset]").addEventListener("click", deal);
    deal();
  });

  // Викторина: ответ подсвечивается, в конце счёт.
  each('[data-game="trivia"]', function (game) {
    var questions = Array.prototype.slice.call(game.querySelectorAll(".t-trivia__q"));
    var score = game.querySelector("[data-trivia-score]");
    var right = 0, answered = 0;
    questions.forEach(function (q) {
      var answer = q.getAttribute("data-answer");
      q.addEventListener("click", function (event) {
        var option = event.target.closest("[data-option]");
        if (!option || q.classList.contains("is-done")) return;
        q.classList.add("is-done"); answered += 1;
        var ok = option.getAttribute("data-option") === answer;
        if (ok) right += 1;
        option.classList.add(ok ? "is-right" : "is-wrong");
        q.querySelector('[data-option="' + answer + '"]').classList.add("is-right");
        if (answered === questions.length) {
          score.hidden = false;
          score.textContent = "Верно " + right + " из " + questions.length +
            (right === questions.length ? " — блестяще!" : right * 2 >= questions.length ? " — неплохо!" : " — зато теперь вы знаете больше.");
          if (right === questions.length) burst(game);
        }
      });
    });
  });

  // Тест «А или Б»: результат по большинству.
  each("[data-quizlet]", function (form) {
    form.addEventListener("submit", function (event) {
      event.preventDefault();
      var score = 0, total = 0;
      Array.prototype.forEach.call(form.querySelectorAll("input:checked"), function (input) { score += parseInt(input.value, 10) || 0; total += 1; });
      var winner = score * 2 > total ? 1 : 0;
      Array.prototype.forEach.call(form.querySelectorAll("[data-quiz-result]"), function (node) {
        node.hidden = node.getAttribute("data-quiz-result") !== String(winner);
      });
    });
  });

  // Конструктор: фразы выбранных вариантов складываются в план.
  each("[data-mixer]", function (form) {
    var out = form.querySelector("[data-mixer-out]");
    form.addEventListener("submit", function (event) {
      event.preventDefault();
      out.innerHTML = "";
      var title = document.createElement("b"); title.textContent = "Ваш план";
      out.appendChild(title);
      Array.prototype.forEach.call(form.querySelectorAll("input:checked"), function (input) {
        var p = document.createElement("p"); p.textContent = input.value; out.appendChild(p);
      });
      out.hidden = false;
      out.classList.remove("is-new"); void out.offsetWidth; out.classList.add("is-new");
    });
  });

  // Табло.
  each('[data-game="score"]', function (game) {
    var values = Array.prototype.slice.call(game.querySelectorAll("[data-score-value]"));
    game.addEventListener("click", function (event) {
      var step = event.target.closest("[data-score-step]");
      if (!step) return;
      var out = step.closest(".t-score__team").querySelector("[data-score-value]");
      out.textContent = Math.max(0, (parseInt(out.textContent, 10) || 0) + parseInt(step.getAttribute("data-score-step"), 10));
    });
    game.querySelector("[data-game-reset]").addEventListener("click", function () { values.forEach(function (v) { v.textContent = "0"; }); });
  });

  // Дыхательный таймер: вдох 4 с, выдох 6 с.
  each('[data-game="breath"]', function (game) {
    var box = game.querySelector("[data-breath]");
    var label = game.querySelector("[data-breath-label]");
    var time = game.querySelector("[data-breath-time]");
    var button = game.querySelector("[data-breath-go]");
    var total = (parseInt(box.getAttribute("data-minutes"), 10) || 3) * 60;
    var timer = null;
    function stop(text) {
      window.clearInterval(timer); timer = null;
      box.classList.remove("is-in", "is-out");
      label.textContent = text; button.textContent = "Начать";
    }
    button.addEventListener("click", function () {
      if (timer) { stop("Пауза"); return; }
      var left = total, phase = 1;
      button.textContent = "Остановить";
      box.classList.add("is-in"); label.textContent = "Вдох";
      timer = window.setInterval(function () {
        left -= 1;
        var m = Math.floor(left / 60), s = left % 60;
        time.textContent = m + ":" + (s < 10 ? "0" : "") + s;
        var inCycle = (total - left) % 10;
        if (inCycle < 4) {
          if (phase !== 1) { phase = 1; box.classList.add("is-in"); box.classList.remove("is-out"); label.textContent = "Вдох"; }
        } else if (phase !== 2) {
          phase = 2; box.classList.add("is-out"); box.classList.remove("is-in"); label.textContent = "Выдох";
        }
        if (left <= 0) { stop("Готово. Как звучит река?"); time.textContent = (total / 60) + ":00"; }
      }, 1000);
    });
  });

  // Полоса месяцев: отмечаем текущий.
  var month = String(new Date().getMonth() + 1);
  each("[data-months] [data-month], [data-year] [data-month]", function (node) {
    if (node.getAttribute("data-month") === month) node.classList.add("is-now");
  });

  // Доплата за питомца по росту в холке.
  each("[data-fee]", function (box) {
    var small = parseInt(box.getAttribute("data-small"), 10) || 0;
    var large = parseInt(box.getAttribute("data-large"), 10) || 0;
    var range = box.querySelector("[data-fee-range]");
    function render() {
      var height = parseInt(range.value, 10);
      box.querySelector("[data-fee-height]").textContent = height;
      box.querySelector("[data-fee-total]").textContent = String(height <= 45 ? small : large).replace(/\B(?=(\d{3})+(?!\d))/g, " ") + " ₽";
      box.querySelector("[data-fee-dog]").style.fontSize = (24 + height * 0.9).toFixed(0) + "px";
    }
    range.addEventListener("input", render);
    render();
  });

  // Конструктор сертификата: живое превью и черновик в Telegram.
  each("[data-gift]", function (box) {
    var form = box.querySelector("[data-gift-form]");
    var card = box.querySelector("[data-gift-card]");
    var send = box.querySelector("[data-gift-send]");
    var base = box.getAttribute("data-base");
    function value(name) {
      var el = form.querySelector('[name="' + name + '"]:checked') || form.querySelector('[name="' + name + '"]:not([type="radio"])');
      return el ? el.value.trim() : "";
    }
    function out(name, text) { var el = card.querySelector('[data-gift-out="' + name + '"]'); if (el) el.textContent = text; }
    function render() {
      var gift = form.querySelector('[name="gift"]:checked');
      var theme = form.querySelector('[name="theme"]:checked');
      out("occasion", value("occasion"));
      out("to", value("to") ? "Для: " + value("to") : "Для вас");
      out("gift", value("gift"));
      out("note", gift ? gift.getAttribute("data-note") : "");
      out("wish", value("wish") || "Время — самый ценный подарок.");
      out("from", value("from"));
      card.className = "t-card t-card--" + value("theme");
      if (send && base) {
        var message = "Здравствуйте! Хочу подарочный сертификат.\nПовод: " + value("occasion") + "\nПодарок: " + value("gift") +
          (value("to") ? "\nКому: " + value("to") : "") + (value("from") ? "\nОт: " + value("from") : "") +
          (value("wish") ? "\nПожелание: " + value("wish") : "") + "\nОткрытка: " + (theme ? theme.parentNode.textContent.trim() : "");
        try { var url = new URL(base); url.searchParams.set("text", message); send.href = url.toString(); } catch (e) { send.href = base; }
      }
    }
    form.addEventListener("input", render);
    form.addEventListener("change", render);
    render();
  });
})();
