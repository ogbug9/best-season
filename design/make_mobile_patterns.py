"""Build light mobile background layers (06.10, Ф1).

Usage: python design/make_mobile_patterns.py [--opacity 0.15] [--check]

Sources are the full mobile layers in config/static/img/mobile-backgrounds/
(crops of the desktop artwork, 30.09); they are read only and never rewritten.
Each light layer keeps every second contour (document order follows the
terrain, so the thinning stays even), lowers the line opacity and stores the
outlines with 0.1 px relative coordinates. Output goes to .../mobile-backgrounds/lite/.
"""
import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'config/static/img/mobile-backgrounds'
TARGET = SOURCE / 'lite'
LAYERS = ('home-quote', 'home-territory', 'home-nearby', 'home-faq', 'houses-top', 'houses-catalog',
          'houses-faq', 'promotions-top', 'promotions-faq', 'house-top', 'house-booking', 'house-reviews')
# Measured on a cream #F7F0E6 pixel: 0.30 gives a clearly drawn line, 0.15 a barely visible one.
DEFAULT_OPACITY = 0.15
MAX_RATIO = 0.30

PATH = re.compile(r'<path d="([^"]*)" fill="(#[0-9A-Fa-f]{6})" fill-opacity="[\d.]+"\s*/>')
TOKEN = re.compile(r'[MLHVCZmlhvcz]|-?\d*\.?\d+(?:e-?\d+)?')


def number(value):
    text = f'{value:.1f}'.rstrip('0').rstrip('.')
    if text in ('-0', ''):
        text = '0'
    return text.replace('0.', '.', 1) if text.startswith('0.') else text.replace('-0.', '-.', 1)


def join(values):
    out, previous = '', None
    for value in values:
        text = number(value)
        # A separator is needed unless the sign or a second decimal point splits the numbers.
        if previous is not None and not text.startswith('-') and not (text.startswith('.') and '.' in previous):
            out += ' '
        out += text
        previous = text
    return out


def relative(d):
    """Absolute M/L/H/V/C/Z path → relative path on a 0.1 px grid (no accumulated error)."""
    tokens = TOKEN.findall(d)
    out, i = [], 0
    x = y = sx = sy = 0.0
    snap = lambda v: round(float(v) * 10) / 10
    while i < len(tokens):
        cmd = tokens[i]; i += 1
        args = []
        while i < len(tokens) and tokens[i] not in 'MLHVCZmlhvcz':
            args.append(snap(tokens[i])); i += 1
        if cmd == 'Z':
            out.append('z'); x, y = sx, sy
            continue
        step = {'M': 2, 'L': 2, 'H': 1, 'V': 1, 'C': 6}[cmd]
        for k in range(0, len(args), step):
            chunk = args[k:k + step]
            if cmd in 'ML':
                nx, ny = chunk
                out.append(('m' if cmd == 'M' and k == 0 else 'l') + join([nx - x, ny - y]))
                if cmd == 'M' and k == 0:
                    sx, sy = nx, ny
                x, y = nx, ny
            elif cmd == 'H':
                out.append('h' + join([chunk[0] - x])); x = chunk[0]
            elif cmd == 'V':
                out.append('v' + join([chunk[0] - y])); y = chunk[0]
            else:
                out.append('c' + join([chunk[0] - x, chunk[1] - y, chunk[2] - x, chunk[3] - y, chunk[4] - x, chunk[5] - y]))
                x, y = chunk[4], chunk[5]
    # Repeated commands may omit the letter; a following negative number or "." still separates them.
    text, last = '', None
    for part in out:
        letter, rest = part[0], part[1:]
        if letter == last and letter != 'z':
            previous = re.split(r'[^\d.]', text)[-1]
            text += rest if rest[0] == '-' or (rest[0] == '.' and '.' in previous) else ' ' + rest
        else:
            text += part
        last = letter if letter != 'm' else 'l'
    return text


def build(name, opacity):
    source = (SOURCE / f'{name}.svg').read_text(encoding='utf-8')
    head = source[:source.index('>') + 1]
    paths = PATH.findall(source)
    if len(paths) != source.count('<path'):
        raise SystemExit(f'{name}: unexpected path markup')
    kept = paths[::2]
    fill = kept[0][1]
    body = ''.join(f'<path d="{relative(d)}"/>' for d, _ in kept)
    svg = f'{head}<g fill="{fill}" fill-opacity="{opacity:g}">{body}</g></svg>\n'
    target = TARGET / f'{name}.svg'
    return source, svg, target, len(paths), len(kept)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--opacity', type=float, default=DEFAULT_OPACITY)
    parser.add_argument('--check', action='store_true', help='verify committed files are current')
    args = parser.parse_args()
    TARGET.mkdir(exist_ok=True)
    failed = False
    for name in LAYERS:
        source, svg, target, total, kept = build(name, args.opacity)
        ratio = len(svg.encode()) / len(source.encode())
        stale = not target.exists() or target.read_text(encoding='utf-8') != svg
        if args.check:
            failed |= stale
        else:
            target.write_text(svg, encoding='utf-8', newline='\n')
        failed |= ratio > MAX_RATIO
        print(f'{name}: {kept}/{total} contours, {len(svg.encode())} / {len(source.encode())} bytes = {ratio:.1%}'
              + (' STALE' if args.check and stale else ''))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
