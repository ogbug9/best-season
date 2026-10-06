'use strict';
// Ф1: desktop background layers must stay pixel-identical; mobile loads only light layers.
const fs = require('node:fs'), path = require('node:path');
const navigate = require('./pravki_05_10_navigation.cjs');

const DESKTOP_ROUTES = ['/', '/razmeshchenie/', '/razmeshchenie/domik-1/', '/razmeshchenie/domik-2/',
  '/razmeshchenie/domik-3/', '/razmeshchenie/domik-4/', '/akcii/', '/o-nas/'];
const ALL_ROUTES = [...DESKTOP_ROUTES, '/territoriya/', '/territoriya/razvlecheniya/', '/territoriya/chem-zanyatsya/',
  '/territoriya/uslugi/', '/territoriya/meropriyatiya/', '/interesnoe-ryadom/', '/o-nas/galereya/', '/o-nas/otzyvy/',
  '/o-nas/kontakty/', '/o-nas/voprosy/', '/o-nas/partneram/', '/kak-dobratsya/', '/pravila-bronirovaniya/',
  '/vyezdy-kompaniy/', '/rassylka/', '/oferta/', '/politika-konfidencialnosti/', '/soglasie-na-obrabotku/'];
const MOBILE_ROUTES = ALL_ROUTES;
const ONLY_BACKGROUND = `body *{visibility:hidden!important;animation:none!important;transition:none!important}
.home-bg,.home-bg *,.about-background,.about-background *{visibility:visible!important}`;
const slug = route => route.replace(/\W+/g, '-').replace(/^-|-$/g, '') || 'home';

async function settle(page) {
  await page.evaluate(() => document.fonts.ready);
  await page.evaluate(async () => {
    for (let y = 0; y < document.documentElement.scrollHeight; y += 700) { scrollTo(0, y); await new Promise(r => setTimeout(r, 40)); }
    scrollTo(0, 0);
    const loaded = Promise.all([...document.querySelectorAll('.home-bg img')].map(img => img.complete ? 0 : new Promise(r => { img.onload = img.onerror = r; })));
    await Promise.race([loaded, new Promise(r => setTimeout(r, 8000))]);
    await new Promise(r => setTimeout(r, 300));
  });
}

// Desktop layers: document-space rectangles and sources, plus a background-only full-page shot.
async function desktopLayers(page) {
  return page.evaluate(() => [...document.querySelectorAll('.home-bg__layer, .about-background svg')]
    .filter(el => getComputedStyle(el).display !== 'none' && el.getBoundingClientRect().width > 0)
    .map(el => { const r = el.getBoundingClientRect(); return {
      key: el.getAttribute('class'), src: el.currentSrc || '',
      x: Math.round(r.left + scrollX), y: Math.round(r.top + scrollY), w: Math.round(r.width), h: Math.round(r.height)}; }));
}

async function captureDesktop(browser, base, dir) {
  fs.mkdirSync(dir, {recursive: true});
  const context = await browser.newContext({viewport: {width: 1440, height: 900}, deviceScaleFactor: 1});
  await context.addInitScript(() => { try { localStorage.setItem('bs-cookie-consent-v1', 'dismissed'); } catch (_) {} });
  const page = await context.newPage(), result = {};
  for (const route of DESKTOP_ROUTES) {
    await navigate(page, base + route); await settle(page);
    await page.waitForFunction(() => !document.querySelector('[data-about-art]') || document.querySelector('.about-art--desktop'));
    result[route] = await desktopLayers(page);
    await page.addStyleTag({content: ONLY_BACKGROUND});
    await page.waitForTimeout(200);
    await page.screenshot({path: path.join(dir, `bg-1440-${slug(route)}.png`), fullPage: true});
  }
  await context.close();
  fs.writeFileSync(path.join(dir, 'layers-1440.json'), JSON.stringify(result, null, 2));
  return result;
}

function samePng(a, b) {
  if (!fs.existsSync(a) || !fs.existsSync(b)) return false;
  return Buffer.compare(fs.readFileSync(a), fs.readFileSync(b)) === 0;
}

async function mobileNetwork(browser, base, width) {
  const context = await browser.newContext({viewport: {width, height: 844}, isMobile: true, hasTouch: true, deviceScaleFactor: 1});
  await context.addInitScript(() => { try { localStorage.setItem('bs-cookie-consent-v1', 'dismissed'); } catch (_) {} });
  const page = await context.newPage(), rows = [];
  for (const route of MOBILE_ROUTES) {
    const hits = [];
    const onResponse = async res => {
      const url = res.url();
      if (!/\/static\/img\/(home-backgrounds|mobile-backgrounds|about)\//.test(url) && !/about-art/.test(url)) return;
      let size = 0; try { size = (await res.body()).length; } catch (_) {}
      if (!size) { try { size = (await (await page.request.get(url)).body()).length; } catch (_) {} } // cached response
      hits.push({url: url.replace(base, ''), size});
    };
    page.on('response', onResponse);
    await navigate(page, base + route); await settle(page);
    await page.waitForTimeout(400);
    page.off('response', onResponse);
    const inline = await page.evaluate(() => [...document.querySelectorAll('.about-background svg')].map(s => ({cls: s.getAttribute('class'), size: s.outerHTML.length})));
    const svg = hits.filter(h => /\.svg/.test(h.url));
    const desktop = hits.filter(h => /home-backgrounds|about-art-desktop|decoration-desktop/.test(h.url))
      .concat(inline.filter(s => /desktop/.test(s.cls)).map(s => ({url: 'inline ' + s.cls, size: s.size})));
    const total = svg.reduce((s, h) => s + h.size, 0) + inline.reduce((s, h) => s + h.size, 0);
    rows.push({route, width, svg, inline, desktop, total, pass: desktop.length === 0 && total <= 1024 * 1024});
  }
  await context.close();
  return rows;
}

module.exports = {captureDesktop, desktopLayers, samePng, mobileNetwork, settle, DESKTOP_ROUTES, ALL_ROUTES, ONLY_BACKGROUND, slug};

if (require.main === module) {
  const {chromium} = require('playwright');
  const [base, dir] = process.argv.slice(2);
  (async () => {
    const browser = await chromium.launch({channel: 'msedge'});
    try { await captureDesktop(browser, base.replace(/\/$/, ''), path.resolve(dir)); } finally { await browser.close(); }
    console.log('baseline saved', dir);
  })().catch(e => { console.error(e); process.exitCode = 1; });
}
