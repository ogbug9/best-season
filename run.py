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
