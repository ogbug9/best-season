// Run: node --test core/tests_kontur.cjs
// A deterministic DOM/SDK boundary for script races; no network or reservations.
const { test } = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, '../config/static/js/kontur.js'), 'utf8');

function fixture(options = {}) {
  const events = {}, timers = new Map(), frames = [], scripts = [], added = [];
  let timerId = 0, initCount = 0, hooks, reloads = 0;
  function node(id = '') {
    return { id, hidden: false, textContent: '', style: {}, attrs: {},
      setAttribute(k, v) { this.attrs[k] = v; },
      removeAttribute(k) { delete this.attrs[k]; },
      getAttribute(k) { return this.attrs[k] || ''; },
      addEventListener(k, fn) { this[k] = fn; },
      getClientRects() { return modal.open && !this.hidden ? [{}] : []; },
      getBoundingClientRect() { return { width: modal.open && !this.hidden ? 1176 : 0 }; },
      focus() {}, remove() { this.removed = true; }, querySelector() { return null; },
    };
  }
  const modal = node(); modal.open = false;
  modal.showModal = () => { modal.open = true; };
  modal.close = () => { modal.open = false; modal.onclose(); };
  modal.addEventListener = (k, fn) => { modal['on' + k] = fn; };
  const nodes = {};
  for (const name of ['host', 'fallback', 'loading', 'note', 'retry', 'help', 'catalog']) {
    nodes['[data-booking-' + name + ']'] = node(name);
  }
  const host = nodes['[data-booking-host]']; host.id = 'BookingFormWidget'; host.hidden = true;
  const fallback = nodes['[data-booking-fallback]']; fallback.hidden = true;
  nodes['[data-fallback-note-idle]'] = node();
  nodes['[data-fallback-note-error]'] = node();
  const containers = ['roomsList', 'hourlyObjectsList', 'availabilityCalendar'].map(type => {
    const el = node(type); el.attrs['data-kontur-type'] = type; return el;
  });
  modal.querySelector = key => nodes[key] || null;
  modal.querySelectorAll = () => containers;
  const config = { hotelId: options.missing ? '' : 'configured-in-settings' };
  const document = {
    body: node(), head: { appendChild(s) { scripts.push(s); } },
    querySelector: () => modal,
    getElementById: () => ({ textContent: JSON.stringify(config) }),
    createElement: () => node(),
    addEventListener: (k, fn) => { events[k] = fn; },
  };
  const window = { scrollY: 123, scrollTo() {}, location: { reload() { reloads++; } } };
  const sdk = {
    init(config) {
      initCount++; hooks = config.hooks;
      if (options.throwInit) throw new Error('init');
      if (options.failInit) { hooks.onError(new Error('init')); return; }
      if (!options.asyncInit) hooks.onInit();
    },
    add(config) {
      assert.equal(modal.open, true, 'add must never run in a closed dialog');
      assert.equal(host.hidden, false, 'booking form must be visible before add');
      assert.equal(nodes['[data-booking-catalog]'].hidden, false);
      added.push(config.type);
      if (options.failAdd) hooks.onError({ message: 'private details' });
    },
  };
  vm.runInNewContext(source, {
    document, window, requestAnimationFrame(fn) { frames.push(fn); },
    setTimeout(fn) { timers.set(++timerId, fn); return timerId; },
    clearTimeout(id) { timers.delete(id); },
  });
  function click(selector) {
    const target = node(); target.closest = s => s === selector ? target : null;
    events.click({ target, preventDefault() {} });
  }
  function frame() { while (frames.length) frames.shift()(); }
  function load() { window.HotelWidget = sdk; scripts.at(-1).onload(); frame(); }
  return { window, modal, nodes, host, fallback, scripts, added, click, frame, load,
    open() { click('[data-booking-open]'); frame(); },
    close() { click('[data-booking-close]'); },
    timeout() { const pending = [...timers.values()]; timers.clear(); pending.forEach(fn => fn()); },
    get initCount() { return initCount; }, get hooks() { return hooks; }, get reloads() { return reloads; },
  };
}

