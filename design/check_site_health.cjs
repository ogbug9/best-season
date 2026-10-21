'use strict';
// Site health over every sitemap page at 390 and 1440 (no forms submitted):
// console errors, failed same-origin requests, broken images, horizontal scroll,
// h1 count, img without alt, and the status of every internal link found.
// Usage: node design/check_site_health.cjs <base-url> [out.json]
const fs = require('node:fs');
const {chromium} = require('playwright');

const base = (process.argv[2] || 'http://localhost:8010').replace(/\/$/, '');
const outFile = process.argv[3];
const origin = new URL(base).origin;
const problems = [];
const add = (width, path, kind, detail) => { problems.push({width, path, kind, detail}); console.log(`FAIL ${width} ${path} ${kind} ${String(detail).slice(0, 300)}`); };

async function launch() {
  try { return await chromium.launch(); } catch (_) { return chromium.launch({channel: 'msedge'}); }
}

async function go(page, url) {
  for (let attempt = 0; ; attempt++) {
    try { return await page.goto(url, {waitUntil: 'domcontentloaded', timeout: 90000}); } catch (error) { if (attempt >= 2) throw error; await page.waitForTimeout(3000); }
  }
}

(async () => {
  const browser = await launch();
  const xml = await (await fetch(`${base}/sitemap.xml`)).text();
  const paths = [...xml.matchAll(/<loc>([^<]+)<\/loc>/g)].map(m => new URL(m[1]).pathname);
  const links = new Set();
  for (const width of [390, 1440]) {
    const mobile = width < 700;
    const ctx = await browser.newContext({viewport: {width, height: mobile ? 844 : 900}, isMobile: mobile, hasTouch: mobile});
    await ctx.addInitScript(() => { try { localStorage.setItem('bs-cookie-consent-v1', 'dismissed'); } catch (_) {} });
    const page = await ctx.newPage();
    let current = '';
    page.on('console', msg => { if (msg.type() === 'error' && !/favicon|yandex|mc\.yandex|kontur|metrika/i.test(msg.text())) add(width, current, 'console', msg.text()); });
    page.on('pageerror', error => add(width, current, 'js', error.message));
    page.on('response', response => {
      const url = response.url();
      if (url.startsWith(origin) && response.status() >= 400) add(width, current, `http ${response.status()}`, url);
    });
    for (const path of paths) {
      current = path;
      const response = await go(page, base + path);
      if (!response || response.status() >= 400) { add(width, path, 'page', response && response.status()); continue; }
      // Scroll through so lazy images load.
      await page.evaluate(async () => {
        for (let y = 0; y < document.body.scrollHeight; y += 700) { window.scrollTo(0, y); await new Promise(r => setTimeout(r, 60)); }
        window.scrollTo(0, 0);
      });
      await page.waitForTimeout(800);
      const r = await page.evaluate(() => ({
        overflow: document.documentElement.scrollWidth - window.innerWidth,
        h1: document.querySelectorAll('h1').length,
        noAlt: [...document.querySelectorAll('img')].filter(img => !img.hasAttribute('alt')).map(img => img.currentSrc || img.src).slice(0, 3),
        broken: [...document.querySelectorAll('img')].filter(img => img.complete && img.naturalWidth === 0 && (img.currentSrc || img.src) && !(img.currentSrc || img.src).startsWith('data:') && img.offsetParent !== null).map(img => img.currentSrc || img.src).slice(0, 5),
        links: [...document.querySelectorAll('a[href]')].map(a => a.href),
        junk: (document.body.innerText.match(/Текст ожидается|Lorem ipsum|TODO|\{\{|\{%|None|undefined|NaN/g) || []).slice(0, 5),
        low: (() => {
          // Text contrast against the nearest opaque background (≥ 4.5, large ≥ 3).
          const parse = c => { const m = (c.match(/[\d.]+/g) || [0, 0, 0, 0]).map(Number); return {rgb: m.slice(0, 3), a: m.length > 3 ? m[3] : 1}; };
          const lum = rgb => { const v = rgb.map(x => { x /= 255; return x <= 0.03928 ? x / 12.92 : ((x + 0.055) / 1.055) ** 2.4; }); return 0.2126 * v[0] + 0.7152 * v[1] + 0.0722 * v[2]; };
          const bgOf = el => {
            for (let node = el; node && node.nodeType === 1; node = node.parentElement) {
              const cs = getComputedStyle(node);
              if (cs.backgroundImage !== 'none' && !cs.backgroundImage.startsWith('linear-gradient')) return null;  // текст на фото — не меряем
              const {rgb, a} = parse(cs.backgroundColor);
              if (a >= 0.95) return rgb;
            }
            return [247, 240, 230];
          };
          const out = [];
          for (const el of document.querySelectorAll('main *, footer *')) {
            if (!el.offsetWidth || el.closest('[aria-disabled="true"], [disabled], picture, svg, .kontur, [class*="kontur"], [hidden]')) continue;
            if (![...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim())) continue;
            const cs = getComputedStyle(el);
            if (cs.visibility === 'hidden' || Number(cs.opacity) === 0) continue;
            if (el.offsetWidth <= 2 || el.offsetHeight <= 2 || cs.clip !== 'auto' || cs.clipPath !== 'none') continue;  // visually-hidden
            const bg = bgOf(el); if (!bg) continue;
            let op = 1; for (let node = el; node && node.nodeType === 1; node = node.parentElement) op *= Number(getComputedStyle(node).opacity);
            if (op < 0.2) continue;  // элемент в анимации появления
            const {rgb, a} = parse(cs.color);
            const mix = rgb.map((v, i) => v * a * op + bg[i] * (1 - a * op));
            const [x, y] = [lum(mix), lum(bg)].sort((p, q) => p - q);
            const ratio = (y + 0.05) / (x + 0.05);
            const size = parseFloat(cs.fontSize), bold = Number(cs.fontWeight) >= 600;
            const need = size >= 24 || (bold && size >= 18.66) ? 3 : 4.5;
            if (ratio < need - 0.05) out.push(`${el.tagName.toLowerCase()}.${String(el.className).split(' ')[0]} «${el.textContent.trim().slice(0, 24)}» ${ratio.toFixed(2)}`);
          }
          return [...new Set(out)].slice(0, 6);
        })(),
      }));
      if (r.overflow > 0) add(width, path, 'overflow', r.overflow);
      if (r.h1 !== 1) add(width, path, 'h1', r.h1);
      if (r.noAlt.length) add(width, path, 'alt', r.noAlt.join(' '));
      if (r.broken.length) add(width, path, 'image', r.broken.join(' '));
      if (r.low.length) add(width, path, 'contrast', r.low.join(' | '));
      if (r.junk.length) add(width, path, 'junk', r.junk.join(' '));
      r.links.filter(href => href.startsWith(origin)).forEach(href => links.add(href.split('#')[0]));
    }
    await ctx.close();
  }
  // Остальные ширины — только горизонтальная прокрутка.
  for (const width of [320, 700, 768, 1024, 1920]) {
    const mobile = width < 700;
    const ctx = await browser.newContext({viewport: {width, height: 900}, isMobile: mobile, hasTouch: mobile});
    const page = await ctx.newPage();
    for (const path of paths) {
      await go(page, base + path);
      await page.waitForTimeout(400);
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
      if (overflow > 0) add(width, path, 'overflow', overflow);
    }
    await ctx.close();
  }
  await browser.close();
  for (const href of links) {
    try {
      const response = await fetch(href, {redirect: 'follow'});
      if (response.status >= 400) add('-', href, `link ${response.status}`, '');
    } catch (error) { add('-', href, 'link', error.message); }
  }
  console.log(`pages: ${paths.length}, internal links: ${links.size}, problems: ${problems.length}`);
  if (outFile) fs.writeFileSync(outFile, JSON.stringify(problems, null, 1));
  process.exit(problems.length ? 1 : 0);
})();
