(() => {
  const map = document.querySelector('[data-territory-map]');
  if (!map) return;

  const points = [...map.querySelectorAll('[data-map-point]')];
  const filters = [...map.querySelectorAll('[data-map-filter]')];
  const seasons = [...map.querySelectorAll('[data-map-season]')];
  const details = map.querySelectorAll('[data-map-detail]');
  const summary = map.querySelector('[data-map-summary-text]');
  const detailPanel = map.querySelector('.t-field__detail');

  function select(point) {
    points.forEach(item => item.setAttribute('aria-pressed', item === point));
    details.forEach(detail => { detail.hidden = detail.dataset.mapDetail !== point.dataset.mapPoint; });
    summary.textContent = point.dataset.mapSummary;
  }

  filters.forEach(filter => filter.addEventListener('click', () => {
    const category = filter.dataset.mapFilter;
    filters.forEach(item => item.setAttribute('aria-pressed', item === filter));
    points.forEach(point => { point.hidden = !!category && !point.dataset.mapCategory.split(' ').includes(category); });
    select(category ? points.find(point => !point.hidden) : points.find(point => point.dataset.mapPoint === 'farm'));
  }));

  points.forEach(point => point.addEventListener('click', () => select(point)));
  seasons.forEach(season => season.addEventListener('click', () => {
    seasons.forEach(item => item.setAttribute('aria-pressed', item === season));
    map.dataset.season = season.dataset.mapSeason;
  }));
  map.querySelector('[data-map-expand]').addEventListener('click', () => detailPanel.focus());
})();
