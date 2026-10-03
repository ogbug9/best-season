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


def run(*args, required=True):
    print(f"[start] {' '.join(args)}", flush=True)
    result = subprocess.run([sys.executable, *args])
    if result.returncode != 0:
        print(f"[start] ОШИБКА, код {result.returncode}", flush=True)
        if required:
            sys.exit(result.returncode)
        print("[start] шаг необязательный, продолжаю запуск", flush=True)


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
run("manage.py", "seed_pages", "--create-only")
# Наполняет справочники текстами из макета. Тоже идемпотентно: то, что
# уже заведено, не трогается.
run("manage.py", "seed_content", "--initial-only")
# Фото, галереи, три кадра первого экрана и отзывы из Desktop.svg. Команда
# применяет набор один раз; дальнейшие редакторские правки не перезаписывает.
run("manage.py", "apply_desktop_reference", "--if-not-applied")
run("manage.py", "import_archive_photos", "--if-not-applied")
run("manage.py", "initialize_site_content")
# Исходники архива используются командой импорта, но не отдаются как static.
# Не дублируем 1.36 GiB фотографий в STATIC_ROOT на каждом старте контейнера.
# collectstatic — строго до prepare_site_images: та рендерит шаблоны с
# {% static %}, а без манифеста ManifestStaticFilesStorage падает
# («Missing staticfiles manifest entry»).
run("manage.py", "collectstatic", "--noinput", "--ignore=*originals*")
# Прогрев фото — оптимизация, а не условие работы сайта. Идёт фоном с низким
# приоритетом: при новом наборе размеров нарезка сотен исходников на CPU
# тарифа занимает десятки минут, и держать всё это время 503 нельзя.
# Пока варианта нет, страница отдаёт исходник, как до подготовки.
# Процесс переживает exec ниже; gunicorn сам подбирает завершившихся детей.
print("[start] manage.py prepare_site_images (фоном)", flush=True)
subprocess.Popen(
    [sys.executable, "manage.py", "prepare_site_images"],
    preexec_fn=lambda: os.nice(10),
)

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
