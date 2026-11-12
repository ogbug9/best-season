from importlib import import_module

from django.apps import apps
from django.test import TestCase

from services.models import Service, ServicesPage
from wagtail.models import Site


class ServiceCatalogTests(TestCase):
    def test_small_gazebo_seed_preserves_editor_data_and_has_no_invented_rate(self):
        service = Service.objects.get(slug='malaya-besedka')
        self.assertIsNone(service.price)
        self.assertIsNone(service.image_id)
        service.short_description = 'Редакторский текст'
        service.save()
        import_module('services.migrations.0010_small_gazebo_card').add_card(apps, None)
        service.refresh_from_db()
        self.assertEqual(service.short_description, 'Редакторский текст')
        root = Site.objects.get(is_default_site=True).root_page
        page = root.add_child(instance=ServicesPage(title='Услуги', slug='services-test'))
        page.save_revision().publish()
        response = self.client.get(page.url)
        self.assertContains(response, 'id="service-malaya-besedka"')
        self.assertContains(response, 'Цена по запросу')
        self.assertContains(response, 'Добавить к отдыху')
        self.assertNotContains(response, 'Баня и беседка выбираются в окне брони')
