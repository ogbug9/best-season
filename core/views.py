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
