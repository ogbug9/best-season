'use strict';
// Acceptance for the second 06.10 wave (chat of Nastya/Sofia). No forms are submitted.
// Usage: node design/check_final_06_10_b.cjs <base-url> <out-dir>
const fs = require('node:fs'), path = require('node:path');
const {chromium} = require('playwright');
const navigate = require('./pravki_05_10_navigation.cjs');

const [baseArg, outArg] = process.argv.slice(2);
const base = baseArg.replace(/\/$/, ''), out = path.resolve(outArg || 'tmp/pravki-06-10/final-b');
const results = [];
const add = (name, pass, detail = {}, width = '') => {
  results.push({name, width, pass: !!pass, detail});
  console.log(`${pass ? 'PASS' : 'FAIL'} ${width} ${name}${pass ? '' : ' ' + JSON.stringify(detail).slice(0, 400)}`);
};
const EMPTY = ['/territoriya/razvlecheniya/', '/territoriya/chem-zanyatsya/', '/territoriya/meropriyatiya/',
  '/o-nas/partneram/', '/pravila-bronirovaniya/', '/vyezdy-kompaniy/', '/rassylka/'];

async function context(browser, width, extra = {}) {
  const mobile = width < 700;
  const ctx = await browser.newContext({viewport: {width, height: mobile ? 844 : 900}, deviceScaleFactor: 1, isMobile: mobile, hasTouch: mobile, ...extra});
  await ctx.addInitScript(() => { try { localStorage.setItem('bs-cookie-consent-v1', 'dismissed'); } catch (_) {} });
  return ctx;
}

// Rows of a clip where pixels differ from the first pixel: returns [{y, from, to}] runs.
async function strokes(page, clip) {
  const png = await page.screenshot({clip});
  return page.evaluate(async data => {
    const img = new Image(); img.src = 'data:image/png;base64,' + data; await img.decode();
    const c = document.createElement('canvas'); c.width = img.width; c.height = img.height;
    const x = c.getContext('2d'); x.drawImage(img, 0, 0); const d = x.getImageData(0, 0, c.width, c.height).data;
    const bg = d[0] + d[1] + d[2], rows = [];
    for (let y = 0; y < c.height; y++) {
      let from = -1, to = -1;
      for (let X = 0; X < c.width; X++) { const k = (y * c.width + X) * 4; if (Math.abs(d[k] + d[k + 1] + d[k + 2] - bg) > 150) { if (from < 0) from = X; to = X; } }
      if (from >= 0) rows.push({y, from, to});
    }
    return rows;
  }, png.toString('base64'));
}

async function mobile(browser) {
  const ctx = await context(browser, 390), page = await ctx.newPage();
  // Burger 16 / 16 / 9, step 5, bottom line right-aligned.
  for (const route of ['/', '/razmeshchenie/', '/o-nas/']) {
    await navigate(page, base + route);
    const box = await page.locator('.nav-toggle__button span').boundingBox();
    const rows = await strokes(page, {x: box.x - 2, y: box.y - 2, width: 20, height: 16});
    const lines = [];
    for (const r of rows) { const last = lines[lines.length - 1]; if (last && r.y === last.y2 + 1) last.y2 = r.y; else lines.push({y1: r.y, y2: r.y, w: r.to - r.from + 1, right: r.to}); }
    const widths = lines.map(l => l.w), tops = lines.map(l => l.y1);
    add(`burger ${route}: lines ${widths.join('/')}`, lines.length === 3 && Math.abs(widths[0] - 16) <= 1 && Math.abs(widths[1] - 16) <= 1 && Math.abs(widths[2] - 9) <= 1 &&
      tops[1] - tops[0] === 5 && tops[2] - tops[1] === 5 && Math.abs(lines[2].right - lines[0].right) <= 1, {lines}, 390);
  }
  // Footer: regular headings, pills like the menu, closed sections stay hidden.
  await navigate(page, base + '/');
  const toggle = page.locator('.footer__toggle').first();
  await toggle.scrollIntoViewIfNeeded(); await toggle.tap(); await page.waitForTimeout(300);
  const foot = await page.evaluate(() => {
    const lists = [...document.querySelectorAll('.footer__columns ul')].map(u => getComputedStyle(u).display);
    const items = [...document.querySelectorAll('.footer__columns ul:not([hidden]) li > :is(a, button)')].map(e => {
      const c = getComputedStyle(e), r = e.getBoundingClientRect();
      return {h: Math.round(r.height), bg: c.backgroundColor, fs: c.fontSize, fw: c.fontWeight, r: c.borderRadius, jc: c.justifyContent};
    });
    return {lists, items, title: getComputedStyle(document.querySelector('.footer__column-title')).fontWeight};
  });
  add('footer: headings 400, open items are 40 px #E0D9C9 pills, others stay closed', foot.title === '400' && foot.lists[0] === 'grid' && foot.lists.slice(1).every(d => d === 'none') &&
    foot.items.length > 0 && foot.items.every(i => i.h === 40 && i.bg === 'rgb(224, 217, 201)' && i.fs === '16px' && i.fw === '400' && i.r === '100px' && i.jc !== 'center'), foot, 390);
  // Gallery: title → lead 8, lead → photo 24.
  const gal = await page.evaluate(() => {
    const s = document.querySelector('.section--gallery'), R = e => e.getBoundingClientRect();
    const h = s.querySelector('h2'), d = s.querySelector('.section__lead');
    const img = [...s.querySelectorAll('img')].find(i => R(i).width > 200);
    return {a: Math.round(R(d).top - R(h).bottom), b: Math.round(R(img).top - R(d).bottom)};
  });
  add(`gallery gaps ${gal.a}/${gal.b} (8/24)`, gal.a === 8 && gal.b === 24, gal, 390);
  // Territory: carousel dots → title 66 px (ink), checked via DOM boxes of the dots and title.
  const terr = await page.evaluate(() => {
    const t = [...document.querySelectorAll('h2')].find(h => /территория/i.test(h.textContent));
    const dots = document.querySelector('.mobile-carousel-dots');
    return Math.round(t.getBoundingClientRect().top - dots.getBoundingClientRect().bottom);
  });
  add(`territory: dots → title box gap ${terr}px (ink 66 as in Main mob)`, terr >= 60 && terr <= 66, {terr}, 390);
  // Cards: first tap shows the description, second tap opens the card link.
  for (const [route, sel] of [['/', '.territory-card'], ['/razmeshchenie/', '.mobile-service-tiles .territory-card']]) {
    await navigate(page, base + route);
    const card = page.locator(sel).nth(1);
    await card.scrollIntoViewIfNeeded(); await card.tap(); await page.waitForTimeout(300);
    const first = await card.evaluate(e => {
      const p = e.querySelector('.territory-card__details p'), a = e.querySelector('.territory-card__link');
      return {open: e.classList.contains('is-open'), text: p ? p.textContent.trim().length : 0, visible: !!(p && p.getBoundingClientRect().height), href: a && a.href};
    });
    const box = await card.boundingBox();
    await page.touchscreen.tap(box.x + 12, box.y + 12);
    await page.waitForURL(u => u.href !== base + route, {timeout: 5000}).catch(() => {});
    add(`cards ${route}: tap 1 description, tap 2 → link`, first.open && first.visible && first.text > 20 && page.url() === first.href, {first, url: page.url()}, 390);
  }
  // Placeholder pages; home slogan heart.
  for (const route of EMPTY) {
    await navigate(page, base + route);
    const r = await page.evaluate(() => ({ph: !!document.querySelector('.page-placeholder'), raw: document.body.innerText.includes('ожидается от заказчика'), sw: document.documentElement.scrollWidth - innerWidth}));
    add(`placeholder ${route}`, r.ph && !r.raw && r.sw <= 0, r, 390);
  }
  await navigate(page, base + '/o-nas/');
  const art = await page.evaluate(() => document.querySelectorAll('.about-art--mobile path[stroke-dasharray]').length);
  add(`About mobile: ${art} dashed lines (8 in About us mob (3))`, art === 8, {art}, 390);
  await ctx.close();
}

