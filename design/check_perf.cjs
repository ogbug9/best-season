'use strict';
// Rough mobile performance (Lighthouse-like throttling: 4× CPU, 150 ms RTT, 1.6 Mbps down).
// Not a PageSpeed score — LCP / CLS / TBT for a quick comparison when the PSI quota is out.
// Usage: node design/check_perf.cjs <base-url> path/ [path/ ...]  (без ведущего слэша — Git Bash его переписывает)
const {chromium} = require('playwright');

const [baseArg, ...paths] = process.argv.slice(2);
const base = baseArg.replace(/\/$/, '');

async function launch() {
  try { return await chromium.launch(); } catch (_) { return chromium.launch({channel: 'msedge'}); }
}

(async () => {
  const browser = await launch();
  for (const path of paths.length ? paths : ['/']) {
    const ctx = await browser.newContext({viewport: {width: 412, height: 823}, deviceScaleFactor: 1.75, isMobile: true, hasTouch: true});
    const page = await ctx.newPage();
    const cdp = await ctx.newCDPSession(page);
    await cdp.send('Network.enable');
    await cdp.send('Network.setCacheDisabled', {cacheDisabled: true});
    await cdp.send('Network.emulateNetworkConditions', {offline: false, latency: 150, downloadThroughput: 1.6 * 1024 * 1024 / 8, uploadThroughput: 750 * 1024 / 8});
    await cdp.send('Emulation.setCPUThrottlingRate', {rate: 4});
    await page.addInitScript(() => {
      window.__perf = {lcp: 0, cls: 0, tbt: 0};
      new PerformanceObserver(list => { for (const e of list.getEntries()) window.__perf.lcp = e.startTime; }).observe({type: 'largest-contentful-paint', buffered: true});
      new PerformanceObserver(list => { for (const e of list.getEntries()) if (!e.hadRecentInput) window.__perf.cls += e.value; }).observe({type: 'layout-shift', buffered: true});
      new PerformanceObserver(list => { for (const e of list.getEntries()) window.__perf.tbt += Math.max(0, e.duration - 50); }).observe({type: 'longtask', buffered: true});
    });
    const start = Date.now();
    await page.goto(`${base}/${path.replace(/^\//, '')}`, {waitUntil: 'load', timeout: 180000});
    await page.waitForTimeout(3000);
    const perf = await page.evaluate(() => window.__perf);
    const bytes = await page.evaluate(() => performance.getEntriesByType('resource').reduce((sum, e) => sum + (e.transferSize || 0), 0));
    console.log(`${path} LCP ${(perf.lcp / 1000).toFixed(1)} s, CLS ${perf.cls.toFixed(3)}, TBT ${Math.round(perf.tbt)} ms, load ${((Date.now() - start) / 1000).toFixed(1)} s, ${Math.round(bytes / 1024)} KB`);
    await ctx.close();
  }
  await browser.close();
})();
