"""Отдача изображений по п. 10.3 ТЗ: WebP с фолбэком, srcset, lazy.

Вынесено в тег, а не расставляется руками по шаблонам: иначе на 18 страницах
неизбежно разъедутся наборы размеров, и замер PageSpeed на приёмке
(п. 1.2, ≥80 на мобильных) начнёт зависеть от того, какую страницу открыли.
"""

from django import template
from django.conf import settings
from django.utils.html import escape
from django.utils.safestring import mark_safe

register = template.Library()

# Ширины подобраны под реальные точки: узкий телефон, телефон, планшет,
# ноутбук, десктоп. Плюс двойные для экранов с высокой плотностью.
DEFAULT_WIDTHS = (360, 480, 768, 1024, 1440, 1920)

PRESETS = {
    # имя: (соотношение сторон ш/в, ширины, значение sizes)
    "hero":    (16 / 9, (480, 768, 1024, 1440, 1920), "100vw"),
    # Портретный кроп под экран телефона: ширина горизонтального файла
    # не должна уменьшать высоту первого экрана до 464 px.
    "hero_mobile": (9 / 19.5, (640, 828, 1170), "100vw"),
    "card":    (3 / 2, (360, 480, 768), "(min-width: 900px) 380px, (min-width: 600px) 50vw, 100vw"),
    "house_card": (61 / 50, (360, 610, 768, 1220), "(min-width: 900px) 610px, (min-width: 600px) 50vw, 100vw"),
    "mosaic":  (None, (360, 500, 768, 1024), "(min-width: 900px) 500px, 100vw"),
    "review":  (397 / 220, (397, 794), "(min-width: 900px) 397px, 100vw"),
    "promo":   (360 / 220, (360, 480, 768), "(min-width: 900px) 360px, (min-width: 600px) 50vw, 100vw"),
    "promo_mobile": (None, (360, 480, 768), "100vw"),
    "gallery": (4 / 3, (480, 768, 1024, 1440), "(min-width: 900px) 800px, 100vw"),
    "square":  (1, (240, 360, 480), "(min-width: 600px) 240px, 40vw"),
}


def _focus_attr(image):
    """Передать фокус Wagtail в CSS, сохранив приоритет правил отдельных плиток."""
    x, y = getattr(image, "focal_point_x", None), getattr(image, "focal_point_y", None)
    if x is None or y is None or not image.width or not image.height:
        return ""
    return f' style="--focus: {round(x / image.width * 100)}% {round(y / image.height * 100)}%"'


