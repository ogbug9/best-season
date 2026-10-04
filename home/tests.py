from home.models import HomePage

import importlib
from types import SimpleNamespace
from django.apps import apps
from django.db import connection

from wagtail.models import Page, Site
from wagtail.test.utils import WagtailPageTestCase


class HomeSetUpTests(WagtailPageTestCase):
    """
    Tests for basic page structure setup and HomePage creation.
    """

    def test_root_create(self):
        root_page = Page.objects.get(pk=1)
        self.assertIsNotNone(root_page)

    def test_homepage_create(self):
        root_page = Page.objects.get(pk=1)
        homepage = HomePage(title="Home")
        root_page.add_child(instance=homepage)
        self.assertTrue(HomePage.objects.filter(title="Home").exists())


class HomeTests(WagtailPageTestCase):
    """
    Tests for homepage functionality and rendering.
    """

    def setUp(self):
        """
        Create a homepage instance for testing.
        """
        root_page = Page.get_first_root_node()
        Site.objects.create(
            hostname="testsite", root_page=root_page, is_default_site=True
        )
        self.homepage = HomePage(title="Home")
        root_page.add_child(instance=self.homepage)

    def test_homepage_is_renderable(self):
        self.assertPageIsRenderable(self.homepage)

    def test_homepage_template_used(self):
        response = self.client.get(self.homepage.url)
        self.assertTemplateUsed(response, "home/home_page.html")


class ApprovedAboutCopyTests(WagtailPageTestCase):
    def test_copy_update_preserves_other_fields_draft_and_revision_history(self):
        migration = importlib.import_module('home.migrations.0007_approved_home_about_copy')
        first = '<p data-block-key="editor">Вступление редактора.</p>'
        page = Page.get_first_root_node().add_child(instance=HomePage(
            title='Approved copy', slug='approved-copy',
            about_text=first + '<p>' + migration.OLD + '</p>',
        ))
        old_revision = page.save_revision()
        page.hero_subtitle = 'Незавершённая редакторская правка'
        draft = page.save_revision()
        migration.update_copy(apps, SimpleNamespace(connection=connection))
        migration.update_copy(apps, SimpleNamespace(connection=connection))
        page.refresh_from_db(); draft.refresh_from_db(); old_revision.refresh_from_db()
        self.assertEqual(page.about_text, first + '<p>' + migration.NEW + '</p>')
        self.assertEqual(draft.content['about_text'], page.about_text)
        self.assertEqual(draft.content['hero_subtitle'], 'Незавершённая редакторская правка')
        self.assertIn(migration.OLD, old_revision.content['about_text'])

    def test_copy_update_leaves_custom_editor_paragraph_unchanged(self):
        migration = importlib.import_module('home.migrations.0007_approved_home_about_copy')
        text = '<p>Территория глэмпинга: собственный текст редактора.</p>'
        page = Page.get_first_root_node().add_child(instance=HomePage(
            title='Custom copy', slug='custom-copy', about_text=text,
        ))
        draft = page.save_revision()
        migration.update_copy(apps, SimpleNamespace(connection=connection))
        page.refresh_from_db(); draft.refresh_from_db()
        self.assertEqual(page.about_text, text)
        self.assertEqual(draft.content['about_text'], text)
