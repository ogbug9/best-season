"""Точка входа для Amvera.

Команда запуска вынесена сюда, а не в amvera.yml, потому что YAML-поле command
Amvera разбирает без шелла: цепочка через && и кавычки там не работают.
Логи пишутся без буферизации, иначе при падении контейнера трейсбек
не успевает долететь до логов Amvera.
"""

import os
import subprocess
import sys

os.environ.setdefault("PYTHONUNBUFFERED", "1")


def run(*args):
    print(f"[start] {' '.join(args)}", flush=True)
    result = subprocess.run([sys.executable, *args])
    if result.returncode != 0:
        print(f"[start] ОШИБКА, код {result.returncode}", flush=True)
        sys.exit(result.returncode)


def ensure_superuser():
    """Создаёт админа из переменных окружения при первом запуске.

    Консоли у приложения на Amvera нет, вручную createsuperuser не выполнить.
    Если пользователь уже существует, команда падает — это штатная ситуация,
    её глушим, чтобы не ронять контейнер на каждом перезапуске.
    """
    if not os.environ.get("DJANGO_SUPERUSER_USERNAME"):
        return
    print("[start] проверяю суперпользователя", flush=True)
    result = subprocess.run(
        [sys.executable, "manage.py", "createsuperuser", "--noinput"],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        print("[start] суперпользователь создан", flush=True)
    else:
        print("[start] суперпользователь уже существует, пропускаю", flush=True)


run("manage.py", "migrate", "--noinput")
ensure_superuser()
run("manage.py", "setup_roles")
# Досоздаёт недостающие страницы по карте сайта. Идемпотентно: то, что уже
# есть, не трогается — ни текст, ни порядок, ни настройки. Консоли у Amvera
# нет, поэтому разовые команды вызываются отсюда.
run("manage.py", "seed_pages")
# Наполняет справочники текстами из макета. Тоже идемпотентно: то, что
# уже заведено, не трогается.
run("manage.py", "seed_content")
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
