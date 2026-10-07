import json
from pathlib import Path
from django import template
from django.db import DatabaseError
from django.utils.html import conditional_escape, format_html, format_html_join, strip_tags
from django.utils.safestring import mark_safe

register = template.Library()
DEFAULTS = json.loads((Path(__file__).resolve().parents[1] / 'data/interface_text.json').read_text(encoding='utf-8'))


def texts(request):
    if request is None:
        from core.models import InterfaceText
        try:
            return dict(InterfaceText.objects.values_list('key', 'text'))
        except DatabaseError:
            return {}
    if not hasattr(request, '_bs_interface_texts'):
        from core.models import InterfaceText
        try:
            request._bs_interface_texts = dict(InterfaceText.objects.values_list('key', 'text'))
        except DatabaseError:
            request._bs_interface_texts = {}
    return request._bs_interface_texts


def value(request, key, default=''):
    return texts(request).get(key, DEFAULTS.get(key, {}).get('text', default))


# Служебные пометки сида и админки, которые гость видеть не должен.
PLACEHOLDER_MARKERS = ('Текст ожидается от заказчика', 'берутся из настроек сайта')
PLACEHOLDER_VALUES = {'описание', 'уточняется'}


@register.filter
def filled(value):
    """Пустая строка вместо незаполненного поля или служебной пометки."""
    text = ' '.join(strip_tags(str(value or '')).split())
    if (not text or text.lower().rstrip('.') in PLACEHOLDER_VALUES
            or any(marker in text for marker in PLACEHOLDER_MARKERS)):
        return ''
    return value


@register.simple_tag(takes_context=True)
def cms_text(context, key):
    # Escape plain text; line breaks are the only supported formatting.
    # Без request (страница 500) тексты берутся из базы или из значений по умолчанию.
    return mark_safe(str(conditional_escape(value(context.get('request'), key))).replace('\n', '<br>'))


@register.simple_tag
def legal_table(value):
    """Plain cells, real spans and source column labels for mobile reflow."""
    rows = value.get('data', [])
    headers = rows[0] if rows and value.get('first_row_is_table_header') else []
    spans, covered = {}, set()
    for merge in value.get('mergeCells', []):
        row, col = merge['row'], merge['col']
        rowspan, colspan = merge['rowspan'], merge['colspan']
        spans[(row, col)] = (rowspan, colspan)
        covered.update((r, c) for r in range(row, row+rowspan) for c in range(col, col+colspan) if (r, c) != (row, col))
    rendered = []
    for row_index, row in enumerate(rows):
        cells = []
        for col_index, cell in enumerate(row):
            if (row_index, col_index) in covered:
                continue
            tag = 'th' if (headers and row_index == 0) or (value.get('first_col_is_header') and col_index == 0) else 'td'
            rowspan, colspan = spans.get((row_index, col_index), (1, 1))
            label = headers[col_index] if headers and col_index < len(headers) else ''
            text = mark_safe(str(conditional_escape(cell or '')).replace('\n', '<br>'))
            scope = format_html(' scope="{}"', 'col' if headers and row_index == 0 else 'row') if tag == 'th' else ''
            cells.append(format_html('<{}{} rowspan="{}" colspan="{}" data-label="{}">{}</{}>', mark_safe(tag), scope, rowspan, colspan, label, text, mark_safe(tag)))
        rendered.append(format_html('<tr>{}</tr>', format_html_join('', '{}', ((cell,) for cell in cells))))
    heading = format_html('<thead>{}</thead>', rendered[0]) if headers else ''
    body = rendered[1:] if headers else rendered
    caption = format_html('<caption>{}</caption>', value['table_caption']) if value.get('table_caption') else ''
    return format_html('<table>{}{}<tbody>{}</tbody></table>', caption, heading, format_html_join('', '{}', ((row,) for row in body)))


@register.simple_tag
def video_clip(slot):
    """Опубликованный ролик для места или None — тогда выводится заглушка."""
    if not slot:
        return None
    from core.models import VideoClip
    try:
        return VideoClip.objects.select_related("file", "poster").filter(slot=slot, is_published=True).first()
    except DatabaseError:
        return None

