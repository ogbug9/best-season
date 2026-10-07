from django.http import HttpResponse
from django.views.decorators.cache import cache_control


@cache_control(max_age=60 * 60 * 24)
def robots_txt(request):
    """robots.txt по п. 10.8 ТЗ. Отдаётся вьюхой, а не статикой,
    чтобы адрес карты сайта подставлялся под текущий домен —
    иначе при переезде на best-season.online пришлось бы править файл."""
    host = f"{request.scheme}://{request.get_host()}"
    lines = [
        "User-agent: *",
        "Disallow: /admin/",
        "Disallow: /django-admin/",
        "Disallow: /search/",
        "Allow: /",
        "",
        f"Sitemap: {host}/sitemap.xml",
        "",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain; charset=utf-8")


def server_error(request):
    """500 без зависимости от базы и контекстных процессоров (docs/dop-stranicy/21).

    Контакты подставляются, только если настройки удалось прочитать: если
    упала сама база, гость всё равно получит страницу, а не «Server Error».
    """
    from django.template.loader import render_to_string

    settings = None
    try:
        from core.models import SiteSettings
        from wagtail.models import Site

        site = Site.objects.filter(is_default_site=True).first()
        settings = SiteSettings.for_site(site) if site else None
    except Exception:  # база недоступна — показываем страницу без контактов
        settings = None
    try:
        body = render_to_string("500.html", {"s": settings})
    except Exception:
        body = "<h1>Что-то пошло не так</h1><p>Мы уже чиним. Попробуйте обновить страницу через минуту.</p>"
    return HttpResponse(body, status=500)
