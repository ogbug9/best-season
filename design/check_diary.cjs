'use strict';
// 20.10 Н2: «Дневник Сезона» — индекс и записи. No forms are submitted.
// Usage: node design/check_diary.cjs <base-url>
// 320/390/768/1024/1440/1920: no horizontal scroll, one h1, alt on every img,
// text contrast ≥ 4.5 (≥ 3 for large text); SEO tags; at 1440 the index matches News.svg (±2 px).
const {chromium} = require('playwright');

const base = (process.argv[2] || 'http://localhost:8010').replace(/\/$/, '');
const WIDTHS = [320, 390, 768, 1024, 1440, 1920];
let failed = 0;
const report = (pass, text) => { if (!pass) failed++; console.log(`${pass ? 'PASS' : 'FAIL'} ${text}`); };

async function launch() {
  try { return await chromium.launch(); } catch (_) { return chromium.launch({channel: 'msedge'}); }
}

function audit() {
  const parse = c => { const m = c.match(/[\d.]+/g).map(Number); return {rgb: m.slice(0, 3), a: m.length > 3 ? m[3] : 1}; };
  const lum = rgb => { const v = rgb.map(x => { x /= 255; return x <= 0.03928 ? x / 12.92 : ((x + 0.055) / 1.055) ** 2.4; }); return 0.2126 * v[0] + 0.7152 * v[1] + 0.0722 * v[2]; };
  const bg = [247, 240, 230];
  const low = [];
  for (const el of document.querySelectorAll('main h1, main h2, main h3, main p, main time, main a, main span, main li, main blockquote')) {
    if (!el.offsetWidth || el.closest('[aria-disabled="true"], .is-current, picture') || !el.childNodes.length) continue;
    if (![...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim())) continue;
    const cs = getComputedStyle(el); const {rgb, a} = parse(cs.color);
    const op = Number(cs.opacity);
    const mix = rgb.map((v, i) => v * a * op + bg[i] * (1 - a * op));
    const [x, y] = [lum(mix), lum(bg)].sort((p, q) => p - q);
    const ratio = (y + 0.05) / (x + 0.05);
    const size = parseFloat(cs.fontSize), bold = Number(cs.fontWeight) >= 600;
    const need = size >= 24 || (bold && size >= 18.66) ? 3 : 4.5;
    if (ratio < need) low.push(`${el.tagName}.${el.className} ${ratio.toFixed(2)}`);
  }
  return {
    overflow: document.documentElement.scrollWidth - window.innerWidth,
    h1: document.querySelectorAll('h1').length,
    noAlt: [...document.querySelectorAll('main img')].filter(img => !img.hasAttribute('alt')).length,
    low,
  };
}

(async () => {
  const browser = await launch();
  const xml = await (await fetch(`${base}/sitemap.xml`)).text();
  const urls = [...xml.matchAll(/<loc>([^<]+)<\/loc>/g)].map(m => new URL(m[1]).pathname).filter(p => p.startsWith('/o-nas/dnevnik/'));
  report(urls.includes('/o-nas/dnevnik/') && urls.length >= 4, `sitemap: ${urls.length} diary URLs`);
  const entry = urls.find(p => p !== '/o-nas/dnevnik/') || '/o-nas/dnevnik/novyj-god/';
  for (const width of WIDTHS) {
    const mobile = width < 700;
    const ctx = await browser.newContext({viewport: {width, height: mobile ? 844 : 900}, isMobile: mobile, hasTouch: mobile});
    await ctx.addInitScript(() => { try { localStorage.setItem('bs-cookie-consent-v1', 'dismissed'); } catch (_) {} });
    const page = await ctx.newPage();
    for (const path of ['/o-nas/dnevnik/', entry]) {
      await page.goto(base + path, {waitUntil: 'load'});
      await page.waitForTimeout(300);
      const r = await page.evaluate(audit);
      report(r.overflow <= 0 && r.h1 === 1 && !r.noAlt && !r.low.length, `${width} ${path} ${JSON.stringify(r)}`);
    }
    if (width === 1440) {
      await page.goto(`${base}/o-nas/dnevnik/`, {waitUntil: 'load'});
      const box = await page.evaluate(() => {
        const q = s => { const r = document.querySelector(s).getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y + scrollY), Math.round(r.width), Math.round(r.height)]; };
        return {photo: q('.diary-card__photo'), title: q('.diary-card__title'), lead: q('.diary-index__lead')};
      });
      // News.svg: фото 100,406 400×240; строка названия с 664 (кегль 24/29, верх букв 670.7).
      const near = (a, b) => a.every((v, i) => Math.abs(v - b[i]) <= 2);
      report(near(box.photo, [100, 406, 400, 240]) && Math.abs(box.title[1] - 666) <= 2, `1440 index geometry ${JSON.stringify(box)}`);
    }
    await ctx.close();
  }
  // SEO: свой title/description, og:image JPEG 1200×630 (если вариант подготовлен), Article + BreadcrumbList.
  const html = await (await fetch(base + entry)).text();
  const meta = name => (html.match(new RegExp(`<meta (?:name|property)="${name}" content="([^"]*)"`)) || [])[1] || '';
  const types = [...html.matchAll(/"@type": "(\w+)"/g)].map(m => m[1]);
  report(types.includes('Article') && types.includes('BreadcrumbList'), `${entry} JSON-LD ${types.join(',')}`);
  report(meta('og:type') === 'article' && meta('description').length > 30, `${entry} og:type/description`);
  const og = meta('og:image');
  // Wagtail не увеличивает исходник: при фото меньше 1200 px превью меньше, но в той же пропорции 1200:630.
  const w = Number(meta('og:image:width')), h = Number(meta('og:image:height'));
  report(/\.jpe?g$/i.test(og) && w >= 600 && Math.abs(w / h - 1200 / 630) < 0.02, `${entry} og:image ${w}×${h} ${og}`);
  if (w && w < 1200) console.log(`NOTE ${entry}: исходник обложки меньше 1200 px — превью ${w}×${h}`);
  const index = await (await fetch(`${base}/o-nas/dnevnik/`)).text();
  const title = s => (s.match(/<title>([^<]*)<\/title>/) || [])[1];
  report(title(index) !== title(html), `titles differ: «${title(index)}» / «${title(html)}»`);
  await browser.close();
  console.log(failed ? `FAIL ${failed}` : 'all PASS');
  process.exit(failed ? 1 : 0);
})();
