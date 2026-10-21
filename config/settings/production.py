from .base import *

DEBUG = False
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.smtp.EmailBackend')

# Wagtail renditions are expensive to create on a cold /data volume. Generating
# several variants for every photo while rendering a page times out Gunicorn.
GENERATE_IMAGE_RENDITIONS_ON_REQUEST = False

# HTTPS с автопродлением — Amvera выдаёт SSL на своём домене, здесь только заголовки (п.10 ТЗ).
SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", default=True, cast=bool)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
CSRF_TRUSTED_ORIGINS = config(
    "CSRF_TRUSTED_ORIGINS", default="https://best-season.online", cast=Csv()
)

WAGTAILADMIN_BASE_URL = config(
    "WAGTAILADMIN_BASE_URL", default="https://best-season.online"
)

# Загруженные картинки должны лежать в постоянном хранилище Amvera (/data).
# Иначе каждая пересборка стирает всё, что залил редактор: репозиторий
# при деплое разворачивается заново, а /data переживает пересборку.
MEDIA_ROOT = config("MEDIA_ROOT", default="/data/media")

# Манифест с хешами в именах, как и раньше, плюс заранее сжатые .gz:
# Amvera не сжимает ответы сама, а main.css без сжатия весит 230 КБ
# и блокирует первую отрисовку на мобильном (п. 10.3 ТЗ).
STORAGES["staticfiles"][
    "BACKEND"
] = "whitenoise.storage.CompressedManifestStaticFilesStorage"

try:
    from .local import *
except ImportError:
    pass
