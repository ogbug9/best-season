"""Reference migrations must preserve editor copy, links and revision history."""
import importlib
from types import SimpleNamespace
from django.apps import apps
from django.db import connection
from django.test import TestCase
from wagtail.models import Page
from core.models import ContentPage, FaqItem
from home.models import HomePage


class ReferenceCopyTests(TestCase):
    def test_faq_updates_only_seed_answer_and_is_idempotent(self):
        migration = importlib.import_module('core.migrations.0022_faq_reference_05_10')
        old_question, old_answer, new_question, new_answer = migration.UPDATES[6]
        item = FaqItem.objects.create(question=old_question, answer=old_answer, show_on_home=False)
        editor = FaqItem.objects.create(question=old_question, answer='<p>Правка редактора со своим условием залога.</p>')
        for _ in range(2):
            migration.update_faq(apps, SimpleNamespace(connection=connection))
        item.refresh_from_db(); editor.refresh_from_db()
        self.assertEqual(item.answer, new_answer)
        self.assertEqual(item.question, new_question)
        self.assertFalse(item.show_on_home)
        self.assertEqual(editor.answer, '<p>Правка редактора со своим условием залога.</p>')

    def test_home_faq_preserves_editor_changed_link_with_same_visible_text(self):
        migration = importlib.import_module('core.migrations.0022_faq_reference_05_10')
        Page.get_first_root_node().add_child(instance=ContentPage(title='Как добраться', slug='kak-dobratsya'))
        old_question, old_answer, _, _ = migration.UPDATES[0]
        custom = old_answer.replace('https://yandex.com/maps/-/CPsvELJx', 'https://example.com/editor-route')
        item = FaqItem.objects.create(question=old_question, answer=custom)
        migration.update_faq(apps, SimpleNamespace(connection=connection))
        item.refresh_from_db()
        self.assertEqual(item.answer, custom)

    def test_about_updates_published_copy_and_latest_draft_preserving_history(self):
        migration = importlib.import_module('home.migrations.0008_about_reference_05_10')
        page = HomePage.objects.filter(slug='home').first()
        if page is None:
            page = Page.get_first_root_node().add_child(instance=HomePage(title='Home', slug='home'))
        page.about_text = '<p>' + migration.OLD + '</p>'
        page.save()
        old_revision = page.save_revision()
        page.hero_subtitle = 'Незавершённая правка редактора'
        draft = page.save_revision()
        for _ in range(2):
            migration.update_copy(apps, SimpleNamespace(connection=connection))
        page.refresh_from_db(); draft.refresh_from_db(); old_revision.refresh_from_db()
        self.assertEqual(page.about_text, '<p>' + migration.NEW + '</p>')
        self.assertEqual(draft.content['about_text'], page.about_text)
        self.assertEqual(draft.content['hero_subtitle'], 'Незавершённая правка редактора')
        self.assertIn(migration.OLD, old_revision.content['about_text'])


class AboutNurseryNameMigrationTests(TestCase):
    def test_only_the_exact_phrase_is_removed(self):
        import importlib
        clean = importlib.import_module('core.migrations.0024_about_remove_nursery_name').clean
        data, changed = clean([{'type': 'content', 'value': {'intro': ['Скнижка, рядом питомник «Долина роз»', 'Другой текст']}}])
        self.assertTrue(changed)
        self.assertEqual(data[0]['value']['intro'], ['Скнижка, рядом питомник', 'Другой текст'])
        edited = [{'type': 'content', 'value': {'intro': ['Редактор написал по-своему']}}]
        self.assertFalse(clean(edited)[1])
