"""Подписи блока бронирования.

Русские окончания и разделитель тысяч нужны и на сервере, и в JSON для
скрипта. Держим их в одном месте: иначе шаблон и скрипт со временем
начинают писать по-разному («2 ночи» против «2 ночь»).
"""

from django import template

from houses import booking

register = template.Library()


@register.filter
def nights(value):
    return booking.nights_label(value or 0)


@register.filter
def guests(value):
    return booking.guests_label(value or 0)


@register.filter
def price_ru(value):
    """«8 000» вместо «8000». Пробел неразрывный: число не должно
    разрываться переносом строки."""
    try:
        return f"{int(value):,}".replace(",", "\u00a0")
    except (TypeError, ValueError):
        return ""