@register.simple_tag
def picture(image, preset="card", alt=None, loading="lazy", css_class="", sizes=None,
            mobile_original=False, mobile_preset=None, mobile_image=None):
    """Отдаёт <picture> с WebP-источником и JPEG-фолбэком.

    loading="eager" ставить только для картинки первого экрана — она
    участвует в замере LCP, и ленивая загрузка её ухудшает.
    """
    if not image:
        return ""

    ratio, widths, default_sizes = PRESETS.get(preset, PRESETS["card"])
    sizes = sizes or default_sizes
    mobile_source = _mobile_sources(mobile_image or image, mobile_preset) if mobile_preset else ""

    # On the small production container, building all WebP/JPEG srcset variants
    # during the first page request can exceed Gunicorn's 120-second timeout.
    # Serve the existing upload until renditions can be prepared outside requests.
    if not getattr(settings, "GENERATE_IMAGE_RENDITIONS_ON_REQUEST", True):
        alt_text = escape(alt if alt is not None else getattr(image, "title", ""))
        class_attr = f' class="{escape(css_class)}"' if css_class else ""
        return mark_safe(
            f"<picture>{mobile_source}"
            f'<img src="{escape(image.file.url)}"'
            f' width="{image.width}" height="{image.height}"'
            f' alt="{alt_text}" loading="{escape(loading)}" decoding="async"{class_attr}{_focus_attr(image)}>'
            "</picture>"
        )

    webp_srcset, jpeg_srcset = [], []
    fallback = None

    for width in widths:
        spec = f"fill-{width}x{max(1, round(width / ratio))}" if ratio else f"width-{width}"
        try:
            webp = image.get_rendition(f"{spec}|format-webp")
            jpeg = image.get_rendition(f"{spec}|format-jpeg")
        except Exception:
            # Битый или нечитаемый файл не должен ронять всю страницу
            continue
        # Wagtail не увеличивает исходник: дескриптор описывает файл,
        # а одинаковые реальные ширины не повторяются в srcset.
        if any(item.endswith(f" {webp.width}w") for item in webp_srcset):
            continue
        webp_srcset.append(f"{webp.url} {webp.width}w")
        jpeg_srcset.append(f"{jpeg.url} {jpeg.width}w")
        fallback = jpeg

    if fallback is None:
        return ""

    # Пустая строка в alt — осознанный выбор для декоративных картинок
    # (фон первого экрана), её нельзя подменять названием файла: имя вида
    # b5dedcca94a6... как подпись бесполезно и мешает читалкам экрана.
    # Название подставляется только если alt вообще не передан.
    alt_text = escape(alt if alt is not None else getattr(image, "title", ""))
    class_attr = f' class="{escape(css_class)}"' if css_class else ""
    # width/height обязательны: без них браузер не резервирует место
    # и уезжает CLS, а он предмет приёмки (п. 1.2, ≤0,1)
    mobile_source = mobile_source or (
        f'<source media="(max-width: 699px)" srcset="{escape(image.file.url)}">'
        if mobile_original else ""
    )
    html = (
        "<picture>"
        f'{mobile_source}'
        f'<source type="image/webp" srcset="{", ".join(webp_srcset)}" sizes="{sizes}">'
        f'<img src="{fallback.url}" srcset="{", ".join(jpeg_srcset)}" sizes="{sizes}"'
        f' width="{fallback.width}" height="{fallback.height}"'
        f' alt="{alt_text}" loading="{loading}" decoding="async"{class_attr}{_focus_attr(image)}>'
        "</picture>"
    )
    return mark_safe(html)


def mobile_specs(preset):
    ratio, widths, _ = PRESETS[preset]
    for width in widths:
        spec = f"fill-{width}x{max(1, round(width / ratio))}" if ratio else f"width-{width}"
        for extension in ('webp', 'jpeg'):
            yield width, extension, f'{spec}|format-{extension}|{extension}quality-82'


@register.simple_tag
def mobile_image(image, preset='hero_mobile'):
    if not image:
        return None
    _, _, spec = next(mobile_specs(preset))
    if not getattr(settings, 'GENERATE_IMAGE_RENDITIONS_ON_REQUEST', True):
        return image.renditions.filter(filter_spec=spec).first()
    try:
        return image.get_rendition(spec)
    except Exception:
        return None


def _mobile_srcsets(image, preset):
    """Мобильные srcset по форматам, без создания вариантов в production."""
    generate = getattr(settings, 'GENERATE_IMAGE_RENDITIONS_ON_REQUEST', True)
    specs = list(mobile_specs(preset))
    cached = {} if generate else {
        item.filter_spec: item for item in image.renditions.filter(
            filter_spec__in=[spec for _, _, spec in specs]
        )
    }
    sources = {'webp': [], 'jpeg': []}
    for width, extension, spec in specs:
        try:
            rendition = image.get_rendition(spec) if generate else cached.get(spec)
        except Exception:
            continue
        if rendition and not any(item.endswith(f' {rendition.width}w') for item in sources[extension]):
            sources[extension].append(f'{escape(rendition.url)} {rendition.width}w')
    return sources


def _mobile_sources(image, preset):
    return ''.join(
        f'<source media="(max-width: 699px)" type="image/{extension}"'
        f' srcset="{", ".join(srcset)}" sizes="100vw">'
        for extension, srcset in _mobile_srcsets(image, preset).items() if srcset
    )


@register.simple_tag
def mobile_srcset(image, preset='hero_mobile', extension='webp'):
    """Те же файлы для preload, что и для мобильного <source>."""
    if not image:
        return ''
    return ', '.join(_mobile_srcsets(image, preset)[extension])
