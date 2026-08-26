"""
WSGI config for config project.

Здесь дополнительно раздаётся медиа — загруженные через админку фото.
Без этого на боевом сервере все картинки отдают 404: Django раздаёт
MEDIA_URL только при DEBUG, а middleware whitenoise занимается
исключительно статикой.

ВАЖНО про autorefresh. По умолчанию whitenoise составляет список файлов
один раз при старте процесса. Для статики это правильно, а для медиа —
нет: всё, что редактор загрузит после запуска контейнера, и все
рендишены, которые Wagtail создаёт на лету, окажутся вне списка
и будут отдавать 404 до следующей пересборки. autorefresh заставляет
проверять файл на диске при каждом запросе.
"""

import os

from django.conf import settings
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

application = get_wsgi_application()

if not settings.DEBUG:
    from whitenoise import WhiteNoise

    media_root = str(settings.MEDIA_ROOT)
    os.makedirs(media_root, exist_ok=True)

    application = WhiteNoise(application, autorefresh=True)
    application.add_files(media_root, prefix=settings.MEDIA_URL)
