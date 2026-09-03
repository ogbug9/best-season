#!/usr/bin/env python3
"""Проверка вёрстки против реестра измеренных значений макета.

Зачем: соответствие макету нельзя держать «в голове». Значения снимаются
из панели инспектора Figma один раз, кладутся в design/spec.json, и дальше
этот скрипт механически проверяет, что браузер рисует именно их.

Что делает: поднимает headless-браузер, открывает страницу, для каждого
селектора из реестра читает вычисленные стили и сравнивает с ожидаемыми.

Три исхода по каждому свойству:
  СОВПАДАЕТ   — вёрстка соответствует измеренному значению
  РАСХОЖДЕНИЕ — вёрстка противоречит замеру, это ошибка
  ДОГАДКА     — значение в реестре помечено source=assumed, замер не делался

Код возврата 1, если есть хоть одно расхождение. Догадки код возврата
не меняют, но выводятся отдельным списком: это очередь на запрос
скриншотов инспектора.

Запуск:
    python design/check_spec.py --url http://127.0.0.1:8000/
    python design/check_spec.py --url http://127.0.0.1:8000/ --strict

--strict считает ошибкой и догадки. Включать перед сдачей этапа.
"""

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

SPEC = Path(__file__).parent / "spec.json"

# Считыватель стилей. Отдельным файлом на Node, потому что вычисленные
# стили доступны только в настоящем браузере — из Python их не получить.
READER = r"""
const { chromium } = require('playwright');
const spec = require(process.argv[2]);
const url = process.argv[3];

(async () => {
  const browser = await chromium.launch({
    executablePath: process.env.CHROME_PATH || undefined,
  });
  const out = {};

  // Группируем компоненты по ширине окна: разные брейкпоинты — разные замеры
  const byViewport = {};
  for (const [name, comp] of Object.entries(spec.components)) {
    const w = comp.viewport || 1440;
    (byViewport[w] = byViewport[w] || []).push([name, comp]);
  }

  for (const [width, comps] of Object.entries(byViewport)) {
    const page = await browser.newPage({
      viewport: { width: Number(width), height: 900 },
    });
    await page.goto(url, { waitUntil: 'networkidle' });

    for (const [name, comp] of comps) {
      const got = await page.evaluate(({ selector, props }) => {
        const el = document.querySelector(selector);
        if (!el) return null;
        const cs = getComputedStyle(el);
        const res = {};
        for (const prop of props) res[prop] = cs.getPropertyValue(prop);
        return res;
      }, { selector: comp.selector, props: Object.keys(comp.props) });
      out[name] = got;
    }
    await page.close();
  }

  await browser.close();
  process.stdout.write(JSON.stringify(out));
})().catch(e => { console.error(e); process.exit(2); });
"""


def rgb_to_hex(value):
    """rgb(132, 127, 87) -> #847F57. Браузер всегда отдаёт цвет в rgb."""
    m = re.match(r"rgba?\(([\d.]+),\s*([\d.]+),\s*([\d.]+)", value.strip())
    if not m:
        return value.strip()
    return "#%02X%02X%02X" % tuple(int(float(g)) for g in m.groups())


def normalize(prop, value):
    """Приводит значение к сравнимому виду.

    Браузер и инспектор Figma записывают одно и то же по-разному: цвет как
    rgb() против hex, шрифт со стековым запасом против одного имени,
    межстрочный в пикселях против процентов.
    """
    value = value.strip()
    if "color" in prop:
        return rgb_to_hex(value).upper()
    if prop == "font-family":
        # Берём первую гарнитуру стека и снимаем кавычки: в CSS стоит
        # запасной набор шрифтов, в макете — одно имя.
        return value.split(",")[0].strip().strip('"\'')
    if prop == "font-weight":
        # Браузер может отдать имя вместо числа
        return {"normal": "400", "bold": "700"}.get(value, value)
    # Размеры: округляем до целых пикселей, доли здесь ни на что не влияют
    m = re.match(r"^([\d.]+)px$", value)
    if m:
        return f"{round(float(m.group(1)))}px"
    return value


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://127.0.0.1:8000/")
    ap.add_argument("--strict", action="store_true",
                    help="считать ошибкой не только расхождения, но и догадки")
    ap.add_argument("--spec", default=str(SPEC))
    args = ap.parse_args()

    spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))

    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
        f.write(READER)
        reader = f.name

    proc = subprocess.run(
        ["node", reader, str(Path(args.spec).resolve()), args.url],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        print("Не удалось снять стили из браузера:\n", proc.stderr[:1500])
        return 2

    measured = json.loads(proc.stdout)

    ok, bad, guesses, missing = 0, [], [], []

    for name, comp in spec["components"].items():
        got = measured.get(name)
        if got is None:
            missing.append((name, comp["selector"]))
            continue

        for prop, meta in comp["props"].items():
            want = normalize(prop, str(meta["value"]))
            have = normalize(prop, got.get(prop, ""))
            same = want == have

            if meta.get("source") == "assumed":
                guesses.append((name, prop, meta["value"], got.get(prop, ""),
                                meta.get("заметка", "")))
                continue
            if same:
                ok += 1
            else:
                bad.append((name, comp["selector"], prop, meta["value"],
                            got.get(prop, ""), meta.get("node", "")))

    print("=" * 72)
    print("ПРОВЕРКА ВЁРСТКИ ПРОТИВ ЗАМЕРОВ МАКЕТА")
    print("=" * 72)
    print(f"Адрес: {args.url}\n")

    if missing:
        print("НЕ НАЙДЕНЫ НА СТРАНИЦЕ (селектор не сработал):")
        for name, sel in missing:
            print(f"  · {name}: {sel}")
        print("  Возможно, блок не выводится без контента — проверьте наполнение.\n")

    if bad:
        print(f"РАСХОЖДЕНИЯ — {len(bad)} шт. Это ошибки вёрстки:")
        for name, sel, prop, want, have, node in bad:
            print(f"  ✗ {name} ({sel})")
            print(f"      {prop}: в макете {want}, на сайте {have}"
                  + (f"   [узел: {node}]" if node else ""))
        print()

    if guesses:
        print(f"ДОГАДКИ — {len(guesses)} шт. Замер не делался, значения подобраны:")
        for name, prop, want, have, note in guesses:
            print(f"  ? {name}.{prop}: стоит {want}, на сайте {have}")
            if note:
                print(f"      {note}")
        print("  Каждая такая строка — повод запросить скриншот инспектора.\n")

    print(f"ИТОГ: совпадает {ok}, расхождений {len(bad)}, "
          f"догадок {len(guesses)}, не найдено {len(missing)}")

    if bad or missing:
        return 1
    if args.strict and guesses:
        print("\n--strict: догадки считаются ошибкой. Реестр не заполнен до конца.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
