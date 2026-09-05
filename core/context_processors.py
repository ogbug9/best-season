"""Общий контекст шаблонов.

Резервная форма бронирования (п. 5.6 ТЗ) и настройки виджета живут в
модальном окне, а оно подключается на каждой странице сайта из base.html.
Прокидывать их через get_context каждого типа страниц пришлось бы в
десяти местах — и одно из них рано или поздно забыли бы, а резервный блок
обязателен к сдаче в первой очереди.
"""

import logging

from django.middleware.csrf import get_token
from django.urls import reverse

from forms.forms import FallbackBookingForm

logger = logging.getLogger(__name__)


# Состав колонок подвала по макету. Группировка отличается от шапки:
# «Акции» стоят внутри «Размещения», «Интересное рядом» — внутри
# «Территории». Из дерева страниц это не выводится, поэтому список
# задан явно. Ключ — слаг страницы, значение — подпись в подвале
# (в макете некоторые пункты названы иначе, чем сами страницы).
FOOTER_COLUMNS = [
    {
        "title": "Размещение",
        "slugs": [
            ("akcii", "Акции"),
            ("__booking__", "Бронирование"),
            ("razmeshchenie", "Дома"),
            ("pravila-bronirovaniya", "Правила бронирования"),
            ("vyezdy-kompaniy", "Выезды компаний"),
        ],
        "legal_slugs": [
            ("rassylka", "Рассылка"),
            ("oferta", "Оферта"),
            ("politika-konfidencialnosti", "Политика конфиденциальности"),
            ("soglasie-na-obrabotku", "Персональные данные"),
        ],
    },
    {
        "title": "Территория",
        "slugs": [
            ("razvlecheniya", "Развлечения"),
            ("chem-zanyatsya", "Чем заняться"),
            ("uslugi", "Доп услуги"),
            ("meropriyatiya", "Мероприятия"),
            ("interesnoe-ryadom", "Интересное рядом"),
        ],
    },
    {
        "title": "О нас",
        "slugs": [
            ("galereya", "Галерея"),
            ("otzyvy", "Отзывы"),
            ("kontakty", "Контакты"),
            ("voprosy", "FAQ"),
            ("partneram", "Партнерам"),
        ],
    },
]


def _links(pairs, pages):
    out = []
    for slug, label in pairs:
        if slug == "__booking__":
            out.append({"title": label, "booking": True})
            continue
        page = pages.get(slug)
        if page is not None:
            out.append({"title": label, "url": page.url})
    return out


def footer(request):
    """Колонки подвала.

    Страницы ищем одним запросом по слагам: подвал есть на каждой странице
    сайта, и десяток отдельных запросов на каждый показ — лишняя нагрузка.
    Ненайденные слаги просто пропускаются, поэтому подвал не разваливается,
    пока часть страниц ещё не заведена.
    """
    from wagtail.models import Page

    wanted = set()
    for column in FOOTER_COLUMNS:
        wanted.update(slug for slug, _ in column["slugs"])
        wanted.update(slug for slug, _ in column.get("legal_slugs", []))

    try:
        pages = {p.slug: p for p in Page.objects.live().filter(slug__in=wanted)}
    except Exception:
        logger.exception("Не удалось собрать колонки подвала")
        pages = {}

    columns = []
    for column in FOOTER_COLUMNS:
        columns.append(
            {
                "title": column["title"],
                "links": _links(column["slugs"], pages),
                "legal": _links(column.get("legal_slugs", []), pages),
            }
        )
    return {"footer_columns": columns}


def booking(request):
    # Ошибки формы после неудачной отправки показываются на самой странице
    # (вьюха возвращает гостя с ?form=error), поэтому здесь всегда пустая.
    context = {"fallback_booking_form": FallbackBookingForm()}

    hotel_id, metrika_id = "", ""
    try:
        from core.models import SiteSettings

        site_settings = SiteSettings.for_request(request)
        hotel_id = site_settings.kontur_hotel_id.strip()
        metrika_id = site_settings.yandex_metrika_id.strip()
    except Exception:
        # Настроек может не быть на самой ранней стадии установки сайта.
        # Это не повод отдавать гостю 500: без hotelId просто откроется
        # резервная форма заявки.
        logger.exception("Не удалось прочитать настройки бронирования")

    context["booking_config"] = {
        "hotelId": hotel_id,
        "metrikaId": metrika_id,
        "errorUrl": reverse("forms:widget_error"),
        "csrfToken": get_token(request),
        # Палитра для темы виджета — п. 5.4.1. Держим здесь, а не в JS,
        # чтобы цвета бренда были описаны в одном месте с остальным кодом.
        "colorAccent": "#9B5026",
        "colorLight": "#F7F0E6",
    }
    return context
