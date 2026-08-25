"""
WSGI config for config project.

Дополнительно к статике whitenoise здесь раздаёт медиа — загруженные
через админку фото. Без этого на боевом сервере все картинки отдают 404:
Django раздаёт MEDIA_URL только при DEBUG, а middleware whitenoise
занимается исключительно статикой.
"""

import os

from django.conf import settings
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

application = get_wsgi_application()

if not settings.DEBUG:
    from whitenoise import WhiteNoise

    application = WhiteNoise(application)
    media_root = str(settings.MEDIA_ROOT)
    os.makedirs(media_root, exist_ok=True)
    # Рендишены Wagtail неизменяемы по содержимому, но имя файла может
    # переиспользоваться, поэтому кэш умеренный, а не «навсегда».
    application.add_files(media_root, prefix=settings.MEDIA_URL)
