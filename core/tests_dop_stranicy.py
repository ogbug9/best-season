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
        self.assertIn('class="dev-strip"', self.render(True))
        self.assertNotIn('dev-strip', self.render(False))


class DopContentTests(SimpleTestCase):
    def test_guide_is_consistent(self):
        from core import dop_content
        kinds = {key for key, _ in dop_content.GUIDE_KINDS}
        keys = [place['key'] for place in dop_content.GUIDE]
        self.assertEqual(len(keys), len(set(keys)))
        for place in dop_content.guide_with_sources():
            self.assertTrue(place['key'].isascii(), place['key'])
            self.assertIn(place['kind'], kinds)
            self.assertTrue(set(place['days']) <= set(range(7)))
            for link in place['links']:
                self.assertTrue(link[1].startswith('https://'))

    def test_calendar_covers_the_year(self):
        from core import dop_content
        self.assertEqual(len(dop_content.SEASON_CALENDAR), 12)


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


class Wave1LogicTests(SimpleTestCase):
    def test_marketing_url_adds_chat_text_only_for_messengers(self):
        from core.templatetags.marketing_tags import marketing_url
        url = marketing_url('https://wa.me/79650000000', 'contacts_page', 'Хочу забронировать')
        self.assertIn('text=%D0%A5', url)
        self.assertIn('utm_content=contacts_page', url)
        self.assertNotIn('text=', marketing_url('https://vk.ru/club', 'contacts_page', 'Привет'))

    def test_route_facts_skip_seed_marks(self):
        from core.models import DirectionsPage
        page = DirectionsPage(car_distance='100 км от Москвы', car_time='уточняется', train_price='от 400 ₽')
        self.assertEqual(page.route_facts(), [('100 км', 'от Москвы'), ('от 400 ₽', 'электричка с Курского вокзала')])


class Wave1PagesTests(TestCase):
    def test_faq_topics_follow_used_topics(self):
        from core.models import FaqItem, FaqPage
        FaqItem.objects.all().delete()
        FaqItem.objects.create(question='Можно ли с животными?', answer='<p>Да</p>', topic='pets')
        context = FaqPage(title='FAQ').get_context(RequestFactory().get('/'))
        self.assertEqual(context['topics'], [('pets', 'Животные')])


class DopPagesTests(TestCase):
    def test_telegram_preview_parser(self):
        from core.management.commands.fetch_telegram_preview import channel_name, parse
        page = ('<div class="tgme_widget_message_wrap"><div data-post="best_season_bs/127">'
                '<a class="tgme_widget_message_photo_wrap" style="width:1px;background-image:url(\'https://cdn.example/p.jpg\')"></a>'
                '<div class="tgme_widget_message_text js-message_text">Мальдивы — ближе,<br/>чем кажется</div>'
                '<time datetime="2026-06-21T10:00:00+00:00"></time></div>'
                '<div class="tgme_widget_message_wrap"><div data-post="best_season_bs/1"><time datetime="2024-09-15T10:00:00+00:00"></time></div>')
        posts = parse(page)
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0]['url'], 'https://t.me/best_season_bs/127')
        self.assertEqual(posts[0]['text'], 'Мальдивы — ближе,\nчем кажется')
        self.assertEqual(posts[0]['image_url'], 'https://cdn.example/p.jpg')
        self.assertEqual(channel_name('https://t.me/best_season_bs?utm_source=x'), 'best_season_bs')
        self.assertEqual(channel_name('https://vk.ru/club'), '')

    def test_group_form_keeps_occasion(self):
        from forms.forms import GroupForm
        form = GroupForm(data={'name': 'Аня', 'phone': '+7 999 000-00-00', 'topic': 'Выпускной',
                               'guests': 12, 'consent_given': True})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.save().topic, 'Выпускной')

    def test_scenarios_have_steps_and_labels(self):
        from core.dop_pages import SCENARIOS
        self.assertEqual([s['code'] for s in SCENARIOS], ['couple', 'kids', 'dog', 'company', 'work'])
        self.assertTrue(all(len(s['steps']) >= 3 for s in SCENARIOS))


class ServicePagesTests(TestCase):
    def test_server_error_page_renders_without_request_context(self):
        from core.views import server_error
        response = server_error(RequestFactory().get('/'))
        self.assertEqual(response.status_code, 500)
        self.assertIn('error-code', response.content.decode())

    def test_search_offers_faq_answers(self):
        from core.models import FaqItem
        from search.views import faq_matches
        item = FaqItem.objects.create(question='Во сколько заезд?', answer='<p>С 14:00</p>')
        self.assertIn(item, faq_matches('заезд'))
        self.assertEqual(faq_matches('да'), [])


class EventsAndSnippetsTests(TestCase):
    def test_interface_texts_stay_editable_snippets(self):
        from wagtail.snippets.models import get_snippet_models
        from core.models import ChannelPost, Event, InterfaceText
        models = get_snippet_models()
        self.assertIn(InterfaceText, models)
        self.assertIn(Event, models)
        self.assertNotIn(ChannelPost, models)

    def test_events_split_by_last_day(self):
        import datetime
        from django.utils import timezone
        from core.dop_pages import context_for
        from core.models import ContentPage, Event
        today = timezone.localdate()
        Event.objects.create(title='Йога', date=today - datetime.timedelta(days=2), end_date=today)
        Event.objects.create(title='Новый год', date=today + datetime.timedelta(days=30))
        Event.objects.create(title='Флористика', date=today - datetime.timedelta(days=5))
        context = context_for(ContentPage(title='М', slug='meropriyatiya'), RequestFactory().get('/'))
        self.assertEqual([e.title for e in context['upcoming']], ['Йога', 'Новый год'])
        self.assertEqual(context['archive'][0]['title'], 'Флористика')


MEDIA_TMP_VIDEO = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=MEDIA_TMP_VIDEO)
class VideoClipTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA_TMP_VIDEO, ignore_errors=True)

    def test_slot_turns_into_video_when_clip_uploaded(self):
        from django.core.files.base import ContentFile
        from wagtail.documents import get_document_model
        from core.models import VideoClip
        render = lambda: render_to_string('includes/video_slot.html', {'slot': 'territory-walk', 'poster': None, 'title': 'Прогулка'},
                                          request=RequestFactory().get('/'))
        self.assertIn('video-slot--empty', render())
        document = get_document_model().objects.create(title='walk', file=ContentFile(b'00', name='walk.mp4'))
        VideoClip.objects.create(slot='territory-walk', file=document)
        html = render()
        self.assertIn('<video', html)
        self.assertIn('preload="none"', html)


class PageStoryTests(SimpleTestCase):
    def test_every_story_has_text_and_known_source(self):
        from core.dop_content import SRC
        from core.dop_stories import STORIES
        self.assertGreaterEqual(len(STORIES), 14)
        for key, stories in STORIES.items():
            for story in stories:
                self.assertTrue(story['title'] and story['lead'] and story['paras'], key)
                if story.get('source'):
                    self.assertIn(story['source'], SRC, key)

    def test_tag_renders_story(self):
        html = render_to_string('includes/page_story.html', {'stories': [{
            'kicker': 'К', 'title': 'Заголовок', 'lead': 'Лид', 'paras': ['Абзац'], 'facts': [('3 км', 'до Поленово')],
        }]})
        self.assertIn('story__lead', html)
        self.assertIn('3 км', html)