async function desktop(browser) {
  const ctx = await context(browser, 1440), page = await ctx.newPage();
  await navigate(page, base + '/o-nas/');
  const about = await page.evaluate(() => {
    const img = document.querySelector('.about-hero__media img');
    return {img: !!(img && img.complete && img.naturalWidth), nursery: document.body.innerText.includes('Долина роз')};
  });
  add('About: hero uses the homepage photo; nursery name removed', about.img && !about.nursery, about, 1440);
  await navigate(page, base + '/akcii/');
  const promos = await page.evaluate(() => [...document.querySelectorAll('main h2, main h3')].map(h => h.textContent.replace(/\s+/g, ' ').trim()));
  const autumn = new Date().getMonth() + 1, day = new Date().getDate();
  const winter = (autumn > 9 || autumn < 4) || (autumn === 9 && day >= 30) || (autumn === 4 && day < 30);
  const has = t => promos.some(p => p.includes(t));
  add(`promotions: only the current seasonal tariff (${winter ? 'октябрь–апрель' : 'май–сентябрь'})`,
    winter ? has('октября по апрель') && !has('мая по сентябрь') : has('мая по сентябрь') && !has('октября по апрель'), {promos}, 1440);
  for (const width of [1440, 1024, 768]) {
    await page.setViewportSize({width, height: 900});
    await navigate(page, base + '/razmeshchenie/');
    const tiles = page.locator('.cards--service-tiles .territory-card');
    const grid = await page.evaluate(() => [...document.querySelectorAll('.cards--service-tiles > li')].map(e => Math.round(e.getBoundingClientRect().width)));
    const rows = [];
    for (let i = 0; i < await tiles.count(); i++) {
      const t = tiles.nth(i); await t.scrollIntoViewIfNeeded(); await t.hover(); await page.waitForTimeout(250);
      rows.push(await t.evaluate(e => {
        const r = e.getBoundingClientRect(), p = e.querySelector('.territory-card__details p'), a = e.querySelector('.territory-card__link');
        const q = p && p.getBoundingClientRect(), b = a && a.getBoundingClientRect();
        return {text: p ? p.textContent.trim().length : 0, inside: !!(q && b && q.top >= r.top && b.bottom <= r.bottom), clipped: !!(p && p.scrollHeight > p.clientHeight + 1)};
      }));
    }
    const expectW = width >= 1280 ? 295 : null;
    add(`catalogue tiles: ${grid.join('/')} px, descriptions inside`, grid.length === 4 && grid.every(w => expectW ? w === expectW : w > 250) &&
      rows.every(r => r.text > 20 && r.inside && !r.clipped), {grid, rows}, width);
  }
  await ctx.close();
}

(async () => {
  fs.mkdirSync(out, {recursive: true});
  const browser = await chromium.launch({channel: process.env.CHROME_PATH ? undefined : 'msedge', executablePath: process.env.CHROME_PATH || undefined});
  try { await mobile(browser); await desktop(browser); }
  catch (error) { add('script error', false, String(error.stack || error)); }
  finally { await browser.close(); fs.writeFileSync(path.join(out, 'results.json'), JSON.stringify({base, results}, null, 2)); }
  const failed = results.filter(r => !r.pass);
  console.log(`${results.length - failed.length}/${results.length} PASS`);
  if (failed.length) process.exitCode = 1;
})();
