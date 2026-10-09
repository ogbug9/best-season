"""Временные страницы 09.10.2026: seed_pages их заводит, они открываются и не попадают в меню."""
from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from wagtail.models import Page

from core.models import ContentPage
from core.temp_pages import SLUGS, TREE


class TempPagesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_pages", "--create-only", stdout=StringIO(), stderr=StringIO())

    def test_pages_are_created_hidden_and_in_progress(self):
        for parent_slug, slug, _, _ in TREE:
            page = ContentPage.objects.get(slug=slug)
            self.assertEqual(page.get_parent().slug, parent_slug)
            self.assertFalse(page.show_in_menus, slug)
            self.assertTrue(page.in_progress, slug)

    def test_pages_render(self):
        for slug in SLUGS:
            page = Page.objects.get(slug=slug)
            response = self.client.get(page.url)
            self.assertEqual(response.status_code, 200, slug)
            html = response.content.decode()
            self.assertIn("dev-strip", html, slug)
            self.assertIn("temp-pages.css", html, slug)

    def test_pet_and_service_specifics(self):
        snezhka = self.client.get(Page.objects.get(slug="snezhka").url).content.decode()
        self.assertIn("Погладить Снежку", snezhka)
        self.assertIn("Дымок", snezhka)  # «Ещё ищут дом»
        besedka = self.client.get(Page.objects.get(slug="bolshaya-besedka").url).content.decode()
        self.assertIn('data-capacity="50"', besedka)
        photo = self.client.get(Page.objects.get(slug="fotosessii").url).content.decode()
        self.assertIn('data-lat="54.736"', photo)

    def test_rerun_creates_nothing(self):
        out = StringIO()
        call_command("seed_pages", "--create-only", stdout=out, stderr=StringIO())
        self.assertIn("создано 0", out.getvalue())

    def test_about_and_service_cards_link_to_new_pages(self):
        from core.temp_pages import link_about
        from services.models import Service

        context = {"about_pets": [{"name": "Снежка", "crop": "pet-snezhka"}],
                   "about_diary": [{"crop": "diary-ayka", "url": ""}, {"crop": "diary-car", "url": "https://t.me/x"}]}
        link_about(context)
        self.assertEqual(context["about_pets"][0]["page_url"], Page.objects.get(slug="snezhka").url)
        self.assertEqual(context["about_diary"][0]["page_url"], Page.objects.get(slug="ayka").url)
        self.assertEqual(context["about_diary"][1]["page_url"], "")  # ссылка из CMS важнее
        self.assertEqual(context["about_pets_url"], Page.objects.get(slug="pushistiki").url)
        self.assertEqual(Service(slug="russkaya-banya").page_url, Page.objects.get(slug="banya").url)
        self.assertEqual(Service(slug="arenda-sapov").page_url, "")