test('lazy loading and all four visible containers are registered once across reopenings', () => {
  const f = fixture(); assert.equal(f.scripts.length, 0);
  f.open(); f.load(); f.close(); f.open();
  assert.equal(f.initCount, 1);
  assert.deepEqual(f.added, ['bookingForm', 'roomsList', 'hourlyObjectsList', 'availabilityCalendar']);
  assert.equal(f.fallback.hidden, true);
});
test('script arriving after close waits for reopening', () => {
  const f = fixture(); f.open(); f.close(); f.load();
  assert.equal(f.initCount, 0);
  f.open(); assert.equal(f.initCount, 1);
});
test('close before the layout frame does not load the script', () => {
  const f = fixture(); f.click('[data-booking-open]'); f.close(); f.frame();
  assert.equal(f.scripts.length, 0);
  f.open(); assert.equal(f.scripts.length, 1);
});
test('double open does not create extra scripts or timers', () => {
  const f = fixture(); f.open(); f.open();
  assert.equal(f.scripts.length, 1); f.load(); assert.equal(f.initCount, 1);
});
test('timeout is terminal for late script events', () => {
  const f = fixture(); f.open(); f.timeout(); f.load();
  assert.equal(f.initCount, 0); assert.equal(f.fallback.hidden, false); assert.equal(f.host.hidden, true);
});
test('script error can be retried while preserving the fallback DOM', () => {
  const f = fixture(); f.open(); f.scripts[0].onerror();
  f.fallback.draft = 'typed request'; f.click('[data-booking-retry]'); f.frame();
  assert.equal(f.scripts.length, 2); assert.equal(f.scripts[0].removed, true);
  f.load(); assert.equal(f.initCount, 1); assert.equal(f.fallback.draft, 'typed request');
});
test('callbacks from an abandoned attempt cannot poison the retry', () => {
  const f = fixture(); f.open(); const lateError = f.scripts[0].onerror;
  f.timeout(); f.click('[data-booking-retry]'); f.frame(); lateError(); f.load();
  assert.equal(f.fallback.hidden, true);
});
test('init exception exposes fallback and an explicit full reload, never a second init', () => {
  const f = fixture({ throwInit: true }); f.open(); f.load();
  assert.equal(f.fallback.hidden, false);
  assert.equal(f.nodes['[data-booking-retry]'].textContent, 'Перезагрузить страницу');
  f.click('[data-booking-retry]'); assert.equal(f.reloads, 1); assert.equal(f.initCount, 1);
});
test('provider error during add stops further registration', () => {
  const f = fixture({ failAdd: true }); f.open(); f.load();
  assert.equal(f.fallback.hidden, false); assert.deepEqual(f.added, ['bookingForm']);
});
test('synchronous init error does not call add on newly hidden containers', () => {
  const f = fixture({ failInit: true }); f.open(); f.load();
  assert.equal(f.fallback.hidden, false); assert.equal(f.added.length, 0);
});
test('late onInit cannot hide fallback after a timeout', () => {
  const f = fixture({ asyncInit: true }); f.open(); f.load(); f.timeout(); f.hooks.onInit();
  assert.equal(f.fallback.hidden, false); assert.equal(f.host.hidden, true);
});
test('reopening a pending init does not initialize again', () => {
  const f = fixture({ asyncInit: true }); f.open(); f.load(); f.close(); f.open(); f.hooks.onInit();
  assert.equal(f.initCount, 1); assert.equal(f.fallback.hidden, true);
});
test('empty configuration shows the working request form without network', () => {
  const f = fixture({ missing: true }); f.open();
  assert.equal(f.scripts.length, 0); assert.equal(f.fallback.hidden, false);
});
test('provider runtime/booking failure exposes fallback', () => {
  const f = fixture(); f.open(); f.load(); f.hooks.onError(new Error('booking'));
  assert.equal(f.fallback.hidden, false); assert.equal(f.host.hidden, true);
});
