"""Отдача изображений по п. 10.3 ТЗ: WebP с фолбэком, srcset, lazy.

Вынесено в тег, а не расставляется руками по шаблонам: иначе на 18 страницах
неизбежно разъедутся наборы размеров, и замер PageSpeed на приёмке
(п. 1.2, ≥80 на мобильных) начнёт зависеть от того, какую страницу открыли.
"""

from django import template
from django.utils.safestring import mark_safe

register = template.Library()

# Ширины подобраны под реальные точки: узкий телефон, телефон, планшет,
# ноутбук, десктоп. Плюс двойные для экранов с высокой плотностью.
DEFAULT_WIDTHS = (360, 480, 768, 1024, 1440, 1920)

PRESETS = {
    # имя: (соотношение сторон ш/в, ширины, значение sizes)
    "hero":    (16 / 9, (480, 768, 1024, 1440, 1920), "100vw"),
    "card":    (3 / 2, (360, 480, 768), "(min-width: 900px) 380px, (min-width: 600px) 50vw, 100vw"),
    "gallery": (4 / 3, (480, 768, 1024, 1440), "(min-width: 900px) 800px, 100vw"),
    "square":  (1, (240, 360, 480), "(min-width: 600px) 240px, 40vw"),
}


@register.simple_tag
def picture(image, preset="card", alt="", loading="lazy", css_class="", sizes=None):
    """Отдаёт <picture> с WebP-источником и JPEG-фолбэком.

    loading="eager" ставить только для картинки первого экрана — она
    участвует в замере LCP, и ленивая загрузка её ухудшает.
    """
    if not image:
        return ""

    ratio, widths, default_sizes = PRESETS.get(preset, PRESETS["card"])
    sizes = sizes or default_sizes

    webp_srcset, jpeg_srcset = [], []
    fallback = None

    for width in widths:
        height = max(1, round(width / ratio))
        spec = f"fill-{width}x{height}"
        try:
            webp = image.get_rendition(f"{spec}|format-webp")
            jpeg = image.get_rendition(f"{spec}|format-jpeg")
        except Exception:
            # Битый или нечитаемый файл не должен ронять всю страницу
            continue
        webp_srcset.append(f"{webp.url} {width}w")
        jpeg_srcset.append(f"{jpeg.url} {width}w")
        fallback = jpeg

    if fallback is None:
        return ""

    alt_text = alt or getattr(image, "title", "") or ""
    class_attr = f' class="{css_class}"' if css_class else ""
    # width/height обязательны: без них браузер не резервирует место
    # и уезжает CLS, а он предмет приёмки (п. 1.2, ≤0,1)
    html = (
        "<picture>"
        f'<source type="image/webp" srcset="{", ".join(webp_srcset)}" sizes="{sizes}">'
        f'<img src="{fallback.url}" srcset="{", ".join(jpeg_srcset)}" sizes="{sizes}"'
        f' width="{fallback.width}" height="{fallback.height}"'
        f' alt="{alt_text}" loading="{loading}" decoding="async"{class_attr}>'
        "</picture>"
    )
    return mark_safe(html)
