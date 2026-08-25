from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Ключ для локальной разработки берётся из .env (SECRET_KEY) через base.py.
# Хардкод убран: Amvera помечала файл как содержащий секрет, а в проде
# всё равно используется production.py с ключом из секретов Amvera.

# SECURITY WARNING: define the correct hosts in production!
ALLOWED_HOSTS = ["*"]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"


try:
    from .local import *
except ImportError:
    pass
