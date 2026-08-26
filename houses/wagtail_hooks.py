"""Отчёт «Галереи домов» — сколько фото добрано на каждый дом.

Публикацию недобранной галереи мы намеренно не блокируем: фото
добираются по ходу работы. Но требование п. 4.1.2 ТЗ (≥15 фото на дом)
остаётся в силе, поэтому нужен способ в любой момент увидеть общую
картину, а не вспоминать о недоборе на приёмке.
"""

from django.shortcuts import render
from django.urls import path, reverse
from wagtail import hooks
from wagtail.admin.menu import MenuItem

from .models import MIN_GALLERY_IMAGES, HousePage


def gallery_report(request):
    rows = []
    for house in HousePage.objects.all().order_by("sort_order_index", "title"):
        count = house.gallery_images.count()
        rows.append(
            {
                "house": house,
                "count": count,
                "missing": max(0, MIN_GALLERY_IMAGES - count),
                "ok": count >= MIN_GALLERY_IMAGES,
                "edit_url": reverse("wagtailadmin_pages:edit", args=[house.id]),
            }
        )
    return render(
        request,
        "houses/admin/gallery_report.html",
        {
            "rows": rows,
            "minimum": MIN_GALLERY_IMAGES,
            "total_missing": sum(r["missing"] for r in rows),
        },
    )


@hooks.register("register_admin_urls")
def gallery_report_urls():
    return [
        path(
            "otchety/galerei-domov/",
            gallery_report,
            name="houses_gallery_report",
        )
    ]


@hooks.register("register_admin_menu_item")
def gallery_report_menu():
    return MenuItem(
        "Галереи домов",
        reverse("houses_gallery_report"),
        icon_name="image",
        order=900,
    )
