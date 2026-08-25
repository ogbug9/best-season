from .base import *

DEBUG = False

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

# ManifestStaticFilesStorage is recommended in production, to prevent
# outdated JavaScript / CSS assets being served from cache
# (e.g. after a Wagtail upgrade).
# See https://docs.djangoproject.com/en/5.2/ref/contrib/staticfiles/#manifeststaticfilesstorage
STORAGES["staticfiles"][
    "BACKEND"
] = "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"

try:
    from .local import *
except ImportError:
    pass
