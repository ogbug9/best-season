"""Иконки из спрайта static/img/icons.svg.

Отдельный тег нужен, чтобы имя иконки нигде не собиралось строкой в шаблоне:
набор закрыт списком ICON_CHOICES (п. 9.4 ТЗ), и неизвестное имя должно
давать пустоту, а не битую ссылку на несуществующий символ.
"""

from django import template
from django.templatetags.static import static
from django.utils.html import escape
from django.utils.safestring import mark_safe

from core.models import ICON_CHOICES

register = template.Library()

KNOWN_ICONS = {value for value, _ in ICON_CHOICES}


@register.simple_tag
def icon(name, css_class="icon"):
    """Иконка удобства. Декоративная: смысл несёт подпись рядом."""
    if name not in KNOWN_ICONS:
        return ""
    return mark_safe(
        f'<svg class="{escape(css_class)}" aria-hidden="true" focusable="false">'
        f'<use href="{static("img/icons.svg")}#i-{name}"></use>'
        "</svg>"
    )


@register.simple_tag
def house_icon(name):
    """Иконки страницы дома из присланного макета."""
    if name not in {"sofa_bed", "bunk_bed", "layout", "area", "capacity",
                    "guest", "moon", "calendar", "camera"}:
        return icon(name)
    return mark_safe(
        f'<img class="icon house-icon house-icon--{name}" '
        f'src="{static(f"img/house-icons/{name}.png")}" alt="" aria-hidden="true">'
    )
