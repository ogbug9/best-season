# Best Season

Django 5.2 / Wagtail 7.4, PostgreSQL, Alpine.js и Swiper без сборки фронтенда. Бронирование, доступность и оплата обслуживаются Контур.Отелем. Хостинг — Amvera. Исходники шаблонов и статики: `config/`; приложения: `core`, `home`, `houses`, `promotions`, `reviews`, `services`, `forms`.

## Окружение и запуск

Нужен Python 3.11, PostgreSQL и зависимости из `requirements.txt`. Создание нового окружения выполняется владельцем среды; текущая задача новых пакетов не добавляет.

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
.venv\Scripts\python.exe manage.py migrate
.venv\Scripts\python.exe manage.py setup_roles
.venv\Scripts\python.exe manage.py seed_pages --create-only
.venv\Scripts\python.exe manage.py seed_content --initial-only
.venv\Scripts\python.exe manage.py initialize_site_content
.venv\Scripts\python.exe manage.py prepare_site_images --strict
.venv\Scripts\python.exe manage.py runserver
```

До запуска заполните `.env`, создайте БД и пользователя с правами на неё. Настройки локальной среды могут переопределяться игнорируемым `config/settings/local.py`; проверьте его перед работой с БД. В данном рабочем каталоге `.venv` ссылается на отсутствующий Python 3.11: для проверок использован bundled Python с добавлением `.venv/Lib/site-packages` **в конец** `sys.path`. Не переносите это локальное обходное решение на сервер.

`initialize_site_content` однократно переносит новые поля «О нас», документы и подписи интерфейса. Существующий контент, очищенные редактором поля, черновики, цены и `consent_version` повторный запуск не заменяет. Не запускайте обычный `seed_content` на рабочей БД: у него остаётся режим первоначального наполнения. Разовые импорты фото в `run.py` защищены флагом `--if-not-applied`.

## Переменные

Список без секретов — `.env.example`. На production обязательны:

- `DJANGO_SETTINGS_MODULE=config.settings.production`, случайный `SECRET_KEY`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `WAGTAILADMIN_BASE_URL`.
- `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` — PostgreSQL.
- `MEDIA_ROOT=/data/media` — постоянный том. `STATIC_ROOT` формируется из репозитория.
- Telegram: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`.
- Почта: `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS`, `DEFAULT_FROM_EMAIL`, `NOTIFY_EMAIL`, `EMAIL_TIMEOUT=5`. Production использует SMTP; console backend допустим только локально.
- `BACKUP_ROOT` — защищённый каталог копий вне media, см. процедуру ниже.

ID Метрики, Контур.Отеля, контакты, карты и ссылки редактируются в Wagtail → Настройки сайта. `KONTUR_HOTEL_ID` может использоваться как резервная настройка. Ни `.env`, ни токены, пароли, дампы БД или пользовательские медиа не включаются в Git. Переменные создания суперпользователя применяются только при первом создании, не меняют пароль существующей учётной записи.

## Проверки и публикация

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
node --test core/tests_analytics.cjs core/tests_calendar.cjs core/tests_kontur.cjs core/tests_house_slider.cjs core/tests_scroll_intent.cjs
git diff --check
```

Проверьте именно изменённые файлы и включите их в коммит явно. `origin` хранит историю; сайт обновляет remote `amvera`:

```powershell
git push origin main
git push amvera main:master
```

`amvera.yml` запускает `run.py`: миграции → безопасное наполнение → подготовка используемых изображений → `collectstatic --noinput --ignore=*originals*` → Gunicorn. На первом старте подготовка фото увеличивает время запуска; последующие используют готовые варианты. После выкладки проверьте логи запуска, статус реплики и реальный сайт, включая медиа, документы и мобильную верстку. Успешный push сам по себе не подтверждает работу сайта.

## Резервирование и восстановление

Подробные команды, процедура восстановления в отдельной среде и незакрытые серверные настройки: [docs/technical-handoff.md](docs/technical-handoff.md). Сейчас автоматическое хранение семи копий **не включено**. `backup_site` — готовая команда, но её наличие не заменяет настройку хранилища и ежедневного задания.

Инструкция редактору: [docs/owner-guide.md](docs/owner-guide.md), PDF `output/pdf/best-season-owner-guide.pdf`. Перечень доступов и проверка целей — в технической передаче.
