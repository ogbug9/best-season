'use strict';
// 20.10 Н1: on every page with FAQ all questions are closed after load (1440 and 390).
// Pages come from sitemap.xml, so new pages with FAQ are covered automatically.
// Usage: node design/check_faq_closed.cjs <base-url>
const {chromium} = require('playwright');

const base = (process.argv[2] || 'http://localhost:8010').replace(/\/$/, '');
let failed = 0;
const report = (pass, text) => { if (!pass) failed++; console.log(`${pass ? 'PASS' : 'FAIL'} ${text}`); };

async function launch() {
  try { return await chromium.launch(); } catch (_) { return chromium.launch({channel: 'msedge'}); }
}

(async () => {
  const browser = await launch();
  const xml = await (await fetch(`${base}/sitemap.xml`)).text();
  const paths = [...xml.matchAll(/<loc>([^<]+)<\/loc>/g)].map(m => new URL(m[1]).pathname);
  let withFaq = 0;
  for (const width of [1440, 390]) {
    const mobile = width < 700;
    const ctx = await browser.newContext({viewport: {width, height: mobile ? 844 : 900}, isMobile: mobile, hasTouch: mobile});
    await ctx.addInitScript(() => { try { localStorage.setItem('bs-cookie-consent-v1', 'dismissed'); } catch (_) {} });
    const page = await ctx.newPage();
    for (const path of paths) {
      await page.goto(base + path, {waitUntil: 'load'});
      await page.waitForTimeout(300);
      const state = await page.evaluate(() => ({
        items: document.querySelectorAll('.faq__item, details.t-faq__item').length,
        expanded: document.querySelectorAll('.faq__question[aria-expanded="true"]').length,
        open: document.querySelectorAll('.faq__item.is-open').length,
        visible: [...document.querySelectorAll('.faq__answer')].filter(a => !a.hidden && a.offsetHeight > 0).length,
        details: document.querySelectorAll('details.t-faq__item[open]').length,
      }));
      if (!state.items) continue;
      if (width === 1440) withFaq++;
      report(!state.expanded && !state.open && !state.visible && !state.details, `${width} ${path} ${JSON.stringify(state)}`);
    }
    // Click still opens with aria-expanded, and #q-N opens its answer.
    await page.goto(`${base}/o-nas/voprosy/`, {waitUntil: 'load'});
    const button = page.locator('.faq__question').first();
    await button.click();
    await page.waitForTimeout(400);
    report(await button.getAttribute('aria-expanded') === 'true'
      && await page.locator('.faq__answer').first().isVisible(), `${width} click opens first answer`);
    const id = await page.locator('.faq__item').nth(2).getAttribute('id');
    await page.goto(`${base}/o-nas/voprosy/#${id}`, {waitUntil: 'load'});
    await page.waitForTimeout(400);
    report(await page.locator(`#${id} .faq__question`).getAttribute('aria-expanded') === 'true'
      && await page.locator('.faq__item.is-open').count() === 1, `${width} #${id} opens only its answer`);
    await ctx.close();
  }
  await browser.close();
  console.log(`pages with FAQ: ${withFaq}; ${failed ? `FAIL ${failed}` : 'all PASS'}`);
  process.exit(failed ? 1 : 0);
})();
