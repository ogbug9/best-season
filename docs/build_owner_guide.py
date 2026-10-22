"""Собирает output/pdf/best-season-owner-guide.pdf из docs/owner-guide.md.

Источник один — Markdown. Минимальный разбор (заголовки, абзацы, списки,
таблицы, **жирный**, `код`) и печать в PDF через Edge без заголовков/колонтитулов.
Запуск: python docs/build_owner_guide.py
"""
import html
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "docs" / "owner-guide.md"
OUT = ROOT / "output" / "pdf" / "best-season-owner-guide.pdf"
EDGES = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]

CSS = """
@page { size: A4; margin: 18mm 16mm; }
body { font: 11pt/1.5 "Segoe UI", Arial, sans-serif; color: #1f2a24; }
h1 { font-size: 26pt; margin: 0 0 6mm; color: #1d4d3a; }
h2 { font-size: 17pt; color: #1d4d3a; border-bottom: 2px solid #c9a96a; padding-bottom: 2mm; margin: 10mm 0 4mm; break-before: page; break-after: avoid; }
h2.first { break-before: auto; }
h3 { font-size: 13pt; margin: 7mm 0 2mm; color: #2d6a4f; break-after: avoid; }
p { margin: 0 0 3mm; }
ul, ol { margin: 0 0 3mm 6mm; padding-left: 5mm; }
li { margin: 1mm 0; }
code { font-family: Consolas, monospace; background: #f1efe6; padding: 0 1mm; border-radius: 1mm; font-size: 10pt; }
table { border-collapse: collapse; width: 100%; margin: 3mm 0 5mm; break-inside: avoid; }
th, td { border: 1px solid #cfd8cf; padding: 2mm 3mm; text-align: left; vertical-align: top; }
th { background: #e6efe8; }
.toc { margin: 4mm 0 6mm; }
.toc a { color: inherit; text-decoration: none; }
strong { color: #1d4d3a; }
"""


def inline(text):
    text = html.escape(text, quote=False)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)


def convert(md):
    lines = md.splitlines()
    out, toc, i, first_h2 = [], [], 0, True
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
        elif line.startswith("# "):
            out.append(f"<h1>{inline(line[2:])}</h1>")
            i += 1
        elif line.startswith("## "):
            anchor = f"c{len(toc)}"
            toc.append((anchor, line[3:]))
            cls = ' class="first"' if first_h2 else ""
            first_h2 = False
            out.append(f'<h2 id="{anchor}"{cls}>{inline(line[3:])}</h2>')
            i += 1
        elif line.startswith("### "):
            out.append(f"<h3>{inline(line[4:])}</h3>")
            i += 1
        elif line.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            head, body = rows[0], [r for r in rows[2:]]
            out.append("<table><thead><tr>" + "".join(f"<th>{inline(c)}</th>" for c in head) + "</tr></thead><tbody>")
            for r in body:
                out.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>")
            out.append("</tbody></table>")
        elif re.match(r"\d+\. ", line) or line.startswith("- "):
            ordered = bool(re.match(r"\d+\. ", line))
            tag = "ol" if ordered else "ul"
            items = []
            while i < len(lines) and (re.match(r"\d+\. ", lines[i]) if ordered else lines[i].startswith("- ")):
                item = re.sub(r"^(\d+\. |- )", "", lines[i])
                i += 1
                while i < len(lines) and lines[i].startswith("   - "):  # вложенный список
                    item += "<br>• " + inline(lines[i][5:])
                    i += 1
                items.append(f"<li>{inline(item) if '<br>' not in item else item}</li>")
            out.append(f"<{tag}>" + "".join(items) + f"</{tag}>")
        else:
            para = [line]
            i += 1
            while i < len(lines) and lines[i].strip() and not re.match(r"(#|\||\d+\. |- )", lines[i]):
                para.append(lines[i])
                i += 1
            out.append(f"<p>{inline(' '.join(para))}</p>")
    toc_html = '<div class="toc"><ol>' + "".join(f'<li><a href="#{a}">{inline(t)}</a></li>' for a, t in toc) + "</ol></div>"
    # оглавление после заголовка h1
    for idx, chunk in enumerate(out):
        if chunk.startswith("<h1>"):
            out.insert(idx + 1, toc_html)
            break
    return "\n".join(out)


def main():
    body = convert(SRC.read_text(encoding="utf-8"))
    doc = f'<!doctype html><html lang="ru"><head><meta charset="utf-8"><title>Best Season: учебник</title><style>{CSS}</style></head><body>{body}</body></html>'
    edge = next((p for p in EDGES if Path(p).exists()), None)
    if not edge:
        sys.exit("Edge не найден")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        page = Path(tmp) / "guide.html"
        pdf = Path(tmp) / "guide.pdf"
        page.write_text(doc, encoding="utf-8")
        # отдельный профиль: иначе уже запущенный Edge перехватывает команду и PDF не создаётся
        subprocess.run(
            [edge, "--headless", "--disable-gpu", "--no-pdf-header-footer",
             f"--user-data-dir={Path(tmp) / 'profile'}", f"--print-to-pdf={pdf}", page.as_uri()],
            check=True, timeout=120,
        )
        for _ in range(60):  # Edge может завершить запускающий процесс раньше, чем допишет файл
            if pdf.exists() and pdf.stat().st_size > 0:
                time.sleep(1)
                break
            time.sleep(0.5)
        else:
            sys.exit("Edge не создал PDF")
        OUT.write_bytes(pdf.read_bytes())
    print(f"Готово: {OUT} ({OUT.stat().st_size // 1024} КБ)")


if __name__ == "__main__":
    main()
