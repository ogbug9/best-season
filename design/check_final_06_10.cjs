'use strict';
// Acceptance checks for 06.10 (Ф1–Ф5 + regression). No forms are submitted.
// Usage: node design/check_final_06_10.cjs <base-url> <out-dir> <baseline-dir> [--only=f1,f2,...]
const fs = require('node:fs'), path = require('node:path');
const {chromium} = require('playwright');
const navigate = require('./pravki_05_10_navigation.cjs');
const bg = require('./check_final_06_10_bg.cjs');
const {checkValues} = require('./check_final_06_10_values.cjs');

const [baseArg, outArg, baselineArg] = process.argv.slice(2);
const base = baseArg.replace(/\/$/, ''), out = path.resolve(outArg), baseline = path.resolve(baselineArg);
const only = (process.argv.find(a => a.startsWith('--only=')) || '').slice(7).split(',').filter(Boolean);
const want = name => !only.length || only.includes(name);
const results = [];
const add = (name, pass, detail = {}, width = '') => {
  results.push({name, width, pass: !!pass, detail});
  console.log(`${pass ? 'PASS' : 'FAIL'} ${width} ${name}${pass ? '' : ' ' + JSON.stringify(detail).slice(0, 400)}`);
};
const dismissCookies = () => { try { localStorage.setItem('bs-cookie-consent-v1', 'dismissed'); } catch (_) {} };

// Measured in the mockup PNGs (the slogan is outlined in SVG), see docs/pravki-06-10.md.
const MOTTO = {
  1440: {source: 'About us (2).png', line1: 318, line2: 329, heartRight: 1120, center: 719},
  390: {source: 'About us mob (2).png', line1: 28, line2: 33, heartRight: 360, center: 194},
};
const TEXT = [0x49, 0x49, 0x49];

async function context(browser, width, height, extra = {}) {
  const mobile = width < 700;
  const ctx = await browser.newContext({viewport: {width, height}, deviceScaleFactor: 1, isMobile: mobile, hasTouch: mobile, ...extra});
  if (!extra.keepCookies) await ctx.addInitScript(dismissCookies);
  return ctx;
}

// Pixel analysis of a PNG inside the browser (no extra Node dependencies).
async function pixels(page, png, fn, arg) {
  return page.evaluate(async ([data, source, arg]) => {
    const img = new Image(); img.src = 'data:image/png;base64,' + data; await img.decode();
    const c = document.createElement('canvas'); c.width = img.width; c.height = img.height;
    const x = c.getContext('2d', {willReadFrequently: true}); x.drawImage(img, 0, 0);
    const d = x.getImageData(0, 0, c.width, c.height).data;
    return (0, eval)('(' + source + ')')(d, c.width, c.height, arg);
  }, [png.toString('base64'), fn.toString(), arg]);
}

function inkEdges(d, w, h, rows) {
  const lum = i => (d[i] * 299 + d[i + 1] * 587 + d[i + 2] * 114) / 1000;
  const out = rows.map(() => ({left: Infinity, right: -Infinity}));
  let heartRight = -Infinity;
  for (let y = 0; y < h; y++) {
    const ls = []; for (let x = 0; x < w; x++) ls.push(lum((y * w + x) * 4));
    const bgLum = [...ls].sort((a, b) => a - b)[Math.floor(w * .9)];
    for (let x = 0; x < w; x++) {
      const i = (y * w + x) * 4, warm = d[i] - d[i + 2] > 45;
      if (warm && bgLum - ls[x] > 25) heartRight = Math.max(heartRight, x);
      if (!warm && bgLum - ls[x] > 40) rows.forEach((r, k) => { if (y >= r[0] && y < r[1]) { out[k].left = Math.min(out[k].left, x); out[k].right = Math.max(out[k].right, x); } });
    }
  }
  return {lines: out, heartRight};
}

