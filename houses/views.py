"""Данные для блока бронирования: календарь и расчёт стоимости.

Скрипт перелистывает месяцы и пересчитывает сумму без перезагрузки:
календарь приходит готовой разметкой, расчёт — в JSON. Страница при
этом остаётся рабочей и без JS — те же данные кладёт в контекст
HousePage.get_context.
"""

from django.http import Http404, HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.views.decorators.http import require_GET

from houses.booking import calendar_months, guests_label, nights_label, quote
from houses.models import HousePage


def _house(slug):
    house = HousePage.objects.live().filter(slug=slug).first()
    if house is None:
        raise Http404("Домик не найден")
    return house


@require_GET
def calendar(request, slug):
    """Готовая разметка сетки календаря.

    Отдаём HTML, а не JSON: иначе скрипту пришлось бы вторым экземпляром
    повторять разметку из шаблона, и однажды они бы разъехались.
    """
    house = _house(slug)
    data = calendar_months(
        house,
        start=request.GET.get("start"),
        selection={
            "date_from": request.GET.get("date_from"),
            "date_to": request.GET.get("date_to"),
        },
    )
    html = render_to_string(
        "houses/_calendar_months.html", {"calendar": data}, request=request
    )
    return HttpResponse(html)


@require_GET
def price(request, slug):
    house = _house(slug)
    result = quote(
        house,
        date_from=request.GET.get("date_from"),
        date_to=request.GET.get("date_to"),
        adults=request.GET.get("adults"),
        children=request.GET.get("children"),
        pets=request.GET.get("pets"),
    )
    # Подписи считает сервер: русские окончания «ночь/ночи/ночей» —
    # одна логика на шаблон и на скрипт, иначе они разъедутся.
    result["nights_label"] = nights_label(result["nights"])
    result["guests_label"] = guests_label(result["guests"])
    return JsonResponse(result)
