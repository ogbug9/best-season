#!/usr/bin/env python3
"""Попиксельное сравнение страницы с эталоном из макета.

Зачем: «на глаз похоже» — не критерий приёмки. Этот скрипт берёт PNG,
выгруженный из Figma, рендерит нашу страницу в той же ширине и
показывает, где именно и на сколько они расходятся.

Важная оговорка: полного совпадения пиксель в пиксель не будет никогда,
пока на сайте нет тех же фотографий, что в макете. Поэтому скрипт
считает расхождение по горизонтальным полосам и выводит худшие — так
видно, какая секция уехала, даже когда картинки внутри разные.

Как получить эталон:
  В Figma выделить фрейм → Ctrl+Shift+E → PNG, масштаб 1x →
  положить в design/reference/<имя>.png

Запуск:
  python design/compare.py --ref design/reference/glavnaya.png \
                           --url http://127.0.0.1:8000/
  python design/compare.py --ref ... --url ... --band 100 --top 12

Что выводит:
  · общее расхождение в процентах
  · таблицу худших полос с координатой по вертикали
  · картинку сравнения в design/out/: эталон, наш рендер и карта различий
"""

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    import numpy as np
    from PIL import Image, ImageChops, ImageDraw
except ImportError:
    print("Нужен Pillow: pip install Pillow --break-system-packages")
    sys.exit(2)

OUT = Path(__file__).parent / "out"

SHOOTER = r"""
const { chromium } = require('playwright');
(async () => {
  const [, , url, width, outPath] = process.argv;
  const browser = await chromium.launch({
    executablePath: process.env.CHROME_PATH || undefined,
  });
  const page = await browser.newPage({
    viewport: { width: Number(width), height: 900 },
    deviceScaleFactor: 1,
  });
  await page.goto(url, { waitUntil: 'networkidle' });
  // Ждём шрифты: без этого первый кадр снимается запасной гарнитурой
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(400);
  await page.screenshot({ path: outPath, fullPage: true });
  await browser.close();
})().catch(e => { console.error(e); process.exit(2); });
"""


def shoot(url, width, path):
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
        f.write(SHOOTER)
        js = f.name
    proc = subprocess.run(["node", js, url, str(width), str(path)],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"Не удалось снять страницу:\n{proc.stderr[:1200]}")