async function compareImages(page, a, b, limit = Infinity) {
  if (!fs.existsSync(a) || !fs.existsSync(b)) return {missing: true};
  return page.evaluate(async ([da, db, limit]) => {
    const load = async s => { const i = new Image(); i.src = 'data:image/png;base64,' + s; await i.decode(); return i; };
    const [ia, ib] = await Promise.all([load(da), load(db)]);
    const w = Math.min(ia.width, ib.width), h = Math.min(ia.height, ib.height, limit);
    if (!h) return {diff: 0, compared: 0, heights: [ia.height, ib.height], widths: [ia.width, ib.width]};
    const read = i => { const c = document.createElement('canvas'); c.width = w; c.height = h; const x = c.getContext('2d'); x.drawImage(i, 0, 0); return x.getImageData(0, 0, w, h).data; };
    const pa = read(ia), pb = read(ib); let diff = 0;
    for (let k = 0; k < pa.length; k += 4) if (pa[k] !== pb[k] || pa[k + 1] !== pb[k + 1] || pa[k + 2] !== pb[k + 2]) diff++;
    return {diff, compared: h, heights: [ia.height, ib.height], widths: [ia.width, ib.width]};
  }, [fs.readFileSync(a).toString('base64'), fs.readFileSync(b).toString('base64'), limit]);
}

// ---------- Ф1 ----------
async function f1(browser) {
  for (const width of [390, 320]) {
    const rows = await bg.mobileNetwork(browser, base, width);
    for (const r of rows) add(`Ф1 mobile backgrounds ${r.route}: no desktop layers, ${Math.round(r.total / 1024)} KB SVG`, r.pass,
      {desktop: r.desktop, total: r.total, files: r.svg.map(s => `${s.url} ${s.size}`)}, width);
  }
  // Light layers: darkest line pixel on cream keeps body text contrast ≥ 4.5.
  const ctx = await context(browser, 390, 844), page = await ctx.newPage();
  await navigate(page, base + '/');
  const token = await page.evaluate(() => getComputedStyle(document.documentElement).getPropertyValue('--bg-pattern-mobile-display').trim());
  const shown = await page.evaluate(() => getComputedStyle(document.querySelector('.page-home .home-nearby'), '::before').display);
  await page.evaluate(() => document.documentElement.style.setProperty('--bg-pattern-mobile-display', 'none'));
  const hidden = await page.evaluate(() => ['.page-home .home-nearby', '.page-home .quote', '.page-home .footer__legal']
    .map(s => getComputedStyle(document.querySelector(s), '::before').display));
  add('Ф1 token --bg-pattern-mobile-display: block shows, none hides all', token === 'block' && shown === 'block' && hidden.every(v => v === 'none'), {token, shown, hidden}, 390);
  const layers = await page.evaluate(() => [...new Set([...document.styleSheets].flatMap(s => { try { return [...s.cssRules]; } catch (_) { return []; } })
    .flatMap(r => (r.cssText.match(/mobile-backgrounds\/lite\/[\w-]+\.svg/g) || [])))]);
  let darkest = 255;
  for (const layer of layers) {
    const svg = await (await page.request.get(`${base}/static/img/${layer}`)).text();
    darkest = Math.min(darkest, await page.evaluate(async svg => {
      const img = new Image(); img.src = 'data:image/svg+xml;base64,' + btoa(svg); await img.decode();
      const c = document.createElement('canvas'); c.width = img.width; c.height = img.height; const x = c.getContext('2d');
      x.fillStyle = '#F7F0E6'; x.fillRect(0, 0, c.width, c.height); x.drawImage(img, 0, 0);
      const d = x.getImageData(0, 0, c.width, c.height).data; let min = 255;
      for (let i = 0; i < d.length; i += 4) min = Math.min(min, (d[i] + d[i + 1] + d[i + 2]) / 3);
      return min;
    }, svg));
  }
  const lin = v => { v /= 255; return v <= .03928 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4; };
  const L = rgb => .2126 * lin(rgb[0]) + .7152 * lin(rgb[1]) + .0722 * lin(rgb[2]);
  const ratio = (L([darkest, darkest, darkest]) + .05) / (L(TEXT) + .05);
  add(`Ф1 ${layers.length} light layers: darkest line ${Math.round(darkest)}, text #494949 contrast ${ratio.toFixed(2)} ≥ 4.5`, layers.length === 12 && ratio >= 4.5, {darkest, ratio}, 390);
  await ctx.close();
  // Desktop: background-only shots equal the baseline taken before the changes.
  const now = path.join(out, 'bg-desktop');
  const layersNow = await bg.captureDesktop(browser, base, now);
  const before = JSON.parse(fs.readFileSync(path.join(baseline, 'layers-1440.json'), 'utf8'));
  const cmpCtx = await browser.newContext(), cmp = await cmpCtx.newPage();
  // A layer may only move together with content that Ф4/Ф5 moved on purpose: by exactly the page-height
  // change. Everything above the first moved layer must be pixel-identical.
  for (const route of bg.DESKTOP_ROUTES) {
    const file = `bg-1440-${bg.slug(route)}.png`, a = before[route], b = layersNow[route];
    const size = await compareImages(cmp, path.join(baseline, file), path.join(now, file), 0);
    const delta = size.missing ? null : size.heights[1] - size.heights[0];
    const same = a.length === b.length && a.every((l, i) => b[i].key === l.key && b[i].src.split('/static/')[1] === l.src.split('/static/')[1] && b[i].x === l.x && b[i].w === l.w && b[i].h === l.h);
    const moved = a.filter((l, i) => b[i] && b[i].y !== l.y);
    const consistent = a.every((l, i) => b[i] && (b[i].y === l.y || Math.abs(b[i].y - l.y - delta) <= 1));
    const limit = moved.length ? Math.max(0, Math.min(...moved.map(l => l.y))) : Infinity;
    const res = await compareImages(cmp, path.join(baseline, file), path.join(now, file), limit);
    add(`Ф1 desktop background ${route}: layers unchanged${moved.length ? `, ${moved.length} moved with content by ${delta}px` : ''}, pixels identical above ${res.compared}px`,
      !res.missing && same && consistent && res.diff === 0, {res, delta, moved: moved.map(l => l.key)}, 1440);
  }
  await cmpCtx.close();
}

