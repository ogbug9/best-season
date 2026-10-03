import io
import json
import re
import sqlite3
import tarfile
import tempfile
from contextlib import closing
from hashlib import sha256
from pathlib import Path
from unittest.mock import patch

from django.conf import settings
from django.core.files.images import ImageFile
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, SimpleTestCase, override_settings
from wagtail.images import get_image_model
from wagtail.models import Site

from core.models import ContentPage, InterfaceText, SiteSettings


class ContentSafetyTests(TestCase):
    def test_mobile_home_photos_seed_once_and_preserve_editor_clear(self):
        from home.models import HomePage
        home = Site.objects.first().root_page.add_child(instance=HomePage(title='Главная', slug='mobile-home'))
        draft = home.save_revision()
        call_command('initialize_site_content', stdout=io.StringIO())
        home.refresh_from_db(); draft.refresh_from_db()
        self.assertTrue(home.about_mobile_image)
        self.assertTrue(home.quote_mobile_image)
        self.assertEqual(draft.content['about_mobile_image'], home.about_mobile_image_id)
        home.about_mobile_image = None; home.save(update_fields=['about_mobile_image'])
        call_command('initialize_site_content', stdout=io.StringIO())
        home.refresh_from_db()
        self.assertIsNone(home.about_mobile_image)

    def test_editor_upload_prepares_after_commit_including_mobile(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as media, override_settings(MEDIA_ROOT=media):
            content = io.BytesIO()
            Image.new('RGB', (90, 60), 'olive').save(content, format='JPEG')
            content.seek(0)
            with patch('core.management.commands.prepare_site_images.prepare', return_value=0) as prepare:
                with self.captureOnCommitCallbacks(execute=True):
                    image = get_image_model().objects.create(title='Upload', file=ImageFile(content, name='upload.jpg'))
                plan = prepare.call_args[0][0]
                self.assertIn((image.pk, 'width-360|format-webp'), plan)
                self.assertIn((image.pk, 'fill-640x1387|format-webp|webpquality-82'), plan)

    def test_initialization_keeps_editor_content_drafts_and_consent_version(self):
        site = Site.objects.first()
        page = site.root_page.add_child(instance=ContentPage(title='Оферта', slug='oferta', body='<p>Редакторский текст</p>', show_booking_cta=False))
        page.save_revision().publish()
        page.body = '<p>Неопубликованный текст</p>'
        draft = page.save_revision()
        config = SiteSettings.for_site(site)
        config.consent_version = 'approved-v2'; config.save()
        call_command('initialize_site_content', stdout=io.StringIO())
        page.refresh_from_db(); draft.refresh_from_db(); config.refresh_from_db()
        self.assertEqual(page.body, '<p>Редакторский текст</p>')
        self.assertEqual(draft.content['body'], '<p>Неопубликованный текст</p>')
        self.assertEqual(config.consent_version, 'approved-v2')
        self.assertTrue(page.legal_body)
        page.legal_body = []; page.save(update_fields=['legal_body'])
        entry = InterfaceText.objects.first(); entry.text = 'Редактор'; entry.save()
        call_command('initialize_site_content', stdout=io.StringIO())
        page.refresh_from_db(); entry.refresh_from_db()
        self.assertFalse(page.legal_body)
        self.assertEqual(entry.text, 'Редактор')

    def test_all_legal_pages_render_full_text_and_merged_tables_without_viewer(self):
        from core.templatetags.legal_docs import LEGAL_PDFS
        site = Site.objects.first()
        for slug in LEGAL_PDFS:
            page = site.root_page.add_child(instance=ContentPage(title=slug, slug=slug, show_booking_cta=False))
            page.save_revision().publish()
        call_command('initialize_site_content', stdout=io.StringIO())
        for slug, pdf in LEGAL_PDFS.items():
            page = ContentPage.objects.get(slug=slug)
            response = self.client.get(page.url)
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'Скачать PDF')
            self.assertNotContains(response, '<object')
            self.assertNotContains(response, '<iframe')
            source = Path(settings.BASE_DIR)/'config/static'/pdf
            self.assertEqual(page.legal_source_sha256, sha256(source.read_bytes()).hexdigest())
        consent = self.client.get(ContentPage.objects.get(slug='soglasie-na-obrabotku').url).content.decode()
        self.assertIn('rowspan="5"', consent)
        self.assertIn('образовательных услуг', consent)

    def test_interface_text_cannot_inject_markup(self):
        from core.templatetags.content_tags import cms_text
        from django.test import RequestFactory
        InterfaceText.objects.create(key='test', label='Test', text='<style>body{display:none}</style>\nТекст')
        html = cms_text({'request': RequestFactory().get('/')}, 'test')
        self.assertNotIn('<style>', html)
        self.assertIn('&lt;style&gt;', html)
        self.assertIn('<br>', html)

    def test_breadcrumbs_and_organization_are_valid_json_and_urls_match_canonical(self):
        page = Site.objects.first().root_page.add_child(instance=ContentPage(title='Название "в кавычках"', slug='json-test'))
        page.save_revision().publish()
        html = self.client.get(page.url).content.decode()
        schemas = [json.loads(data) for data in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)]
        breadcrumb = next(s for s in schemas if s['@type'] == 'BreadcrumbList')
        self.assertEqual(breadcrumb['itemListElement'][-1]['name'], page.title)
        canonical = re.search(r'rel="canonical" href="([^"]+)"', html)[1]
        self.assertEqual(breadcrumb['itemListElement'][-1]['item'], canonical)
        self.assertIn('name="twitter:card"', html)

    def test_prepared_desktop_has_srcsets_without_processing_and_keeps_aspect(self):
        from PIL import Image
        from core.templatetags.media_tags import picture
        with tempfile.TemporaryDirectory() as media, override_settings(MEDIA_ROOT=media, GENERATE_IMAGE_RENDITIONS_ON_REQUEST=False):
            content = io.BytesIO(); Image.new('RGB', (900, 600), 'olive').save(content, format='JPEG'); content.seek(0)
            image = get_image_model().objects.create(title='Test', file=ImageFile(content, name='test.jpg'))
            for ext in ('jpeg', 'webp'):
                rendition = image.get_rendition(f'width-360|format-{ext}')
                self.assertEqual((rendition.width, rendition.height), (360, 240))
            with patch.object(image, 'get_rendition', side_effect=AssertionError('HTTP processing')):
                html = picture(image, preset='about')
            self.assertIn('type="image/webp"', html)
            self.assertIn('.jpg', html)
            self.assertIn('360w', html)
            self.assertIn('width="360" height="240"', html)


