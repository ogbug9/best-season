"""Ограничения для роли «Редактор», которые не выражаются правами Wagtail.

В Wagtail право change_page само по себе разрешает удалять конечные страницы
(wagtail/models/pages.py, PagePermissionTester.can_delete): выдать «править,
но не удалять» через GroupPagePermission нельзя. По разделу 8 ТЗ редактор
не должен иметь возможности снести страницу дома, поэтому удаление
перехватывается хуками и остаётся только у суперпользователя.
"""

from django.contrib.admin.utils import quote
from django.shortcuts import redirect
from django.urls import reverse
from wagtail import hooks
from wagtail.admin import messages

DELETE_DENIED = (
    "Удаление страниц доступно только администратору. "
    "Чтобы убрать страницу с сайта, снимите её с публикации."
)


@hooks.register("before_delete_page")
def deny_page_delete_for_editors(request, page):
    if request.user.is_superuser:
        return None
    messages.error(request, DELETE_DENIED)
    return redirect(reverse("wagtailadmin_explore", args=[page.get_parent().id]))


@hooks.register("before_bulk_action")
def deny_bulk_page_delete_for_editors(request, action_type, objects, action_class_instance):
    """Массовое удаление из списка страниц — тот же запрет."""
    if action_type != "delete" or request.user.is_superuser:
        return None
    messages.error(request, DELETE_DENIED)
    return redirect(reverse("wagtailadmin_home"))


@hooks.register("after_publish_page")
def warn_short_gallery(request, page):
    """Напоминание о недоборе галереи — п. 4.1.2 ТЗ требует ≥15 фото.

    Публикацию не блокируем: на этапе разработки фото добираются
    постепенно. Но молча пропускать нельзя — иначе недобор всплывёт
    на приёмке. Полный список — в отчёте «Галереи домов».
    """
    from houses.models import MIN_GALLERY_IMAGES, HousePage

    page = page.specific
    if not isinstance(page, HousePage):
        return
    if page.gallery_is_short:
        messages.warning(
            request,
            f"В галерее «{page.title}» {page.gallery_count} фото из "
            f"{MIN_GALLERY_IMAGES}, которые требует п. 4.1.2 ТЗ. "
            f"Страница опубликована, но к приёмке галерею нужно добрать.",
        )