// ---------- Ф2 ----------
async function f2(browser) {
  for (const width of [768, 900, 1024, 1280, 1440, 1920]) {
    const ctx = await context(browser, width, 900, {keepCookies: true}), page = await ctx.newPage();
    await navigate(page, base + '/');
    await page.waitForSelector('[data-cookie-banner]:not([hidden])', {timeout: 5000}).catch(() => {});
    const m = await page.evaluate(() => {
      const r = e => { const q = e.getBoundingClientRect(); return {x: q.x, y: q.y, w: q.width, h: q.height, bottom: q.bottom}; };
      const bar = document.querySelector('.header__bar'), cookie = document.querySelector('[data-cookie-banner]');
      const cta = document.querySelector('.header__aside .btn');
      return {visible: !cookie.hidden, bar: r(bar), cookie: r(cookie), gap: innerHeight - cookie.getBoundingClientRect().bottom,
        barRadius: getComputedStyle(bar).borderRadius, cookieRadius: getComputedStyle(cookie).borderRadius,
        accept: r(cookie.querySelector('.cookie-accept')), cta: cta.offsetParent ? r(cta) : null,
        font: getComputedStyle(cookie.querySelector('.cookie-text')).fontSize,
        navFont: (document.querySelector('.nav--desktop .nav__link') && getComputedStyle(document.querySelector('.nav--desktop .nav__link')).fontSize) || '',
        overflow: document.documentElement.scrollWidth - innerWidth};
    });
    add('Ф2 cookie banner shown, no horizontal scroll', m.visible && m.overflow <= 0, m, width);
    if (width >= 1280) {
      add('Ф2 cookie banner = header (width, height, radius, bottom gap = header top, text = menu font, accept = CTA height)',
        Math.abs(m.cookie.w - m.bar.w) <= 1 && Math.abs(m.cookie.h - m.bar.h) <= 1 && m.cookieRadius === m.barRadius &&
        Math.abs(m.gap - m.bar.y) <= 1 && Math.abs(m.cookie.x - m.bar.x) <= 1 && m.font === m.navFont && m.cta && Math.abs(m.accept.h - m.cta.h) <= 1, m, width);
    }
    if (width === 1440) {
      await page.screenshot({path: path.join(out, 'cookie-1440.png')});
      await page.click('[data-cookie-accept]');
      await page.reload(); await page.waitForTimeout(600);
      const stored = await page.evaluate(() => ({hidden: document.querySelector('[data-cookie-banner]').hidden, value: localStorage.getItem('bs-cookie-consent-v1')}));
      add('Ф2 consent is remembered after reload', stored.hidden && !!stored.value, stored, width);
    }
    await ctx.close();
  }
}

