"""Final acceptance for 06.10 (Ф1–Ф5 + regression), locally or on production.

Usage: python design/check_final_06_10.py --url http://127.0.0.1:8000
       python design/check_final_06_10.py --url https://best-season-sfnvsd24.amvera.io

Ф1 compares desktop backgrounds with a baseline taken before the changes:
  node design/check_final_06_10_bg.cjs <url> tmp/pravki-06-10/before/<local|prod>
The run ends with design/check_pravki_05_10.py on the same URL (regression).
Requires the existing Node/Playwright runtime; does not install dependencies or submit forms.
"""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
from urllib.parse import urlparse


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--url', required=True)
    parser.add_argument('--baseline', help='default: tmp/pravki-06-10/before/local or /prod')
    parser.add_argument('--output', help='default: tmp/pravki-06-10/final/<local|prod>')
    parser.add_argument('--only', default='', help='comma list: f1,f2,f3,f4,f5,regression')
    parser.add_argument('--skip-05-10', action='store_true', help='do not run check_pravki_05_10.py')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    kind = 'local' if urlparse(args.url).hostname in ('127.0.0.1', 'localhost') else 'prod'
    baseline = Path(args.baseline or root / 'tmp/pravki-06-10/before' / kind)
    output = Path(args.output or root / 'tmp/pravki-06-10/final' / kind)
    env = os.environ.copy()
    runtime = Path.home() / '.cache/codex-runtimes/codex-primary-runtime/dependencies/node'
    if 'NODE_PATH' not in env and runtime.is_dir():
        env['NODE_PATH'] = str(runtime / 'node_modules')
    node = shutil.which('node')
    if not node:
        parser.error('Node.js is unavailable; use the existing bundled runtime.')
    command = [node, str(root / 'design/check_final_06_10.cjs'), args.url, str(output.resolve()), str(baseline.resolve())]
    if args.only:
        command.append('--only=' + args.only)
    code = subprocess.call(command, cwd=root, env=env)
    if not args.skip_05_10 and not args.only:
        print('--- regression: design/check_pravki_05_10.py')
        code |= subprocess.call([sys.executable, str(root / 'design/check_pravki_05_10.py'), '--url', args.url,
                                 '--output', str(output / 'pravki-05-10')], cwd=root, env=env)
    print('RESULT:', 'PASS' if code == 0 else 'FAIL')
    return code


if __name__ == '__main__':
    sys.exit(main())
