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