// ---------- Ф4 ----------
async function measureMotto(browser, width) {
  const ctx = await context(browser, width, 900), page = await ctx.newPage();
  await navigate(page, base + '/o-nas/');
  await page.evaluate(() => document.fonts.ready);
  await page.addStyleTag({content: '.about-background{display:none!important}'});
  const box = await page.evaluate(() => {
    const m = document.querySelector('.about-motto'); m.scrollIntoView({block: 'center'});
    const r = m.getBoundingClientRect();
    return {top: r.top, height: r.height, lines: [...m.querySelectorAll('.about-motto__line')].map(l => { const q = l.getBoundingClientRect(); return [q.top, q.bottom]; })};
  });
  await page.waitForTimeout(200);
  const top = Math.max(0, Math.floor(box.top) - 12), height = Math.ceil(box.height) + 24;
  const png = await page.screenshot({clip: {x: 0, y: top, width, height}});
  const rows = box.lines.map(([a, b]) => [Math.floor(a) - top, Math.ceil(b) - top]);
  const ink = await pixels(page, png, inkEdges, rows);
  await ctx.close();
  const left = Math.min(...ink.lines.map(l => l.left)), right = Math.max(ink.heartRight, ...ink.lines.map(l => l.right));
  return {lines: ink.lines.length, line1: ink.lines[0].left, line2: ink.lines[1] && ink.lines[1].left, heartRight: ink.heartRight, center: (left + right) / 2};
}

async function f4(browser) {
  for (const width of [1440, 390]) {
    const m = await measureMotto(browser, width), ref = MOTTO[width];
    add(`Ф4 slogan vs ${ref.source}: lines ${m.line1}/${m.line2}, heart ${m.heartRight}, center ${m.center} (±2)`,
      m.lines === 2 && ['line1', 'line2', 'heartRight', 'center'].every(k => Math.abs(m[k] - ref[k]) <= 2), {site: m, mockup: ref}, width);
  }
  for (const width of [1280, 1920, 768, 320]) {
    const m = await measureMotto(browser, width), ref = width < 700 ? MOTTO[390] : MOTTO[1440];
    const want = width / 2 - (ref === MOTTO[390] ? 195 - ref.center : 720 - ref.center);
    add(`Ф4 slogan centred: ${m.center} vs ${want} (±2), two lines`, m.lines === 2 && Math.abs(m.center - want) <= 2, m, width);
  }
}

// ---------- Ф5 ----------
async function settleScroll(page) {
  let last = -1, same = 0;
  for (let i = 0; i < 60 && same < 5; i++) { await page.waitForTimeout(100); const y = await page.evaluate(() => scrollY); same = y === last ? same + 1 : 0; last = y; }
  return last;
}

