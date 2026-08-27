"""Приём заявок.

Одна вьюха на все типы форм: тип приходит в адресе, набор полей и правила
берутся из соответствующего класса формы. Так не расползается логика
сохранения, UTM и согласия — она описана в одном месте.
"""

import hashlib
import logging

from django.core.cache import cache
from django.http import Http404, JsonResponse
from django.shortcuts import redirect
from django.views.decorators.http import require_POST
from wagtail.models import Site

from .forms import FORM_CLASSES
from .models import FormType
from .notifications import notify

logger = logging.getLogger(__name__)

# Ограничение частоты вместо капчи — п. 7 ТЗ.
RATE_LIMIT_COUNT = 5
RATE_LIMIT_WINDOW = 60 * 60  # час


def _client_key(request):
    """Ключ ограничения частоты.

    IP не сохраняется — только его хеш и только в кеше на час. По разделу 11
    ТЗ мы храним минимум персональных данных, а адрес посетителя к заявке
    отношения не имеет.

    Оговорка: стандартный кеш живёт в памяти процесса, а gunicorn запускает
    несколько воркеров, поэтому фактический лимит кратен их числу. Это
    осознанный размен: основную работу делает ловушка honeypot, а поднимать
    ради счётчика отдельное хранилище — лишняя точка отказа при передаче
    проекта (п. 10.15).
    """
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    ip = forwarded.split(",")[0].strip() if forwarded else request.META.get("REMOTE_ADDR", "")
    digest = hashlib.sha256(f"bs-form:{ip}".encode()).hexdigest()[:32]
    return f"form-rate:{digest}"


def _rate_limited(request):
    """Проверяет лимит, но НЕ увеличивает счётчик.

    Счётчик растёт только после успешно принятой заявки (см. _count_submission).
    Иначе гость, который трижды ошибся в поле и исправлял, выбирал бы свой
    лимит на ровном месте и упирался в отказ — а форма заявки на сайте
    для того и стоит, чтобы её отправляли.
    """
    return cache.get(_client_key(request), 0) >= RATE_LIMIT_COUNT


def _count_submission(request):
    key = _client_key(request)
    cache.set(key, cache.get(key, 0) + 1, RATE_LIMIT_WINDOW)


def _consent_version(request):
    """Версия текста согласия, действующая на момент отправки.

    Хранится вместе с заявкой: раздел 11 ТЗ требует, чтобы факт согласия
    фиксировался с датой и версией текста, под которым его дали.
    """
    try:
        from core.models import SiteSettings

        site = Site.find_for_request(request)
        return SiteSettings.for_site(site).consent_version
    except Exception:
        logger.exception("Не удалось определить версию текста согласия")
        return ""


@require_POST
def submit(request, form_type):
    if form_type not in FORM_CLASSES:
        raise Http404("Неизвестный тип формы")

    wants_json = request.headers.get("X-Requested-With") == "XMLHttpRequest"
    back_to = request.POST.get("source_url") or "/"

    if _rate_limited(request):
        message = "Слишком много заявок подряд. Позвоните нам — так быстрее."
        if wants_json:
            return JsonResponse({"ok": False, "error": message}, status=429)
        return redirect(f"{back_to}?form=rate")

    form_class = FORM_CLASSES[form_type]
    form = form_class(request.POST)

    if not form.is_valid():
        if wants_json:
            return JsonResponse({"ok": False, "errors": form.errors}, status=400)
        return redirect(f"{back_to}?form=error")

    submission = form.save(request=request, consent_version=_consent_version(request))
    _count_submission(request)
    notify(submission)

    if wants_json:
        return JsonResponse({"ok": True})
    return redirect(f"{back_to}?form=ok")


def form_types():
    return [choice[0] for choice in FormType.choices]


# Как часто владельцу может приходить сообщение о недоступности виджета.
# Час выбран не случайно: если Контур лежит, о нём сообщат все посетители
# сразу, и без этого ограничения владелец получит сотню одинаковых
# уведомлений вместо одного.
WIDGET_ERROR_NOTIFY_WINDOW = 60 * 60


@require_POST
def widget_error(request):
    """Сбой виджета Контура — п. 5.6.4 ТЗ: событие логируется, владельцу
    приходит уведомление в Telegram.

    Отвечаем всегда успехом: это служебный сигнал, и никакая неполадка
    здесь не должна отражаться на госте — он в этот момент уже видит
    резервную форму заявки.
    """
    reason = request.POST.get("reason", "")[:200]
    page = request.POST.get("page", "")[:200]
    entry_point = request.POST.get("entry_point", "")[:8]

    logger.error(
        "Виджет Контура недоступен: %s (страница %s, точка входа %s)",
        reason,
        page,
        entry_point,
    )

    if not cache.get("kontur-widget-error-notified"):
        cache.set("kontur-widget-error-notified", True, WIDGET_ERROR_NOTIFY_WINDOW)
        from .notifications import send_service_message

        send_service_message(
            "⚠️ Виджет бронирования недоступен\n"
            f"Причина: {reason}\n"
            f"Страница: {page}\n"
            f"Точка входа: {entry_point or '—'}\n\n"
            "Гостям показывается резервная форма заявки — сайт работает. "
            "Проверьте подписку на модуль бронирования и список разрешённых "
            "доменов в Контур.Отеле."
        )

    return JsonResponse({"ok": True})
