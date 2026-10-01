"""Две проверки фото на страницах сайта.

1. Растяжение: файл меньше окна, в котором показан. Считается как
   (размер окна / размер файла) × плотность экрана с учётом object-fit: cover.
   Больше 1 — браузер дорисовывает пиксели, фото мылится. Порог — для
   плотности 2× (Retina, большинство телефонов).
2. Обрезка сверху: блок <img> больше видимого окна (родитель с overflow
   режет его). Так object-fit не работает, и вместо середины кадра виден верх.

    python design/check_images.py --url http://127.0.0.1:8000
"""
import argparse
import sys

from playwright.sync_api import sync_playwright

PAGES = ['/', '/razmeshchenie/', '/razmeshchenie/domik-1/', '/razmeshchenie/domik-2/',
         '/razmeshchenie/domik-3/', '/razmeshchenie/domik-4/', '/akcii/', '/territoriya/',
         '/territoriya/uslugi/', '/interesnoe-ryadom/', '/o-nas/galereya/', '/o-nas/otzyvy/']
MODES = [('десктоп 1440@2x', 1440, 900, 2), ('мобильный 390@3x', 390, 844, 3)]
THRESHOLD = 1.15

# naturalWidth у картинки из srcset уже поделён на плотность, поэтому
# реальный размер файла берём через отдельный Image() без srcset.
MEASURE = r"""async () => {
  document.querySelectorAll('img').forEach(i => i.loading = 'eager');
  for (let y = 0; y < document.body.scrollHeight; y += 600) { scrollTo(0, y); await new Promise(r => setTimeout(r, 30)); }
  await Promise.all([...document.images].map(i => i.complete ? 0 : new Promise(r => { i.onload = i.onerror = r; })));
  const real = {};
  await Promise.all([...new Set([...document.images].map(i => i.currentSrc).filter(Boolean))].map(src =>
    new Promise(res => { const t = new Image(); t.onload = () => { real[src] = [t.naturalWidth, t.naturalHeight]; res(); }; t.onerror = res; t.src = src; })));
  return [...document.images].map(i => {
    const r = i.getBoundingClientRect(), cs = getComputedStyle(i);
    if (r.width < 100 || r.left < 0 || r.right > innerWidth + 1 || /\.svg/.test(i.currentSrc) || !real[i.currentSrc]) return null;
    const [w, h] = real[i.currentSrc];
    const k = cs.objectFit === 'cover' ? Math.max(r.width / w, r.height / h)
            : cs.objectFit === 'contain' ? Math.min(r.width / w, r.height / h) : r.width / w;
    let c = {l: r.left, t: r.top, r: r.right, b: r.bottom};
    for (let el = i.parentElement; el && el !== document.documentElement; el = el.parentElement) {
      if (getComputedStyle(el).overflow !== 'visible') { const p = el.getBoundingClientRect();
        c = {l: Math.max(c.l, p.left), t: Math.max(c.t, p.top), r: Math.min(c.r, p.right), b: Math.min(c.b, p.bottom)}; }
    }
    const cut = (c.r - c.l > 0 && c.b - c.t > 0 && (r.height > c.b - c.t + 3 || r.width > c.r - c.l + 3))
      ? Math.round(r.width) + 'x' + Math.round(r.height) + ' в окне ' + Math.round(c.r - c.l) + 'x' + Math.round(c.b - c.t) : '';
    return {src: i.currentSrc.replace(location.origin, ''), file: w + 'x' + h,
            box: Math.round(r.width) + 'x' + Math.round(r.height), up2: +(k * 2).toFixed(2), cut};
  }).filter(Boolean);
}"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', default='http://127.0.0.1:8000')
    base = parser.parse_args().url.rstrip('/')
    worst, cut = {}, {}
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch()
        except Exception:
            # На Windows без скачанного Chromium — системный Edge
            browser = p.chromium.launch(channel='msedge')
        for mode, width, height, dpr in MODES:
            context = browser.new_context(viewport={'width': width, 'height': height}, device_scale_factor=dpr)
            page = context.new_page()
            for path in PAGES:
                page.goto(base + path, wait_until='load')
                for row in page.evaluate(MEASURE):
                    if row['cut']:
                        cut[(path, row['src'])] = f"{mode:17s} {path:26s} {row['cut']}  {row['src']}"
                    if row['up2'] > THRESHOLD and row['up2'] > worst.get(row['src'], {}).get('up2', 0):
                        worst[row['src']] = {**row, 'page': path, 'mode': mode}
            context.close()
        browser.close()
    for row in sorted(worst.values(), key=lambda r: -r['up2']):
        print(f"×{row['up2']:<5} {row['file']:>10} → {row['box']:>9}  {row['mode']:17s} {row['page']:26s} {row['src']}")
    print(f'\nРастянуто при плотности 2×: {len(worst)} (порог ×{THRESHOLD})')
    for line in cut.values():
        print('обрезка сверху:', line)
    print(f'Обрезано сверху: {len(cut)}')
    sys.exit(1 if worst or cut else 0)


if __name__ == '__main__':
    main()
