from django.test import SimpleTestCase

from core.territory_content import activity_tags


class TerritoryFilterTests(SimpleTestCase):
    def test_legacy_water_group_is_not_automatically_an_event(self):
        self.assertIn("active", activity_tags('Река «Скнижка»', "water").split())
        self.assertNotIn("events", activity_tags('Река «Скнижка»', "water").split())
        self.assertIn("events", activity_tags("Мастер-классы", "water").split())
        self.assertIn("events", activity_tags("Кинопоказы", "").split())
