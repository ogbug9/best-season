import shutil
import tempfile
from importlib import import_module
from types import SimpleNamespace

from django.template.loader import render_to_string
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings

from core.templatetags.content_tags import filled

directions = import_module('core.migrations.0025_directions_faq_facts')


class FilledFilterTests(SimpleTestCase):
    def test_service_marks_are_empty(self):
        for value in ('', None, 'Описание', 'уточняется', '<p>Маршрут — Текст ожидается от заказчика.</p>',
                      '<p>Контакты и реквизиты берутся из настроек сайта — заполните их.</p>'):
            self.assertEqual(filled(value), '', value)

    def test_real_copy_is_kept(self):
        self.assertEqual(filled('100 км от Москвы'), '100 км от Москвы')
        self.assertEqual(filled('<p>Описание маршрута до реки</p>'), '<p>Описание маршрута до реки</p>')


class DirectionsMigrationTests(SimpleTestCase):
    def test_only_seed_values_are_replaced(self):
        changed = directions.updated({
            'car_distance': 'уточняется', 'car_time': '2 часа', 'transfer_price': 'уточняется',
            'transit_route': '<p>Названия станций — Текст ожидается от заказчика.</p>',
        })
        self.assertEqual(changed['car_distance'], '100 км от Москвы')
        self.assertEqual(changed['transfer_price'], '')
        self.assertIn('Тарусская', changed['transit_route'])
        self.assertNotIn('car_time', changed)


class InProgressNoteTests(TestCase):
    def render(self, in_progress):
        request = RequestFactory().get('/')
        return render_to_string('includes/in_progress_note.html', {'page': SimpleNamespace(in_progress=in_progress)}, request=request)

    def test_note_follows_the_flag(self):
        self.assertIn('class="in-progress"', self.render(True))
        self.assertNotIn('in-progress', self.render(False))


MEDIA_TMP = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=MEDIA_TMP)
class GalleryArchiveMigrationTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA_TMP, ignore_errors=True)

    def test_empty_gallery_gets_archive_photos_once(self):
        from django.apps import apps
        from django.db import connection
        from wagtail.images import get_image_model
        from wagtail.images.tests.utils import get_test_image_file
        from wagtail.models import Page
        from core.models import GalleryPage

        gallery = import_module('core.migrations.0027_gallery_archive_photos')
        root = Page.objects.get(depth=1)
        page = root.add_child(instance=GalleryPage(title='Галерея', slug='galereya-test'))
        page.save_revision()
        Image = get_image_model()
        for name in ('b', 'a'):
            Image.objects.create(title=f'BS archive gallery/{name}', file=get_test_image_file())
        editor = SimpleNamespace(connection=connection)
        gallery.link(apps, editor)
        self.assertEqual([p.image.title for p in page.photos.order_by('sort_order')],
                         ['BS archive gallery/a', 'BS archive gallery/b'])
        page.refresh_from_db()
        self.assertEqual(len(page.latest_revision.content['photos']), 2)
        gallery.link(apps, editor)
        self.assertEqual(page.photos.count(), 2)


class ComponentTemplatesTests(TestCase):
    def render(self, name, context):
        return render_to_string(name, context, request=RequestFactory().get('/'))

    def test_fact_cards_skip_empty_values(self):
        html = self.render('includes/fact_cards.html', {'facts': [('100 км', 'от Москвы'), ('', 'трансфер')]})
        self.assertEqual(html.count('fact-cards__item'), 1)

    def test_video_slot_without_poster_is_a_placeholder(self):
        html = self.render('includes/video_slot.html', {'poster': None, 'title': 'Утро на террасе', 'note': 'Снимаем осенью'})
        self.assertIn('video-slot--empty', html)
        self.assertNotIn('<video', html)
