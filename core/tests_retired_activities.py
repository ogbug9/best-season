from unittest.mock import patch
from types import SimpleNamespace

from django.http import Http404
from django.test import RequestFactory, SimpleTestCase

from core.management.commands.seed_pages import TREE, walk
from core.models import ContentPage
from core.views import old_activities_redirect


class RetiredActivitiesTests(SimpleTestCase):
    def test_seed_does_not_recreate_page(self):
        self.assertNotIn("razvlecheniya", [node[1] for node in walk(TREE)])

    def test_old_page_excluded_from_sitemap(self):
        self.assertEqual(ContentPage.get_sitemap_urls(SimpleNamespace(slug="razvlecheniya")), [])

    @patch("wagtail.models.Page.objects")
    def test_redirect_preserves_query(self, pages):
        pages.live.return_value.filter.return_value.first.return_value.get_url.return_value = "/territoriya/chem-zanyatsya/"
        request = RequestFactory().get("/territoriya/razvlecheniya/?utm_source=test")
        response = old_activities_redirect(request)
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response.url, "/territoriya/chem-zanyatsya/?utm_source=test")

    @patch("wagtail.models.Page.objects")
    def test_missing_target_does_not_redirect_to_a_broken_link(self, pages):
        pages.live.return_value.filter.return_value.first.return_value = None
        with self.assertRaises(Http404):
            old_activities_redirect(RequestFactory().get("/razvlecheniya/"))
