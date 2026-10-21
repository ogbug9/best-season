# К1 и К1б — локальный отчёт

Дата: 1 октября 2026. Основание: `docs/claude-booking-plan.md`, пакеты К1 и К1б.

## Результат

- Метрика подключается при заполненном ID только после `accepted`, после загрузки страницы и в idle-периоде. Закрытие cookie-баннера не считается согласием. Общий `bsTrack` обслуживает сайт и Контур; события до подключения счётчика сохраняются в памяти страницы и отправляются после согласия.
- Добавлены клики контактов, открытие «Как добраться», достижение 75% просмотренной высоты страницы дома (нижняя граница экрана / высота документа).
- Цель заявки перенесена с DOM-submit на страницу успешного серверного redirect `form=ok&ft=...`. Тип проверяется по `FormType`, после учёта параметры удаляются с сохранением остальных параметров, фрагмента и history state. Для fallback отправляются две отдельные цели. Хуки Контура сохраняют прежний набор суммы/id/валюты/точки входа без данных гостя.
- Добавлены редактируемый срок ответа и переключатель почасовых объектов. Срок по умолчанию пустой; прежний текст остаётся. Почасовые по умолчанию включены; выключение убирает контейнер и его регистрацию SDK.
- После отзывов на странице дома добавлена точка 5 с названием, ID дома и категорией PMS. Когда блок виден, липкая кнопка скрывается.

## Изменённые файлы

| Область | Файлы |
|---|---|
| Аналитика | `config/static/js/analytics.js` (новый), `config/static/js/kontur.js`, `config/static/js/site.js`, `config/templates/includes/metrika.html` (новый), `config/templates/base.html`, `core/context_processors.py` |
| Настройки | `core/models.py`, `core/migrations/0017_booking_analytics_settings.py` (новый) |
| Заявки | `forms/views.py`, `forms/templates/forms/request_form.html` |
| К1б | `config/templates/includes/booking_cta.html`, `config/templates/includes/booking_modal.html`, `houses/templates/houses/house_page.html` |
| Классы страниц | `core/templates/core/contacts_page.html`, `core/templates/core/directions_page.html` |
| Тесты | `core/tests_analytics.cjs` (новый), `core/tests_kontur.cjs`, `core/tests_booking.py`, `forms/tests.py`, `houses/tests_booking.py` |
| Передача | `HANDOFF.md`, этот отчёт |

## Проверки

- `node --check` для analytics.js, site.js, kontur.js — успешно.
- `node --test core/tests_calendar.cjs core/tests_kontur.cjs core/tests_analytics.cjs` — **46/46**.
- Django `check` — без замечаний.
- Django `forms.tests core.tests_booking houses.tests_booking` — **64/64**.
- Полный Django-набор — **115/115**.
- `makemigrations --check --dry-run` — изменений модели без миграции нет. Новая миграция применена локально.
- `git diff --check` — успешно.
- Локальный Edge/Playwright, 1440×900 и 390×844, DPR 1: снимки до/после; после правок нет горизонтального переполнения, перекрытия новой кнопки липкой и ошибок JS; открытие точки 5 показывает «Ваш выбор» с домом и категорией. Проверены снимки изменённого блока.
- Локальный браузер на 1440/390 с фиктивным ID `12345678`: до согласия и после крестика нет tag.js/ym; после accepted один script/init; две цели успешного fallback по одному разу; reload не дублирует цель. Скрипт Метрики заменён локальной заглушкой, внешних запросов в этой проверке нет.
- Тесты проверяют точку 5 на четырёх домах, отсутствие hourly-контейнера/регистрации при выключении, неверный тип успеха и невалидную заявку, сохранение параметров URL и отсутствие персональных данных в onBooking.

Python311 из `.venv` отсутствует. Django запущен bundled Python 3.12 с добавлением `.venv/Lib/site-packages` в конец sys.path; зависимости не устанавливались. Уведомления для локальных запусков отключены, сетевые обращения тестов замоканы.

Артефакты: `tmp/booking-k1-20261001/` — `before-1440.png`, `before-390.png`, `after-1440.png`, `after-390.png`, замеры JSON, журналы тестов и скрипты проверки. Локальный сервер и браузеры после проверок остановлены.

## Цели для Яндекс.Метрики

Все создавать как **«JavaScript-событие»** с идентификатором из первого столбца.

| Идентификатор | Параметры |
|---|---|
| `booking_widget_open` | `entry_point` |
| `booking_widget_ready` | — |
| `booking_fallback_shown` | `reason` |
| `booking_fallback_submitted` | `form_type: fallback` |
| `booking_completed` | `price`, `currency`, `bookings` (ID), `entry_point` |
| `hourly_booking_completed` | `price`, `currency`, `bookings` (ID), `entry_point` |
| `contact_click` | `channel: telegram/whatsapp/phone`, `place: header/footer/fallback/contacts/other` |
| `directions_view` | — |
| `house_scroll_75` | `house` (slug) |
| `form_submitted` | `form_type: feedback/transfer/certificate/house_question/fallback` |

## Ограничения

Commit, push, выкладка, кабинеты Метрики/Контура и реальные заявки/брони не выполнялись. Работа реального счётчика и SDK в production не подтверждается этими локальными проверками. ID счётчика и срок ответа владелец заполняет в админке; цели создаёт в Метрике. К2–К5 и задачи Д не входят в этот пакет.