class BackupTests(SimpleTestCase):
    def test_outbound_utm_preserves_routes_and_skips_payments_and_sdk(self):
        from core.templatetags.marketing_tags import marketing_url
        from urllib.parse import parse_qs, urlsplit
        url = 'https://yandex.ru/maps/?rtext=55,37~54,36&utm_source=old'
        query = parse_qs(urlsplit(marketing_url(url, 'route')).query)
        self.assertEqual(query['rtext'], ['55,37~54,36'])
        self.assertEqual(query['utm_source'], ['best_season'])
        for url in ('https://booking.com/payment/?payment_id=test', 'https://yandex.ru/sdk/?token=test',
                    'https://hotel.kontur.ru/book/?hotelId=123', 'https://vk.com/pay?signature=test'):
            self.assertEqual(marketing_url(url), url)

    def test_seven_complete_backups_and_isolated_restore(self):
        from core.backup import create_backup, verify_backup
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp); media = folder/'media'; media.mkdir()
            (media/'photo.bin').write_bytes(b'original media')
            database = folder/'source.sqlite'
            with closing(sqlite3.connect(database)) as connection:
                connection.execute('CREATE TABLE example (id INTEGER PRIMARY KEY, value TEXT)')
                connection.execute("INSERT INTO example VALUES (1, 'content')")
                connection.commit()
            config = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': database}}
            with override_settings(MEDIA_ROOT=media, DATABASES=config):
                copies = [create_backup(folder/'backups') for _ in range(8)]
                self.assertEqual(len(list((folder/'backups').glob('bs-*'))), 7)
                verify_backup(copies[-1])
                restore = folder/'isolated'; restore.mkdir()
                # Only the test's separately created destination is used.
                import shutil
                shutil.copyfile(copies[-1]/'database.dump', restore/'restored.sqlite')
                with closing(sqlite3.connect(restore/'restored.sqlite')) as connection:
                    self.assertEqual(connection.execute('SELECT value FROM example').fetchone()[0], 'content')
                with tarfile.open(copies[-1]/'media.tar.gz') as archive:
                    self.assertEqual(archive.extractfile('photo.bin').read(), b'original media')
                (copies[-1]/'database.dump').write_bytes(b'corrupted')
                with self.assertRaises(CommandError): verify_backup(copies[-1])
                with self.assertRaises(CommandError): create_backup(folder/'other', keep=6)
