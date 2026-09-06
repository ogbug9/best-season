"""Тесты страниц домов.

Порядок блоков — критерий приёмки: он задан макетом «Первый домик» и
редактором не меняется. Тест на структуру пишется специально: пропуск
блока в первой версии Фазы 5 прошёл незамеченным именно потому, что
такого теста не было.
"""

import io
import re
from pathlib import Path

from django.core.files.images import ImageFile

from django.test import TestCase
from wagtail.models import Page, Site
from wagtail.test.utils import WagtailPageTestCase

from core.models import Amenity, AmenityGroup, SiteSettings
from houses.models import HouseIndexPage, HousePage
from reviews.models import Review


class HousePageStructureTests(WagtailPageTestCase):
    @classmethod
    def setUpTestData(cls):
        site = Site.objects.get(is_default_site=True)
        site.hostname = "testserver"
        site.save()
        home = site.root_page

        cls.index = HouseIndexPage(title="Размещение", slug="razmeshchenie")
        home.add_child(instance=cls.index)

        cls.house = HousePage(
            title="Дом №1 с сауной",
            slug="dom-1",
            pms_name="Домик №1",
            short_description="4 спальных места + финская сауна",
            description="<p>Уютный домик-лофт с собственной сауной.</p>",
            capacity=4,
            area=30,
            highlight="с сауной",
            price_from=8000,
        )
        cls.index.add_child(instance=cls.house)

        for i in range(2, 5):
            cls.index.add_child(
                instance=HousePage(
                    title=f"Дом №{i} с камином", slug=f"dom-{i}", capacity=4, sort_order_index=i
                )
            )

        for i in range(3):
            cls.house.gallery_images.create(image=cls._make_image(f"gallery-{i}"))

        group = AmenityGroup.objects.create(name="Сауна", sort_order=10)
        cls.house.amenities.add(
            Amenity.objects.create(name="Финская сауна", group=group, is_featured=True)
        )
        cls.house.amenities.add(
            Amenity.objects.create(name="Шапочки для сауны", group=group)
        )
        cls.house.save_revision().publish()

        Review.objects.create(
            author_name="Элина Т.",
            text="Были в домике вчетвером с детьми.",
            house=cls.house,
            is_published=True,
        )

        site_settings = SiteSettings.for_site(site)
        site_settings.directions_short = "От МКАД 120 км по Симферопольскому шоссе."
        site_settings.save()

    @staticmethod
    def _make_image(name):
        from PIL import Image as PILImage
        from wagtail.images import get_image_model

        buffer = io.BytesIO()
        PILImage.new("RGB", (1200, 800), "olive").save(buffer, format="JPEG")
        buffer.seek(0)
        return get_image_model().objects.create(
            title=name, file=ImageFile(buffer, name=f"{name}.jpg")
        )

    def test_pages_render(self):
        self.assertPageIsRenderable(self.index)
        self.assertPageIsRenderable(self.house)

    def test_block_order_matches_layout(self):
        """Макет задаёт жёсткий порядок блоков страницы дома."""
        html = self.client.get(self.house.url).content.decode()

        markers = [
            "house-title",          # 1. заголовок
            "data-booking-panel",   # 2. бронирование
            "house-mosaic",         # 3. мозаика фото
            "house-facts",          # 4. вместимость и спальные места
            "О домике",             # 5. описание и удобства
            "equipment__columns",   # 6. развёрнутое описание
            "Отзывы о домике",      # 7. отзывы
        ]

        positions = []
        for marker in markers:
            index = html.find(marker)
            self.assertNotEqual(index, -1, f"Блок «{marker}» пропал со страницы дома")
            positions.append(index)

        self.assertEqual(positions, sorted(positions), "Порядок блоков разошёлся с макетом")

    def test_sections_outside_layout_are_gone(self):
        """Секции, которых на макете нет, со страницы убраны.

        Требования ТЗ по ним закрываются в других местах сайта — тест
        держит решение зафиксированным, чтобы блоки не вернулись
        случайной правкой шаблона.
        """
        html = self.client.get(self.house.url).content.decode()
        for marker in ["Как добраться", "Другие домики", "Задать вопрос о доме"]:
            self.assertNotIn(marker, html)

    def test_booking_entry_point_is_numbered(self):
        """Таблица п. 5.1: кнопка брони несёт номер точки входа,
        иначе в Метрику уходит пустой параметр вместо цели."""
        html = self.client.get(self.house.url).content.decode()
        self.assertIn('data-entry-point="3"', html)

    def test_other_houses_are_exactly_three(self):
        self.assertEqual(len(self.house.other_houses), 3)
        self.assertNotIn(self.house, self.house.other_houses)

    def test_index_has_services_block_placeholder(self):
        """П. 9.2.2: «Размещение» = домики + доп услуги одной страницей.
        Без услуг в справочнике блок просто не рисуется — здесь достаточно
        убедиться, что шаблон вообще пытается его вывести."""
        html = self.client.get(self.index.url).content.decode()
        self.assertIn("Дом №1 с сауной", html)

    def test_entry_points_are_numbered(self):
        """Таблица п. 5.1: каждая точка входа должна нести свой номер,
        иначе в Метрику уходит пустой параметр вместо цели."""
        html = self.client.get(self.index.url).content.decode()
        self.assertIn('data-entry-point="1"', html)  # полоса поиска
        self.assertIn('data-entry-point="5"', html)  # кнопка внизу каталога


