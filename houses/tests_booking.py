"""Расчёт стоимости и календарь блока бронирования.

Считаем на сервере, поэтому проверяем именно серверный результат:
подставленное в браузере на сумму влиять не должно.
"""

from datetime import date, timedelta

from django.test import TestCase
from wagtail.models import Site

from houses.booking import calendar_months, guests_label, nights_label, quote
from houses.models import HouseIndexPage, HousePage


class QuoteTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        site = Site.objects.get(is_default_site=True)
        site.hostname = "testserver"
        site.save()
        index = HouseIndexPage(title="Размещение", slug="razmeshchenie")
        site.root_page.add_child(instance=index)

        cls.house = HousePage(
            title="Первый домик",
            slug="domik-1",
            capacity=4,
            price_from=8000,
            price_per_night=8000,
            pet_fee=1000,
            max_adults=4,
            max_children=4,
            max_pets=2,
        )
        index.add_child(instance=cls.house)
        cls.house.save_revision().publish()

        cls.start = date.today() + timedelta(days=7)

    def _quote(self, nights=2, **kwargs):
        return quote(
            self.house,
            date_from=self.start,
            date_to=self.start + timedelta(days=nights),
            **kwargs,
        )

    def test_total_is_price_times_nights(self):
        result = self._quote(nights=2)
        self.assertEqual(result["nights"], 2)
        self.assertEqual(result["total"], 16000)
        self.assertEqual(result["error"], "")

    def test_pet_fee_is_added_per_pet(self):
        self.assertEqual(self._quote(pets=1)["total"], 17000)
        self.assertEqual(self._quote(pets=2)["total"], 18000)

    def test_season_rule_overrides_base_price(self):
        """Сезонная цена перекрывает базовую только в свои даты."""
        self.house.price_rules.create(
            date_from=self.start,
            date_to=self.start,
            price_per_night=12000,
            sort_order=1,
        )
        self.house.save()
        # Первая ночь по сезонной цене, вторая по базовой
        self.assertEqual(self._quote(nights=2)["total"], 20000)

    def test_no_dates_means_no_total(self):
        """До выбора дат суммы нет — показывается цена «от»."""
        result = quote(self.house)
        self.assertIsNone(result["total"])
        self.assertEqual(result["price_from"], 8000)

    def test_checkout_must_be_after_checkin(self):
        result = quote(self.house, date_from=self.start, date_to=self.start)
        self.assertTrue(result["error"])
        self.assertIsNone(result["total"])

    def test_past_dates_are_rejected(self):
        past = date.today() - timedelta(days=3)
        result = quote(self.house, date_from=past, date_to=past + timedelta(days=1))
        self.assertTrue(result["error"])

    def test_guests_are_capped_by_capacity(self):
        result = self._quote(adults=4, children=4)
        self.assertTrue(result["error"])

    def test_counters_are_clamped_to_house_limits(self):
        """Гость может подставить что угодно — сервер приводит к пределам."""
        result = self._quote(adults=99, children=-5, pets="ой")
        self.assertEqual(result["adults"], self.house.max_adults)
        self.assertEqual(result["children"], 0)
        self.assertEqual(result["pets"], 0)


class LabelTests(TestCase):
    def test_russian_endings(self):
        self.assertEqual(nights_label(1), "1 ночь")
        self.assertEqual(nights_label(2), "2 ночи")
        self.assertEqual(nights_label(5), "5 ночей")
        self.assertEqual(nights_label(11), "11 ночей")
        self.assertEqual(nights_label(21), "21 ночь")
        self.assertEqual(guests_label(3), "3 гостя")


class CalendarTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        site = Site.objects.get(is_default_site=True)
        site.hostname = "testserver"
        site.save()
        index = HouseIndexPage(title="Размещение", slug="razmeshchenie")
        site.root_page.add_child(instance=index)
        cls.house = HousePage(
            title="Первый домик", slug="domik-1", capacity=4, price_from=8000
        )
        index.add_child(instance=cls.house)
        cls.house.save_revision().publish()

    def test_two_months_and_no_past_scroll(self):
        data = calendar_months(self.house)
        self.assertEqual(len(data["months"]), 2)
        # Назад в прошлое не листаем: стрелка отключена
        self.assertEqual(data["prev"], "")

    def test_selected_range_is_marked(self):
        start = date.today() + timedelta(days=2)
        data = calendar_months(
            self.house,
            selection={"date_from": start, "date_to": start + timedelta(days=3)},
        )
        cells = [cell for month in data["months"] for week in month["weeks"] for cell in week]
        self.assertTrue(any(cell["range_start"] for cell in cells))
        self.assertTrue(any(cell["range_end"] for cell in cells))
        self.assertTrue(any(cell["in_range"] for cell in cells))

    def test_calendar_endpoint_returns_markup(self):
        response = self.client.get(f"/api/domik/{self.house.slug}/kalendar/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("calendar__grid", response.content.decode())

    def test_price_endpoint_returns_labels(self):
        start = date.today() + timedelta(days=5)
        response = self.client.get(
            f"/api/domik/{self.house.slug}/raschet/",
            {"date_from": start.isoformat(), "date_to": (start + timedelta(days=2)).isoformat()},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["nights"], 2)
        self.assertEqual(data["nights_label"], "2 ночи")

    def test_unknown_house_is_404(self):
        self.assertEqual(self.client.get("/api/domik/net-takogo/raschet/").status_code, 404)
