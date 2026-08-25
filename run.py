"""Точка входа для Amvera.

Команда запуска вынесена сюда, а не в amvera.yml, потому что YAML-поле command
Amvera разбирает без шелла: цепочка через && и кавычки там не работают.
Логи пишутся в stdout без буферизации, иначе при падении контейнера
трейсбек не успевает долететь до логов Amvera.
"""

import os
import subprocess
import sys

os.environ.setdefault("PYTHONUNBUFFERED", "1")


def run(*args):
    print(f"[start] {' '.join(args)}", flush=True)
    result = subprocess.run([sys.executable, *args])
    if result.returncode != 0:
        print(f"[start] ОШИБКА, код {result.returncode}: {' '.join(args)}", flush=True)
        sys.exit(result.returncode)


run("manage.py", "migrate", "--noinput")
run("manage.py", "collectstatic", "--noinput")

print("[start] запускаю gunicorn", flush=True)
os.execvp(
    "gunicorn",
    [
        "gunicorn",
        "config.wsgi:application",
        "--bind", "0.0.0.0:8000",
        "--workers", "3",
        "--timeout", "120",
        "--access-logfile", "-",
        "--error-logfile", "-",
    ],
)
