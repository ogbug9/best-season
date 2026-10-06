'use strict';
// Ф3: «Наши ценности» — autoplay 3 s with rewind, clickable dots, hover pause, reduced motion.
const navigate = require('./pravki_05_10_navigation.cjs');
const SEL = '.about-values [data-about-carousel]';

const state = page => page.evaluate(sel => {
  const c = document.querySelector(sel), s = c.swiper;
  const dots = [...c.querySelectorAll('[data-about-dots] button')];
  return {active: s.activeIndex, dot: dots.findIndex(b => b.classList.contains('swiper-pagination-bullet-active')),
    dots: dots.length, end: s.isEnd, running: !!(s.autoplay && s.autoplay.running)};
}, SEL);

async function open(browser, base, width, reducedMotion) {
  const context = await browser.newContext({viewport: {width, height: 900}, deviceScaleFactor: 1,
    isMobile: width < 700, hasTouch: width < 700, reducedMotion});
  await context.addInitScript(() => { try { localStorage.setItem('bs-cookie-consent-v1', 'dismissed'); } catch (_) {} });
  const page = await context.newPage(), errors = [];
  page.on('pageerror', e => errors.push(String(e)));
  // Own origin only: the Yandex map iframe logs third-party CORS noise.
  page.on('console', m => { if (m.type() === 'error' && (m.location().url || '').startsWith(base)) errors.push(m.text()); });
  await navigate(page, base + '/o-nas/');
  await page.waitForFunction(sel => document.querySelector(sel).swiper, SEL);
  return {context, page, errors};
}

// Records the time of every active-slide change while the block is in view.
async function watch(page, ms) {
  return page.evaluate(([sel, ms]) => new Promise(resolve => {
    const s = document.querySelector(sel).swiper, t0 = performance.now(), log = [];
    const on = () => log.push({t: performance.now() - t0, i: s.activeIndex});
    s.on('activeIndexChange', on);
    setTimeout(() => { s.off('activeIndexChange', on); resolve(log); }, ms);
  }), [SEL, ms]);
}

async function checkValues(browser, base, width) {
  const results = [];
  const add = (name, pass, detail) => results.push({name: `Ф3 ${name}`, width, pass, detail});
  let {context, page, errors} = await open(browser, base, width);
  await page.mouse.move(0, 0);
  const idle = await state(page);
  add('stays still off-screen', !idle.running && idle.active === 0, idle);
  await page.locator(SEL).scrollIntoViewIfNeeded();
  await page.mouse.move(2, 2);
  const s0 = await state(page), positions = s0.dots;
  const log = await watch(page, 3000 * (positions + 1) + 1200);
  // The first change only bounds the start; spacing is measured between later changes.
  const gaps = log.slice(1).map((e, k) => e.t - log[k].t);
  const order = log.map(e => e.i);
  const rewound = order.includes(positions - 1) && order[order.indexOf(positions - 1) + 1] === 0;
  add('autoplay every 3.0±0.5 s', gaps.length >= positions - 1 && log[0] && log[0].t <= 3500 && gaps.every(g => Math.abs(g - 3000) <= 500), {gaps: gaps.map(Math.round), order});
  add('reaches the end and rewinds', rewound, {order, positions});
  const dot = page.locator(`${SEL} [data-about-dots] button`).nth(2);
  await (width < 700 ? dot.tap() : dot.click()); // a phone taps: no mouse hover
  await page.waitForTimeout(400);
  const clicked = await state(page);
  add('third dot opens slide 3', clicked.active === 2 && clicked.dot === 2, clicked);
  if (width >= 700) {
    const box = await page.locator(SEL).boundingBox();
    await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
    const before = await state(page), still = await watch(page, 4500), after = await state(page);
    add('hover pauses', still.length === 0 && before.active === after.active, {before, after, changes: still.length});
    await page.mouse.move(0, 0);
  } else {
    const box = await page.locator(SEL).boundingBox(), cdp = await context.newCDPSession(page);
    const x = box.x + box.width / 2, y = box.y + box.height / 2;
    await cdp.send('Input.dispatchTouchEvent', {type: 'touchStart', touchPoints: [{x, y}]});
    const held = await watch(page, 4000);
    await cdp.send('Input.dispatchTouchEvent', {type: 'touchEnd', touchPoints: []});
    const after = await watch(page, 3600);
    add('touch pauses, resumes 3 s after release', held.length === 0 && after.length >= 1 && Math.abs(after[0].t - 3000) <= 500,
      {held: held.length, resumedAfter: after[0] && Math.round(after[0].t)});
    await cdp.detach();
  }
  add('no console errors', errors.length === 0, errors);
  await context.close();
  ({context, page, errors} = await open(browser, base, width, 'reduce'));
  await page.locator(SEL).scrollIntoViewIfNeeded();
  const still = await watch(page, 4500), reduced = await state(page);
  add('reduced motion: no autoplay', still.length === 0 && !reduced.running && reduced.active === 0, reduced);
  const dot2 = page.locator(`${SEL} [data-about-dots] button`).nth(2);
  await (width < 700 ? dot2.tap() : dot2.click()); await page.waitForTimeout(300);
  add('reduced motion: dots still work', (await state(page)).active === 2, await state(page));
  await context.close();
  return results;
}

module.exports = {checkValues};
