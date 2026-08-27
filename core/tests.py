"""Проверки страниц второй очереди.

Смысл не в покрытии ради покрытия: каждая проверка привязана к пункту ТЗ,
который проверяется на приёмке. Если состав страницы поедет, тест упадёт
до того, как это увидит заказчик.
"""

import glob
import re

from django.test import TestCase
from wagtail.models import Page, Site

from core.models import (
    ContactsPage,
    ContentPage,
    DirectionsPage,
    FaqItem,
    FaqPage,
    SiteSettings,
)


class TemplateHygieneTests(TestCase):
    """Django-комментарий {# #} работает только в одну строку.

    Многострочный он не распознаёт и печатает содержимое прямо в HTML —
    на боевом сайте так уже вылезали служебные заметки, дважды.
    """

    def test_no_multiline_hash_comments(self):
        bad = []
        for pattern in ["config/templates/**/*.html", "*/templates/**/*.html"]:
            for path in glob.glob(pattern, recursive=True):
                with open(path, encoding="utf-8") as fh:
                    source = fh.read()
                for match in re.finditer(r"\{#(.*?)#\}", source, re.S):
                    if "\n" in match.group(0):
                        bad.append(path)
        self.assertEqual(bad, [], f"Многострочные комментарии попадут в HTML: {bad}")


class DirectionsPageTests(TestCase):
    """П. 4.2 ТЗ: страница закрывает главный барьер аудитории и не может
    быть сокращена в первой очереди. Проверяем, что все её обязательные
    части выводятся."""

    def setUp(self):
        home = Page.objects.get(depth=2)
        self.page = DirectionsPage(
            title="Как добраться",
            slug="kak-dobratsya",
            car_distance="100 км от МКАД",
            car_time="1 час 45 минут",
            car_route="<p>По Симферопольскому шоссе.</p>",
            yandex_route_url="https://yandex.ru/maps/",
            transit_route="<p>Электричка до станции Тарусская.</p>",
            transfer_price="от 1500 ₽",
            transfer_note="<p>Заказывать за сутки.</p>",
            map_embed_url="https://yandex.ru/map-widget/v1/?ll=37",
        )
        home.add_child(instance=self.page)
        self.page.save_revision().publish()

    def test_all_required_blocks_present(self):
        body = self.client.get(self.page.url).content.decode()
        for fragment, what in [
            ("100 км от МКАД", "расстояние на авто (п. 4.2.1)"),
            ("yandex.ru/maps", "ссылка на маршрут в Яндекс.Картах (п. 4.2.1)"),
            ("Тарусская", "маршрут без автомобиля (п. 4.2.2)"),
            ("от 1500", "стоимость трансфера (п. 4.2.3)"),
            ("data-map", "карта (п. 4.2.5)"),
            ('data-entry-point="8"', "кнопка возврата к бронированию (п. 4.2.6)"),
        ]:
            self.assertIn(fragment, body, f"Не выводится: {what}")

    def test_map_is_not_loaded_upfront(self):
        """Карта подставляется только по нажатию: iframe Яндекса тянет чужие
        скрипты, портит замер скорости (п. 1.2) и отдаёт IP посетителя
        стороннему сервису до его согласия (раздел 11)."""
        body = self.client.get(self.page.url).content.decode()
        self.assertNotIn("<iframe", body)
        self.assertIn("data-map-load", body)


class FaqPageTests(TestCase):
    def setUp(self):
        home = Page.objects.get(depth=2)
        self.page = FaqPage(title="Ответы на вопросы", slug="faq")
        home.add_child(instance=self.page)
        self.page.save_revision().publish()
        FaqItem.objects.create(
            question="Как добраться?", answer="<p>На машине или электричкой.</p>"
        )
        FaqItem.objects.create(
            question="Скрытый вопрос", answer="<p>Не показывать.</p>", is_published=False
        )

    def test_only_published_questions_shown(self):
        body = self.client.get(self.page.url).content.decode()
        self.assertIn("Как добраться?", body)
        self.assertNotIn("Скрытый вопрос", body)

    def test_faq_structured_data(self):
        """Микроразметка FAQPage — п. 10.5 ТЗ."""
        body = self.client.get(self.page.url).content.decode()
        self.assertIn("FAQPage", body)
        self.assertIn('"@type": "Question"', body)

    def test_accordion_needs_no_javascript(self):
        """Аккордеон на <details>: работает с клавиатуры и не тянет вес,
        а скорость на мобильных — предмет приёмки (п. 1.2)."""
        body = self.client.get(self.page.url).content.decode()
        self.assertIn("<details", body)


class ContactsPageTests(TestCase):
    def test_contacts_come_from_site_settings(self):
        """Контакты и реквизиты берутся из настроек, а не дублируются полями
        страницы: иначе они разойдутся с подвалом, а реквизиты ИП обязаны
        совпадать (раздел 11 ТЗ)."""
        site = Site.objects.first()
        settings_obj = SiteSettings.for_site(site)
        settings_obj.phone = "+79992550837"
        settings_obj.phone_display = "+7 (999) 255-08-37"
        settings_obj.legal_name = "ИП Новосад С. П."
        settings_obj.inn = "710000000000"
        settings_obj.save()

        home = Page.objects.get(depth=2)
        page = ContactsPage(title="Контакты", slug="kontakty")
        home.add_child(instance=page)
        page.save_revision().publish()

        body = self.client.get(page.url).content.decode()
        self.assertIn("+7 (999) 255-08-37", body)
        self.assertIn("ИП Новосад С. П.", body)
        self.assertIn("710000000000", body)


class ContentPageTests(TestCase):
    def test_legal_page_can_hide_booking_cta(self):
        """На правовых страницах кнопка бронирования неуместна —
        она должна выключаться."""
        home = Page.objects.get(depth=2)
        page = ContentPage(
            title="Политика обработки персональных данных",
            slug="politika",
            body="<p>Текст.</p>",
            show_booking_cta=False,
        )
        home.add_child(instance=page)
        page.save_revision().publish()

        body = self.client.get(page.url).content.decode()
        self.assertNotIn("data-entry-point=\"7\"", body)