def to_gray(im):
    """Сравниваем по яркости: разница в цвете фотографий нас не интересует,
    важно, съехала ли раскладка."""
    return im.convert("L")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", required=True, help="PNG-эталон, выгруженный из Figma")
    ap.add_argument("--url", default="http://127.0.0.1:8000/")
    ap.add_argument("--band", type=int, default=100,
                    help="высота полосы для замера, px")
    ap.add_argument("--top", type=int, default=12,
                    help="сколько худших полос показать")
    ap.add_argument("--name", default=None, help="имя файлов отчёта")
    ap.add_argument("--offset", type=int, default=0,
                    help="сдвинуть наш рендер на N px вниз перед сравнением: "
                         "нужно, когда эталон — не начало страницы")
    ap.add_argument("--whole", action="store_true",
                    help="эталон — вся страница целиком, а не фрагмент. "
                         "Тогда проверяется и общая высота")
    args = ap.parse_args()

    ref_path = Path(args.ref)
    if not ref_path.exists():
        print(f"Эталон не найден: {ref_path}")
        print("Выгрузите фрейм из Figma в PNG 1x и положите в design/reference/")
        return 2

    OUT.mkdir(parents=True, exist_ok=True)
    name = args.name or ref_path.stem

    ref = Image.open(ref_path).convert("RGB")
    print(f"Эталон: {ref_path.name}, {ref.width}×{ref.height}")

    shot_path = OUT / f"{name}-nash.png"
    shoot(args.url, ref.width, shot_path)
    shot = Image.open(shot_path).convert("RGB")
    print(f"Наш рендер: {shot.width}×{shot.height}")

    if shot.width != ref.width:
        # Ширина обязана совпадать — иначе сравнение бессмысленно
        shot = shot.resize((ref.width, round(shot.height * ref.width / shot.width)))

    # Сдвиг: эталон может быть куском страницы, а не её началом
    if args.offset:
        shot = shot.crop((0, args.offset, shot.width, shot.height))
        print(f"Сдвиг рендера на {args.offset} px вниз")

    dh = shot.height - ref.height
    if args.whole:
        print(f"Разница по высоте: {dh:+d} px "
              f"({dh / ref.height * 100:+.1f}% от эталона)")
        if abs(dh) > ref.height * 0.15:
            print("  ⚠ Высота расходится больше чем на 15%. Скорее всего дело "
                  "не в отступах, а в составе блоков или в отсутствующих "
                  "фотографиях.")
    else:
        print(f"Эталон — фрагмент страницы, сравниваю первые {ref.height} px "
              f"рендера. Для сверки всей страницы нужен --whole и полный "
              f"экспорт фрейма.")

    # Общая область. Добивать недостающее белым нельзя: белое поле само
    # даёт огромное расхождение и прячет настоящие различия.
    h = max(ref.height, shot.height) if args.whole else min(ref.height, shot.height)
    canvas_ref = Image.new("RGB", (ref.width, h), "white")
    canvas_ref.paste(ref.crop((0, 0, ref.width, min(h, ref.height))), (0, 0))
    canvas_shot = Image.new("RGB", (ref.width, h), "white")
    canvas_shot.paste(shot.crop((0, 0, ref.width, min(h, shot.height))), (0, 0))

    diff = ImageChops.difference(to_gray(canvas_ref), to_gray(canvas_shot))

    # numpy вместо попиксельных циклов: на странице в 8000px разница
    # между секундами и минутами, а сверка гоняется после каждой правки.
    arr = np.asarray(diff, dtype=np.float32) / 255.0
    bands = []
    for y0 in range(0, h, args.band):
        y1 = min(y0 + args.band, h)
        bands.append((y0, y1, float(arr[y0:y1].mean())))
    overall = float(arr.mean())

    # Сравнение с прошлым запуском: смысл сверки не в абсолютном числе,
    # а в том, падает оно от правки к правке или растёт.
    hist_path = OUT / f"{name}-istoriya.json"
    history = []
    if hist_path.exists():
        try:
            history = json.loads(hist_path.read_text(encoding="utf-8"))
        except Exception:
            history = []

    print(f"\nОбщее расхождение: {overall * 100:.1f}%")
    if history:
        prev = history[-1]
        delta = overall - prev["общее_расхождение"]
        # Порог 0.05 п.п.: сглаживание шрифтов и джипег-шум дают дрожание
        # в сотых долях, и без порога каждый запуск читался бы как «хуже».
        if abs(delta) < 0.0005:
            print(f"Прошлый запуск: {prev['общее_расхождение'] * 100:.1f}% "
                  f"— без изменений")
        else:
            znak = "лучше" if delta < 0 else "хуже"
            print(f"Прошлый запуск: {prev['общее_расхождение'] * 100:.1f}%  "
                  f"→ {abs(delta) * 100:.1f} п.п. {znak}")
        # Полосы, которые ухудшились — самое важное после правки
        prev_bands = {b["от"]: b["расхождение"] for b in prev.get("полосы", [])}
        worsened = [
            (y0, c, prev_bands[y0])
            for y0, y1, c in bands
            if y0 in prev_bands and c - prev_bands[y0] > 0.01
        ]
        if worsened:
            print(f"\n⚠ Полосы, которые стали ХУЖЕ после правки — {len(worsened)}:")
            for y0, now, was in sorted(worsened, key=lambda t: -(t[1] - t[2]))[:5]:
                print(f"   y={y0}: было {was * 100:.1f}%, стало {now * 100:.1f}%")
            print("   Проверьте, не сломала ли последняя правка соседний блок.")
    print("(Расхождение включает разницу фотографий. Смотрите не на "
          "абсолютное число, а на то, какие полосы выделяются.)\n")

    worst = sorted(bands, key=lambda b: -b[2])[: args.top]
    print(f"Худшие {len(worst)} полос по {args.band}px:")
    print(f"{'вертикаль':>14}  {'расхождение':>12}  шкала")
    for y0, y1, avg in worst:
        bar = "█" * round(avg * 40)
        print(f"{y0:>6}–{y1:<7}  {avg * 100:>10.1f}%  {bar}")

    # Картинка отчёта: эталон | наш | карта различий
    scale = min(1.0, 1400 / (ref.width * 3))
    tw, th = round(ref.width * scale), round(h * scale)
    report = Image.new("RGB", (tw * 3 + 24, th), "white")
    report.paste(canvas_ref.resize((tw, th)), (0, 0))
    report.paste(canvas_shot.resize((tw, th)), (tw + 12, 0))
    heat = diff.point(lambda v: min(255, v * 3)).convert("RGB")
    report.paste(heat.resize((tw, th)), (tw * 2 + 24, 0))

    d = ImageDraw.Draw(report)
    for i, label in enumerate(["МАКЕТ", "НАШ САЙТ", "РАЗЛИЧИЯ"]):
        d.text((i * (tw + 12) + 6, 6), label, fill=(200, 0, 0))

    report_path = OUT / f"{name}-sravnenie.png"
    report.save(report_path)

    (OUT / f"{name}-otchet.json").write_text(json.dumps({
        "эталон": str(ref_path),
        "адрес": args.url,
        "ширина": ref.width,
        "высота_эталона": ref.height,
        "высота_сайта": shot.height,
        "разница_высоты_px": dh,
        "общее_расхождение": round(overall, 4),
        "полосы": [{"от": a, "до": b, "расхождение": round(c, 4)} for a, b, c in bands],
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    history.append({
        "общее_расхождение": round(overall, 4),
        "полосы": [{"от": a, "расхождение": round(c, 4)} for a, b, c in bands],
    })
    hist_path.write_text(json.dumps(history[-20:], ensure_ascii=False, indent=1),
                         encoding="utf-8")

    print(f"\nОтчёт: {report_path}")
    print(f"Данные: {OUT / f'{name}-otchet.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
