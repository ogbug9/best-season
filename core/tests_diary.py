"""«Дневник Сезона» (20.10, Н2): индекс, запись, sitemap, перенос со временных страниц, права редактора."""
import datetime
import json
import re
from io import StringIO

from django.contrib.auth.models import Group, User
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from wagtail.models import Page

from core.diary_seed import ensure_diary
from core.models import ContentPage, DiaryEntryPage, DiaryIndexPage


class DiaryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_pages", "--create-only", stdout=StringIO(), stderr=StringIO())
        cls.index = DiaryIndexPage.objects.get()

    def add_entry(self, slug, date, title="Запись"):
        page = DiaryEntryPage(title=title, slug=slug, date=date, lead="Лид записи для проверки.")
        self.index.add_child(instance=page)
        page.save_revision().publish()
        return page

    def test_seed_keeps_addresses_and_three_entries(self):
        self.assertEqual(self.index.url, "/o-nas/dnevnik/")
        self.assertEqual([p.url for p in self.index.entries()],
                         ["/o-nas/dnevnik/novyj-god/", "/o-nas/dnevnik/ayka/", "/o-nas/dnevnik/zheltoe-chudo/"])
        out = StringIO()
        call_command("seed_pages", "--create-only", stdout=out, stderr=StringIO())
        self.assertIn("создано 0", out.getvalue())

    def test_index_renders_cards_newest_first(self):
        self.add_entry("svezhee", datetime.date.today() + datetime.timedelta(days=1), "Самая свежая")
        html = self.client.get(self.index.url).content.decode()
        self.assertEqual(html.count("<h1"), 1)
        self.assertEqual(html.count('class="diary-card"'), 4)
        self.assertLess(html.index("Самая свежая"), html.index("бронирование"))
        self.assertNotIn("diary-pages", html)  # одна страница — без пагинации

    def test_pagination_and_all(self):
        for n in range(8):
            self.add_entry(f"old-{n}", datetime.date(2020, 1, n + 1))
        first = self.client.get(self.index.url).content.decode()
        self.assertEqual(first.count('class="diary-card"'), 9)
        self.assertIn('aria-current="page">1<', first)
        self.assertIn('href="?page=2"', first)
        second = self.client.get(self.index.url + "?page=2").content.decode()
        self.assertEqual(second.count('class="diary-card"'), 2)
        everything = self.client.get(self.index.url + "?page=all").content.decode()
        self.assertEqual(everything.count('class="diary-card"'), 11)

    def test_entry_page_seo_and_breadcrumbs(self):
        page = DiaryEntryPage.objects.get(slug="ayka")
        page.seo_title, page.search_description = "Айка в Амбаре", "Уникальное описание записи про Айку для поисковиков."
        page.save_revision().publish()
        html = self.client.get(page.url).content.decode()
        self.assertIn("<title>Айка в Амбаре", html)
        self.assertIn('content="Уникальное описание записи про Айку для поисковиков."', html)
        self.assertIn('property="og:type" content="article"', html)
        types = [json.loads(s)["@type"] for s in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html)]
        self.assertIn("Article", types)
        self.assertIn("BreadcrumbList", types)
        self.assertIn('aria-label="Хлебные крошки"', html)
        self.assertIn(f'href="{self.index.url}"', html)
        self.assertEqual(html.count("<h1"), 1)

    def test_body_is_limited_to_allowed_blocks(self):
        from core.content_blocks import DIARY_BLOCKS

        self.assertEqual([name for name, _ in DIARY_BLOCKS], ["paragraph", "heading", "image", "quote"])
        paragraph = dict(DIARY_BLOCKS)["paragraph"]
        self.assertEqual(paragraph.features, ["bold", "italic", "link", "ul", "ol"])

    def test_sitemap_lists_diary(self):
        xml = self.client.get("/sitemap.xml").content.decode()
        for slug in ("dnevnik/", "dnevnik/novyj-god/", "dnevnik/ayka/", "dnevnik/zheltoe-chudo/"):
            self.assertIn(f"/o-nas/{slug}</loc>", xml)

    def test_conversion_from_temporary_pages(self):
        about = self.index.get_parent()
        self.index.delete()
        old = ContentPage(title="Дневник Сезона", slug="dnevnik", intro="x", in_progress=True)
        about.add_child(instance=old)
        child = ContentPage(title="Новый год", slug="novyj-god", search_description="Описание из админки")
        old.add_child(instance=child)
        self.assertEqual(ensure_diary(log=lambda *_: None), 4)
        index = DiaryIndexPage.objects.get()
        self.assertEqual(index.url, "/o-nas/dnevnik/")
        self.assertFalse(ContentPage.objects.filter(slug__in=["dnevnik", "novyj-god"]).exists())
        self.assertEqual(DiaryEntryPage.objects.get(slug="novyj-god").search_description, "Описание из админки")
        self.assertEqual(ensure_diary(log=lambda *_: None), 0)


class DiaryEditorTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_pages", "--create-only", stdout=StringIO(), stderr=StringIO())
        call_command("setup_roles", stdout=StringIO())
        cls.editor = User.objects.create_user("editor", password="x")
        cls.editor.groups.add(Group.objects.get(name="Редактор"))

    def setUp(self):
        self.client.force_login(self.editor)
        self.index = DiaryIndexPage.objects.get()

    def test_editor_creates_and_edits_entry(self):
        url = reverse("wagtailadmin_pages:add", args=("core", "diaryentrypage", self.index.pk))
        self.assertEqual(self.client.get(url).status_code, 200)
        entry = DiaryEntryPage.objects.get(slug="ayka")
        self.assertEqual(self.client.get(reverse("wagtailadmin_pages:edit", args=(entry.pk,))).status_code, 200)

    def test_editor_cannot_delete_entry(self):
        entry = DiaryEntryPage.objects.get(slug="ayka")
        self.client.post(reverse("wagtailadmin_pages:delete", args=(entry.pk,)))
        self.assertTrue(Page.objects.filter(pk=entry.pk).exists())
