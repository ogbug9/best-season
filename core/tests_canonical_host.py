from django.test import SimpleTestCase, override_settings

HOSTS = ["best-season.online", "www.best-season.online", "best-season-sfnvsd24.amvera.io"]


@override_settings(ALLOWED_HOSTS=HOSTS)
class CanonicalHostTests(SimpleTestCase):
    @override_settings(CANONICAL_HOST="")
    def test_without_setting_nothing_redirects(self):
        response = self.client.get("/robots.txt", HTTP_HOST="best-season-sfnvsd24.amvera.io")
        self.assertEqual(response.status_code, 200)

    @override_settings(CANONICAL_HOST="best-season.online")
    def test_demo_and_www_redirect_once_to_https_canonical(self):
        for host in ("www.best-season.online", "best-season-sfnvsd24.amvera.io"):
            response = self.client.get("/razmeshchenie/?utm_source=x", HTTP_HOST=host)
            self.assertEqual(response.status_code, 301)
            self.assertEqual(response["Location"], "https://best-season.online/razmeshchenie/?utm_source=x")

    @override_settings(CANONICAL_HOST="best-season.online")
    def test_canonical_host_is_served(self):
        response = self.client.get("/robots.txt", HTTP_HOST="best-season.online")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Sitemap: http://best-season.online/sitemap.xml", response.content.decode())
