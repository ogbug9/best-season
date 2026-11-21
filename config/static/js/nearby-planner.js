(function () {
  "use strict";

  const root = document.querySelector("[data-nearby-planner]");
  if (!root) return;

  const groups = Array.from(root.querySelectorAll("[data-guide-group]"), group => ({
    element: group,
    list: group.querySelector(".guide__list"),
    cards: Array.from(group.querySelectorAll("[data-guide-card]")),
  }));
  const cards = groups.flatMap(group => group.cards);
  const items = cards.map(card => card.querySelector("[data-plan-item]"));
  const categories = root.querySelector('[data-chips="kind"]');
  const distances = Array.from(root.querySelectorAll("[data-distance]"));
  const day = root.querySelector("[data-dayplan-day]");
  const empty = root.querySelector("[data-nearby-empty]");
  const example = root.querySelector("[data-ready-route-example]");
  const routeList = root.querySelector("[data-ready-route-list]");
  const photo = root.querySelector("[data-ready-route-photo]");
  const summary = root.querySelector("[data-ready-route-summary]");
  const warning = root.querySelector("[data-ready-route-warning]");
  const emptySummary = summary.textContent;
  const wide = window.matchMedia("(min-width: 1101px)");
  const minutes = item => Number(item.dataset.minutes);
  const plan = items.filter(item => item.checked).sort((a, b) => minutes(a) - minutes(b));
  let manuallyOrdered = false;
  let showExample = plan.length === 0;

  function arrangeCards() {
    if (!wide.matches) return;
    groups.forEach(({ list, cards: groupCards }) => {
      const visible = groupCards.filter(card => !card.hidden);
      const heights = visible.map(card => Math.ceil(card.getBoundingClientRect().height));
      const gap = parseFloat(getComputedStyle(list).columnGap);
      const nextRow = [1, 1];
      visible.forEach((card, index) => {
        const column = index % 2;
        card.style.setProperty("--guide-column", column + 1);
        card.style.setProperty("--guide-row", nextRow[column] + " / span " + heights[index]);
        nextRow[column] += heights[index] + gap;
      });
      list.classList.add("guide__list--stacked");
    });
  }

  function filterCards() {
    const kind = categories.querySelector('[aria-pressed="true"]')?.dataset.chip;
    const bands = distances.find(button => button.getAttribute("aria-pressed") === "true").dataset.distance.split(" ");
    groups.forEach(({ element, cards: groupCards }) => {
      groupCards.forEach(card => {
        card.hidden = Boolean(kind && kind !== card.dataset.tags)
          || !bands.includes(card.dataset.band);
      });
      element.hidden = groupCards.every(card => card.hidden);
    });
    empty.hidden = groups.some(({ element }) => !element.hidden);
    arrangeCards();
  }

  function updateAvailability() {
    const date = new Date();
    const today = (date.getDay() + 6) % 7;
    const weekday = day.value === "today" ? today : Number(day.value);
    date.setDate(date.getDate() + (weekday - today + 7) % 7);
    items.forEach(item => {
      const { days, months, title } = item.dataset;
      const closed = (days && !days.split(",").includes(String(weekday)))
        || (months && !months.split(",").includes(String(date.getMonth() + 1)));
      item.closest("[data-guide-card]").classList.toggle("is-closed", !showExample && Boolean(closed));
      const label = item.checked ? "в плане · убрать" : "в план дня";
      item.nextElementSibling.textContent = label;
      item.setAttribute("aria-label", label + ": " + title);
    });
  }

  function moveButton(item, offset, index) {
    const button = document.createElement("button");
    button.type = "button";
    button.dataset.move = offset;
    button.dataset.index = index;
    button.disabled = index + offset < 0 || index + offset >= plan.length;
    button.textContent = offset < 0 ? "↑" : "↓";
    button.setAttribute("aria-label", (offset < 0 ? "Поднять в маршруте: " : "Опустить в маршруте: ") + item.dataset.title);
    return button;
  }

  function renderPlan() {
    updateAvailability();
    const first = plan[0];
    const source = first ? first.dataset.photo : photo.dataset.placeholder;
    photo.hidden = !source;
    if (source) {
      if (photo.getAttribute("src") !== source) photo.src = source;
      photo.alt = first?.dataset.title || "";
    } else {
      photo.removeAttribute("src");
      photo.alt = "";
    }
    photo.dataset.place = first?.dataset.key || "";

    routeList.replaceChildren(...plan.map((item, index) => {
      const row = document.createElement("li");
      const title = document.createElement("b");
      title.textContent = (index + 1) + " · " + item.dataset.title;
      row.append(title);
      if (item.closest(".is-closed")) {
        const status = document.createElement("span");
        status.textContent = "В этот день закрыто";
        row.append(status);
      }
      if (plan.length > 1) {
        const buttons = document.createElement("div");
        buttons.className = "pn-ready-route__controls";
        buttons.append(moveButton(item, -1, index), moveButton(item, 1, index));
        row.append(buttons);
      }
      return row;
    }));
    routeList.hidden = !first;
    example.hidden = !showExample;
    summary.hidden = showExample;
    warning.hidden = plan.length < 4;
    // Между локациями нет замеров. Оценка складывает поездки туда и обратно
    // от глэмпинга; для теплохода в исходных данных указано время рейса.
    const total = plan.reduce((sum, item) => sum + 2 * minutes(item), 0);
    const duration = [total >= 60 && Math.floor(total / 60) + " ч", total % 60 && total % 60 + " мин"].filter(Boolean).join(" ");
    summary.textContent = first ? "В дороге примерно " + duration + " — не считая остановок" : emptySummary;
    arrangeCards();
  }

  categories.addEventListener("click", filterCards);
  distances.forEach(button => button.addEventListener("click", () => {
    distances.forEach(item => item.setAttribute("aria-pressed", String(item === button)));
    filterCards();
  }));
  day.addEventListener("change", () => {
    showExample = false;
    renderPlan();
  });
  items.forEach(item => item.addEventListener("change", () => {
    showExample = false;
    if (item.checked) {
      plan.push(item);
      if (!manuallyOrdered) plan.sort((a, b) => minutes(a) - minutes(b));
    } else {
      plan.splice(plan.indexOf(item), 1);
      if (plan.length < 2) manuallyOrdered = false;
    }
    renderPlan();
  }));
  routeList.addEventListener("click", event => {
    const button = event.target.closest("[data-move]");
    if (!button || button.disabled) return;
    const index = Number(button.dataset.index);
    const moved = index + Number(button.dataset.move);
    [plan[index], plan[moved]] = [plan[moved], plan[index]];
    manuallyOrdered = true;
    renderPlan();
    const row = routeList.children[moved];
    (row.querySelector('[data-move="' + button.dataset.move + '"]:enabled') || row.querySelector("button:enabled")).focus();
  });
  root.querySelector("[data-nearby-reset]").addEventListener("click", () => {
    day.value = "today";
    plan.length = 0;
    manuallyOrdered = false;
    showExample = true;
    items.forEach(item => { item.checked = false; });
    categories.querySelector('[data-chip=""]').click();
    distances.find(button => button.dataset.distance === "near").click();
    renderPlan();
  });

  if (window.ResizeObserver) {
    const observer = new ResizeObserver(arrangeCards);
    cards.forEach(card => observer.observe(card));
  }
  document.addEventListener("DOMContentLoaded", () => {
    filterCards();
    renderPlan();
  });
})();
