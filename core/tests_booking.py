"""Проверки интеграции виджета Контур.Отеля — раздел 5 ТЗ.

Часть требований раздела проверяется только вживую, когда придёт hotelId.
Здесь закрыто то, что можно проверить кодом и что смотрят на приёмке:
отложенная загрузка, резервный сценарий, уведомление о сбое, отсутствие
персональных данных в аналитике.
"""

from pathlib import Path
from unittest.mock import patch

from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from wagtail.models import Site

from core.models import SiteSettings

JS = (Path(__file__).resolve().parent.parent / "config/static/js/kontur.js").read_text(
    encoding="utf-8"
)


class BookingModalTests(TestCase):
    """П. 5.2 ТЗ: модальное окно поверх страницы, виджет грузится по действию."""

    def setUp(self):
        cache.clear()
        self.home = Site.objects.first().root_page.url

    def test_modal_is_on_every_page(self):
        body = self.client.get(self.home).content.decode()
        self.assertIn("data-booking-modal", body)
        self.assertEqual(
            body.count("data-booking-modal"),
            1,
            "Виджет инициализируется один раз на страницу — окно должно быть одно",
        )

    def test_widget_script_is_not_loaded_upfront(self):
        """Скрипты Контура не должны влиять на замер скорости (п. 5.2, п. 1.2):
        до нажатия кнопки их на странице нет вообще."""
        body = self.client.get(self.home).content.decode()
        self.assertNotIn("bookonline24.ru", body)

    def test_modal_has_no_forbidden_global_selectors(self):
        """Контур снимает поддержку при глобальных `* {}` и `div {}`
        (см. 03-kontur-widget.md) — ресет остаётся скоупленным."""
        css = (
            Path(__file__).resolve().parent.parent / "config/static/css/main.css"
        ).read_text(encoding="utf-8")
        for line in css.splitlines():
            stripped = line.strip()
            self.assertFalse(stripped.startswith("* {"), "Глобальный сброс запрещён")
            self.assertFalse(stripped.startswith("div {"), "Голый div запрещён")


class FallbackTests(TestCase):
    """П. 5.6 ТЗ: резервный блок обязателен в первой очереди и проверяется
    принудительной блокировкой домена виджета."""

    def setUp(self):
        cache.clear()
        self.home = Site.objects.first().root_page.url

    def test_fallback_markup_does_not_depend_on_kontur(self):
        """Разметка резервного блока приходит с сервера. Если домен Контура
        заблокирован — а именно так проверяют на приёмке (п. 5.6.5), — блок
        всё равно на месте, скрипту остаётся только показать его."""
        body = self.client.get(self.home).content.decode()
        self.assertIn("data-booking-fallback", body)
        self.assertIn('action="/zayavka/fallback/"', body)

    def test_fallback_has_required_parts(self):
        """П. 5.6.2: объяснение, форма с именем, телефоном, датами и
        комментарием, кнопки Telegram и WhatsApp."""
        site = Site.objects.first()
        settings_obj = SiteSettings.for_site(site)
        settings_obj.telegram_url = "https://t.me/bestseason"
        settings_obj.whatsapp_url = "https://wa.me/79990001122"
        settings_obj.save()

        body = self.client.get(self.home).content.decode()
        for needle in ('name="name"', 'name="phone"', 'name="date_from"',
                       'name="date_to"', 'name="message"'):
            self.assertIn(needle, body, f"В резервной форме нет поля {needle}")
        self.assertIn("https://t.me/bestseason", body)
        self.assertIn("https://wa.me/79990001122", body)

    def test_timeout_is_five_seconds(self):
        """П. 5.6.1: резервный блок показывается, если виджет не поднялся
        за 5 секунд."""
        self.assertIn("TIMEOUT_MS = 5000", JS)

    def test_missing_hotel_id_goes_straight_to_fallback(self):
        """Пока заказчик не прислал hotelId, ждать нечего: гость сразу
        получает форму заявки, а не пять секунд пустого окна."""
        self.assertIn("hotel_id_missing", JS)
        body = self.client.get(self.home).content.decode()
        self.assertIn('"hotelId": ""', body)


class WidgetErrorTests(TestCase):
    """П. 5.6.4: сбой логируется, владельцу приходит уведомление в Telegram."""

    def setUp(self):
        cache.clear()

    @patch("forms.notifications.send_service_message")
    def test_failure_notifies_owner(self, mocked):
        response = self.client.post(
            reverse("forms:widget_error"),
            {"reason": "script_load_failed", "page": "/", "entry_point": "2"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(mocked.called)
        self.assertIn("script_load_failed", mocked.call_args[0][0])

    @patch("forms.notifications.send_service_message")
    def test_owner_is_not_spammed(self, mocked):
        """Если Контур лежит, о сбое сообщит каждый посетитель. Владельцу
        нужно одно сообщение, а не сотня одинаковых."""
        url = reverse("forms:widget_error")
        for _ in range(10):
            self.client.post(url, {"reason": "timeout_5s", "page": "/"})
        self.assertEqual(mocked.call_count, 1)

    def test_endpoint_never_fails_the_guest(self):
        """Это служебный сигнал: гость в этот момент уже видит форму заявки,
        и никакая неполадка здесь не должна до него дойти."""
        response = self.client.post(reverse("forms:widget_error"), {})
        self.assertEqual(response.status_code, 200)


class AnalyticsTests(TestCase):
    """П. 5.5 ТЗ: видно, с какой кнопки открыт виджет. Раздел 11 ТЗ и
    раздел 12 договора: персональные данные в чужую аналитику не уходят."""

    def test_entry_point_is_tracked(self):
        self.assertIn("booking_widget_open", JS)
        self.assertIn("entry_point", JS)

    def test_personal_data_is_not_sent_to_analytics(self):
        """Хук onBooking отдаёт ФИО, телефон и почту гостя. В цель уходят
        только сумма и идентификатор брони."""
        for field in ("customer", "fio", "phone", "email"):
            self.assertNotIn(
                field,
                JS,
                f"Поле {field} из хука Контура не должно попадать в аналитику",
            )

    def test_fallback_submit_is_a_separate_goal(self):
        """П. 5.6.3: отправка резервной формы — отдельная цель."""
        self.assertIn("booking_fallback_submitted", JS)


class RegressionTests(TestCase):
    """Ошибки, найденные проверкой в браузере. Тесты держат их закрытыми."""

    def test_scroll_is_restored_without_focus_jump(self):
        """Браузер подкручивает страницу к элементу, получающему фокус.
        Без preventScroll гость после закрытия окна улетал в начало
        страницы вместо места, где нажал кнопку (п. 5.2 ТЗ)."""
        self.assertIn("preventScroll", JS)

    def test_invisible_sticky_button_is_not_clickable(self):
        """Одной прозрачности мало: невидимая липкая кнопка продолжала
        ловить нажатия и попадать в обход по Tab."""
        css = (
            Path(__file__).resolve().parent.parent / "config/static/css/main.css"
        ).read_text(encoding="utf-8")
        block = css.split(".sticky-cta {")[1].split("}")[0]
        self.assertIn("visibility: hidden", block)
        self.assertIn("pointer-events: none", block)

    def test_sticky_button_appears_on_short_pages(self):
        """Если первый экран выше, чем экран плюс вся доступная прокрутка,
        наблюдатель не сработает никогда — и точка входа №6 таблицы п. 5.1
        пропала бы на коротких страницах."""
        site_js = (
            Path(__file__).resolve().parent.parent / "config/static/js/site.js"
        ).read_text(encoding="utf-8")
        self.assertIn("heroCannotLeaveView", site_js)