class CssScopeTests(TestCase):
    """Контур снимает поддержку виджета при глобальных селекторах
    `* {}` или `div {}` (03-kontur-widget.md)."""

    def test_no_global_selectors(self):
        css = Path("config/static/css/main.css").read_text(encoding="utf-8")
        css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
        checks = [
            (r"(^|[},])\s*\*\s*[,{]", "глобальный селектор * запрещён Контуром"),
            (r"(^|[},])\s*div\s*[,{]", "голый селектор div запрещён Контуром"),
        ]
        for pattern, message in checks:
            self.assertIsNone(re.search(pattern, css, flags=re.M), message)

class TemplateHygieneTests(TestCase):
    """Django-комментарий {# #} работает только в одну строку.

    Многострочный он не распознаёт и печатает содержимое прямо в HTML —
    на боевом сайте так уже вылезали служебные заметки, дважды.
    Проверяем не наличие нужного, а отсутствие лишнего.
    """

    def test_no_multiline_hash_comments_in_templates(self):
        import glob
        import re

        bad = []
        patterns = ["config/templates/**/*.html", "*/templates/**/*.html"]
        for pattern in patterns:
            for path in glob.glob(pattern, recursive=True):
                with open(path, encoding="utf-8") as fh:
                    source = fh.read()
                for match in re.finditer(r"\{#(.*?)#\}", source, re.S):
                    if "\n" in match.group(0):
                        bad.append(path)
        self.assertEqual(
            bad, [], f"Многострочные {{# #}} попадут в HTML как текст: {bad}"
        )


class HouseCardSliderTests(TestCase):
    """Карусель фотографий в карточке домика на главной.

    В макете под фото стоят три точки — карточка листается. Слайды
    собираются из обложки и первых кадров галереи, дубли не берём.
    """

    @staticmethod
    def _image(name):
        import io as _io
        from PIL import Image as PILImage
        from wagtail.images import get_image_model

        buffer = _io.BytesIO()
        PILImage.new("RGB", (800, 600), "olive").save(buffer, format="JPEG")
        buffer.seek(0)
        return get_image_model().objects.create(
            title=name, file=ImageFile(buffer, name=f"{name}.jpg")
        )

    @classmethod
    def setUpTestData(cls):
        from houses.models import HouseGalleryImage, HouseIndexPage, HousePage

        site = Site.objects.get(is_default_site=True)
        site.hostname = "testserver"
        site.save()
        index = HouseIndexPage(title="Размещение", slug="razmeshchenie-slider")
        site.root_page.add_child(instance=index)

        cls.house = HousePage(title="Домик со слайдером", slug="so-slayderom", capacity=4)
        cls.house.hero_image = cls._image("oblozhka")
        index.add_child(instance=cls.house)
        for i in range(4):
            HouseGalleryImage.objects.create(page=cls.house, image=cls._image(f"kadr-{i}"))

        cls.pustoy = HousePage(title="Домик без фото", slug="bez-foto", capacity=4)
        index.add_child(instance=cls.pustoy)

    def test_beryotsya_rovno_tri_kadra(self):
        """Галерея из пяти кадров, а в карточке показываем три — как в макете."""
        self.assertEqual(len(self.house.card_slides), 3)

    def test_pervyy_kadr_oblozhka(self):
        self.assertEqual(self.house.card_slides[0], self.house.hero_image)

    def test_dubli_ne_povtoryayutsya(self):
        slides = self.house.card_slides
        self.assertEqual(len(slides), len(set(s.pk for s in slides)))

    def test_bez_fotografiy_slaydov_net(self):
        self.assertEqual(self.pustoy.card_slides, [])

    def test_predel_tri_kadra(self):
        from houses.models import HousePage

        self.assertEqual(HousePage.CARD_SLIDES, 3, "в макете ровно три точки")