async function f5(browser) {
  for (const [width, height] of [[1440, 900], [1280, 720], [1920, 1080]]) {
    const ctx = await context(browser, width, height), page = await ctx.newPage();
    await navigate(page, base + '/territoriya/');
    const firstBlock = await page.evaluate(() => {
      const h = document.querySelector('main > :first-child h1, main > :first-child .section__title');
      return h.getBoundingClientRect().top - document.querySelector('.header__bar').getBoundingClientRect().bottom;
    });
    for (const mode of ['wheel', 'trackpad']) {
      await navigate(page, base + '/');
      await page.waitForTimeout(400);
      await page.mouse.move(width / 2, height / 2);
      if (mode === 'wheel') await page.mouse.wheel(0, 200);
      // Trackpad: a burst of small deltas (scroll-intent needs 120 px within 400 ms).
      else for (let i = 0; i < 16; i++) { await page.mouse.wheel(0, 15); await page.waitForTimeout(8); }
      const y = await settleScroll(page);
      const m = await page.evaluate(() => {
        const t = e => e && e.getBoundingClientRect().top;
        return {header: document.querySelector('.header__bar').getBoundingClientRect().bottom,
          title: t(document.querySelector('.about .section__title')), photo: t(document.querySelector('.about__media')),
          heroBottom: document.querySelector('.hero').getBoundingClientRect().bottom, overflow: document.documentElement.scrollWidth - innerWidth};
      });
      const need = m.header + firstBlock - .5;
      add(`Ф5 ${mode}: stop ${y}, title ${m.title} / photo ${m.photo} ≥ header ${m.header.toFixed(1)} + ${firstBlock.toFixed(1)}`,
        y > 0 && m.heroBottom <= 0.5 && m.title >= need && m.photo >= need && m.overflow <= 0, {...m, firstBlock}, `${width}×${height}`);
      if (mode === 'wheel') {
        await page.screenshot({path: path.join(out, `snap-${width}.png`)});
        // Seam: with content hidden, every band of 12 rows above the photo still shows contour lines.
        await page.addStyleTag({content: bg.ONLY_BACKGROUND + '.header{visibility:hidden!important}'});
        await page.waitForTimeout(200);
        const png = await page.screenshot({clip: {x: 0, y: 0, width, height: Math.ceil(m.photo) + 60}});
        const gap = await pixels(page, png, (d, w, h) => {
          let run = 0, worst = 0;
          for (let y = 0; y < h; y++) {
            let line = false;
            for (let x = 0; x < w && !line; x++) { const i = (y * w + x) * 4; if (d[i] < 236 || d[i + 1] < 228) line = true; }
            run = line ? 0 : run + 1; worst = Math.max(worst, run);
          }
          return worst;
        });
        add(`Ф5 no empty band between sections (longest row run without contours: ${gap})`, gap < 12, {gap}, `${width}×${height}`);
      }
    }
    await page.goto('about:blank');
    await navigate(page, base + '/#houses');
    await page.waitForTimeout(600);
    const anchor = await page.evaluate(() => {
      const t = document.querySelector('#houses .section__title, #houses h2');
      return {title: t.getBoundingClientRect().top, header: document.querySelector('.header__bar').getBoundingClientRect().bottom};
    });
    add('Ф5 anchor /#houses: title below the header', anchor.title >= anchor.header + 20, anchor, `${width}×${height}`);
    await ctx.close();
  }
}

// ---------- Regression ----------
async function regression(browser) {
  const errors = [];
  for (const width of [320, 390, 768, 1024, 1440, 1920]) {
    const ctx = await context(browser, width, 900), page = await ctx.newPage(), bad = [];
    page.on('pageerror', e => errors.push(`${width} ${page.url()} ${e}`));
    page.on('console', m => { if (m.type() === 'error' && (m.location().url || '').startsWith(base)) errors.push(`${width} ${page.url()} ${m.text()}`); });
    for (const route of bg.ALL_ROUTES) {
      await navigate(page, base + route);
      const o = await page.evaluate(() => document.documentElement.scrollWidth - innerWidth);
      if (o > 0) bad.push(`${route} +${o}`);
    }
    add(`regression: no horizontal scroll on ${bg.ALL_ROUTES.length} pages`, bad.length === 0, bad, width);
    await navigate(page, base + '/');
    const opener = page.locator('[data-booking-open]:visible').first();
    await opener.scrollIntoViewIfNeeded(); await opener.click();
    await page.waitForTimeout(500);
    const open = await page.evaluate(() => { const d = document.querySelector('[data-booking-modal]'); return !!(d && d.open); });
    add('regression: booking window opens', open, {}, width);
    await ctx.close();
  }
  add('regression: no page errors / own-origin console errors', errors.length === 0, errors);
}

(async () => {
  fs.mkdirSync(out, {recursive: true});
  const browser = await chromium.launch({channel: process.env.CHROME_PATH ? undefined : 'msedge', executablePath: process.env.CHROME_PATH || undefined});
  try {
    if (want('f1')) await f1(browser);
    if (want('f2')) await f2(browser);
    if (want('f3')) for (const width of [1440, 390]) for (const r of await checkValues(browser, base, width)) add(r.name, r.pass, r.detail, width);
    if (want('f4')) await f4(browser);
    if (want('f5')) await f5(browser);
    if (want('regression')) await regression(browser);
  } catch (error) {
    add('script error', false, String(error.stack || error));
  } finally {
    await browser.close();
    fs.writeFileSync(path.join(out, 'results.json'), JSON.stringify({base, results}, null, 2));
  }
  const failed = results.filter(r => !r.pass);
  console.log(`${results.length - failed.length}/${results.length} PASS`);
  if (failed.length) process.exitCode = 1;
})();
