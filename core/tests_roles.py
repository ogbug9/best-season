"""Права роли «Редактор» на справочники (раздел 8 ТЗ)."""
from io import StringIO

from django.contrib.auth.models import Group
from django.core.management import call_command
from django.test import TestCase

EDITOR_SNIPPETS = {
    "amenitygroup": {"add", "change", "view"},
    "amenity": {"add", "change", "view"},
    "faqitem": {"add", "change", "delete", "view"},
    "territoryitem": {"add", "change", "delete", "view"},
    "nearbyplace": {"add", "change", "delete", "view"},
    "event": {"add", "change", "delete", "view"},
    "videoclip": {"add", "change", "delete", "view"},
}


class EditorRoleSnippetTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("setup_roles", stdout=StringIO())
        cls.group = Group.objects.get(name="Редактор")
        cls.codenames = set(cls.group.permissions.values_list("codename", flat=True))

    def test_editor_gets_reference_permissions(self):
        for model, actions in EDITOR_SNIPPETS.items():
            for action in actions:
                self.assertIn(f"{action}_{model}", self.codenames)

    def test_no_delete_where_it_breaks_shared_data(self):
        self.assertNotIn("delete_amenitygroup", self.codenames)
        self.assertNotIn("delete_amenity", self.codenames)

    def test_settings_and_users_stay_closed(self):
        for codename in ("change_sitesettings", "add_user", "delete_page"):
            self.assertNotIn(codename, self.codenames)

    def test_command_is_idempotent(self):
        call_command("setup_roles", stdout=StringIO())
        again = set(self.group.permissions.values_list("codename", flat=True))
        self.assertEqual(again, self.codenames)


class EditorContactSettingsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        from django.contrib.auth.models import User

        call_command("seed_pages", "--create-only", stdout=StringIO(), stderr=StringIO())
        call_command("setup_roles", stdout=StringIO())
        cls.editor = User.objects.create_user("editor_contacts", password="x-test-pass")
        cls.editor.groups.add(Group.objects.get(name="Редактор"))

    def test_editor_has_contacts_but_not_full_settings(self):
        perms = set(Group.objects.get(name="Редактор").permissions.values_list("codename", flat=True))
        self.assertIn("change_contactsettings", perms)
        self.assertNotIn("change_sitesettings", perms)

    def test_contact_form_has_no_hotel_id_or_metrika(self):
        from core.models import ContactSettings
        from wagtail.admin.panels import ObjectList

        form_class = ObjectList(ContactSettings.panels).bind_to_model(ContactSettings).get_form_class()
        fields = set(form_class.base_fields)
        self.assertIn("phone", fields)
        self.assertIn("telegram_url", fields)
        self.assertNotIn("kontur_hotel_id", fields)
        self.assertNotIn("yandex_metrika_id", fields)
        self.assertNotIn("consent_text", fields)

    def test_editor_edits_contacts_over_http(self):
        from wagtail.models import Site

        self.client.force_login(self.editor)
        site = Site.objects.get(is_default_site=True)
        url = f"/admin/settings/core/contactsettings/{site.pk}/"
        self.assertEqual(self.client.get(url).status_code, 200)
        # Полные настройки (hotelId, Метрика) редактору недоступны: перенаправление на панель.
        self.assertEqual(self.client.get(f"/admin/settings/core/sitesettings/{site.pk}/").status_code, 302)
