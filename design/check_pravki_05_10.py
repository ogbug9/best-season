"""Run the Playwright acceptance checks locally or on production, without forms.

Usage: python design/check_pravki_05_10.py --url http://127.0.0.1:8784
Requires the existing Node/Playwright runtime; does not install dependencies.
"""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', required=True)
    parser.add_argument('--output', default='tmp/pravki-05-10/final')
    parser.add_argument('--buttons-only', action='store_true')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    runtime = Path.home() / '.cache/codex-runtimes/codex-primary-runtime/dependencies/node'
    if 'NODE_PATH' not in env and runtime.is_dir():
        env['NODE_PATH'] = str(runtime / 'node_modules')
    node = shutil.which('node')
    if not node:
        parser.error('Node.js is unavailable; use the existing bundled runtime.')
    command = [node, str(root / 'design/check_pravki_05_10.cjs'), args.url, str(Path(args.output).resolve())]
    if args.buttons_only:
        command.append('--buttons-only')
    return subprocess.call(command, cwd=root, env=env)


if __name__ == '__main__':
    sys.exit(main())
