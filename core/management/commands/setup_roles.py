"""Создаёт роль «Редактор» по разделу 8 ТЗ.

Команда идемпотентна и вызывается при каждом старте из run.py: права
описаны здесь кодом, а не выставляются руками в админке, иначе при
пересоздании окружения или передаче проекта заказчику (п. 10.15 ТЗ)
их пришлось бы восстанавливать по памяти.

Роль «Админ» отдельно не заводится — это суперпользователь Django.
"""

from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand
from django.db import transaction
from wagtail.models import (
    Collection,
    GroupCollectionPermission,
    GroupPagePermission,
    Page,
)

EDITOR_GROUP = "Редактор"

# Доступ в саму админку.
ADMIN_ACCESS = [("wagtailadmin", "access_admin")]

# Права на дерево страниц. Публикация даётся: по п. 8 ТЗ редактор правит
# тексты, фото и цены сам, без второго человека на подтверждении.
# Удаления страниц нет намеренно — снести раздел целиком редактор не может.
PAGE_PERMISSIONS = ["add_page", "change_page", "publish_page"]

# Медиатека: загружать и выбирать можно, удалять — нет.
COLLECTION_PERMISSIONS = [
    ("wagtailimages", "add_image"),
    ("wagtailimages", "change_image"),
    ("wagtailimages", "choose_image"),
    ("wagtaildocs", "add_document"),
    ("wagtaildocs", "change_document"),
    ("wagtaildocs", "choose_document"),
]

# Справочники, которые редактор ведёт сам.
SNIPPET_PERMISSIONS = [
    ("reviews", "review", ["add", "change", "delete", "view"]),
    ("promotions", "promotion", ["add", "change", "delete", "view"]),
    ("services", "service", ["add", "change", "delete", "view"]),
    # Удобства — общий справочник для всех домов. Добавлять новые можно,
    # удалять нет: удаление вычистило бы пункт «Что входит» сразу у всех домов.
    ("core", "amenity", ["add", "change", "view"]),
    # Заявки: смотреть и менять статус. Удаление недоступно — заявка
    # с согласием на обработку ПД должна оставаться в системе (раздел 11 ТЗ).
    ("forms", "formsubmission", ["change", "view"]),
]

# Явно НЕ выдаётся редактору (перечислено, чтобы при правках роли
# случайно не добавили): настройки сайта, пользователи и группы,
# коллекции, локали, редиректы, воркфлоу, сайты.
DENIED_CODENAMES = {
    "change_sitesettings",
    "add_user", "change_user", "delete_user",
    "add_group", "change_group", "delete_group",
    "add_collection", "change_collection", "delete_collection",
    "add_locale", "change_locale", "delete_locale",
    "add_redirect", "change_redirect", "delete_redirect",
    "add_workflow", "change_workflow", "delete_workflow",
    "add_site", "change_site", "delete_site",
    "delete_page", "bulk_delete_page",
}


class Command(BaseCommand):
    help = "Создаёт или обновляет роль «Редактор» с правами по разделу 8 ТЗ"

    @transaction.atomic
    def handle(self, *args, **options):
        group, created = Group.objects.get_or_create(name=EDITOR_GROUP)
        self.stdout.write(
            f"Группа «{EDITOR_GROUP}»: {'создана' if created else 'уже есть, обновляю права'}"
        )

        # Права выставляются заново целиком, чтобы команда была идемпотентной
        # и снимала лишнее, если роль правили руками в админке.
        group.permissions.clear()
        GroupPagePermission.objects.filter(group=group).delete()
        GroupCollectionPermission.objects.filter(group=group).delete()

        granted = []

        for app_label, codename in ADMIN_ACCESS:
            group.permissions.add(self._perm(app_label, codename))
            granted.append(codename)

        # Права на страницы выдаются от корня сайта, а не от корня дерева:
        # так редактор не дотянется до служебных страниц вне сайта.
        site_root = Page.objects.filter(depth=2).first()
        if site_root is None:
            self.stdout.write(self.style.WARNING("Корень сайта не найден, права на страницы не выданы"))
        else:
            for codename in PAGE_PERMISSIONS:
                GroupPagePermission.objects.create(
                    group=group,
                    page=site_root,
                    permission=self._perm("wagtailcore", codename),
                )
                granted.append(f"page:{codename}")

        root_collection = Collection.get_first_root_node()
        for app_label, codename in COLLECTION_PERMISSIONS:
            GroupCollectionPermission.objects.create(
                group=group,
                collection=root_collection,
                permission=self._perm(app_label, codename),
            )
            granted.append(codename)

        for app_label, model, actions in SNIPPET_PERMISSIONS:
            for action in actions:
                codename = f"{action}_{model}"
                perm = self._perm(app_label, codename)
                if perm is None:
                    continue
                group.permissions.add(perm)
                granted.append(codename)

        # Страховка: если в список выше когда-нибудь просочится запрещённое право.
        leaked = [c for c in granted if c in DENIED_CODENAMES]
        if leaked:
            raise ValueError(f"В роль «Редактор» попали запрещённые права: {leaked}")

        self.stdout.write(self.style.SUCCESS(f"Готово, выдано прав: {len(granted)}"))

    def _perm(self, app_label, codename):
        try:
            return Permission.objects.get(
                content_type__app_label=app_label, codename=codename
            )
        except Permission.DoesNotExist:
            self.stdout.write(
                self.style.WARNING(f"Права {app_label}.{codename} нет — пропускаю")
            )
            return None
