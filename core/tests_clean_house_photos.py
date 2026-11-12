import shutil
import tempfile
from hashlib import sha256
from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase, override_settings
from wagtail.images import get_image_model
from wagtail.images.tests.utils import get_test_image_file
from wagtail.models import Page

from houses.models import HousePage, HouseGalleryImage


class CleanHousePhotosTests(TestCase):
    def setUp(self):
        directory = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, directory)
        override = override_settings(MEDIA_ROOT=directory)
        override.enable()
        self.addCleanup(override.disable)
        self.page = Page.objects.get(depth=1).add_child(instance=HousePage(title='Test', slug='domik-test'))
        self.page.save_revision().publish()
        self.image = get_image_model().objects.create(title='Imported test', file=get_test_image_file())
        self.row = HouseGalleryImage.objects.create(page=self.page, image=self.image, sort_order=0)
        with self.image.file.open('rb') as source:
            digest = sha256(source.read()).hexdigest()
        self.record = dict(house=self.page.slug, old_title=self.image.title, old_sha256=digest,
                           source='original.jpg', file='domik-1-figma-62.webp')

    def apply(self):
        with patch('core.management.commands.apply_clean_house_photos.load_records', return_value=[self.record]):
            call_command('apply_clean_house_photos', stdout=StringIO())
        self.row.refresh_from_db()

    def test_relink_is_idempotent_and_preserves_original(self):
        old_path = self.image.file.path
        self.apply()
        clean_id = self.row.image_id
        self.assertNotEqual(clean_id, self.image.pk)
        self.apply()
        self.assertEqual(self.row.image_id, clean_id)
        self.assertTrue(get_image_model().objects.filter(pk=self.image.pk).exists())
        with open(old_path, 'rb') as source:
            self.assertEqual(sha256(source.read()).hexdigest(), self.record['old_sha256'])

    def test_editor_file_change_is_preserved(self):
        self.record['old_sha256'] = 'not-the-original-checksum'
        self.apply()
        self.assertEqual(self.row.image_id, self.image.pk)

    def test_unpublished_page_is_preserved(self):
        self.page.title = 'Editor draft'
        self.page.save_revision()
        self.apply()
        self.assertEqual(self.row.image_id, self.image.pk)
