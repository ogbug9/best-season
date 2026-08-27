"""Проверки форм — раздел 7 и раздел 11 ТЗ.

Каждая проверка привязана к требованию, которое смотрят на приёмке:
согласие без предзаполнения, honeypot и рейт-лимит вместо капчи,
уведомления, выгрузка в CSV, минимальный состав персональных данных.
"""

from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse
from wagtail.models import Page, Site

from core.models import SiteSettings
from forms.forms import FallbackBookingForm, TransferForm
from forms.models import FormSubmission, FormType


class FormTestCase(TestCase):
    """Кеш живёт в памяти процесса и переживает отдельные тесты, поэтому
    счётчик рейт-лимита нужно сбрасывать перед каждым — иначе тесты
    начинают влиять друг на друга."""

    def setUp(self):
        cache.clear()


def payload(**extra):
    data = {
        "name": "Пётр",
        "phone": "+79990001122",
        "email": "",
        "message": "Заберите со станции",
        "consent_given": "on",
        "website": "",
        "source_url": "/kak-dobratsya/",
    }
    data.update(extra)
    return data


class ConsentTests(FormTestCase):
    """Раздел 11 ТЗ: чекбокс без предзаполнения, факт согласия хранится
    с датой и версией текста."""

    def test_consent_is_not_pre_checked(self):
        form = TransferForm()
        self.assertFalse(form.fields["consent_given"].initial)
        self.assertNotIn("checked", str(form["consent_given"]))

    def test_submission_without_consent_is_rejected(self):
        response = self.client.post(
            reverse("forms:submit", args=["transfer"]),
            payload(consent_given=""),
        )
        self.assertEqual(FormSubmission.objects.count(), 0)
        self.assertIn("form=error", response["Location"])

    def test_consent_version_and_time_are_stored(self):
        site = Site.objects.first()
        settings_obj = SiteSettings.for_site(site)
        settings_obj.consent_version = "1.3"
        settings_obj.save()

        self.client.post(reverse("forms:submit", args=["transfer"]), payload())

        submission = FormSubmission.objects.get()
        self.assertTrue(submission.consent_given)
        self.assertEqual(submission.consent_version, "1.3")
        self.assertIsNotNone(submission.consent_at)


class BotProtectionTests(FormTestCase):
    """П. 7 ТЗ: honeypot и ограничение частоты вместо капчи."""

    def test_honeypot_blocks_bots(self):
        self.client.post(
            reverse("forms:submit", args=["transfer"]),
            payload(website="http://spam.example"),
        )
        self.assertEqual(FormSubmission.objects.count(), 0)

    def test_rate_limit_after_five_submissions(self):
        url = reverse("forms:submit", args=["feedback"])
        for _ in range(5):
            self.client.post(url, payload())
        self.assertEqual(FormSubmission.objects.count(), 5)

        response = self.client.post(url, payload())
        self.assertEqual(FormSubmission.objects.count(), 5, "Шестая заявка прошла")
        self.assertIn("form=rate", response["Location"])

    def test_ip_is_not_stored(self):
        """Адрес посетителя к заявке отношения не имеет, и по разделу 11
        мы храним минимум данных — в модели поля под IP просто нет."""
        field_names = {f.name for f in FormSubmission._meta.get_fields()}
        self.assertNotIn("ip", field_names)
        self.assertNotIn("ip_address", field_names)


class ValidationTests(FormTestCase):
    def test_contact_is_required(self):
        self.client.post(
            reverse("forms:submit", args=["feedback"]),
            payload(phone="", email=""),
        )
        self.assertEqual(FormSubmission.objects.count(), 0)

    def test_checkout_must_be_after_checkin(self):
        form = FallbackBookingForm(
            data=payload(date_from="2026-09-10", date_to="2026-09-08")
        )
        self.assertFalse(form.is_valid())
        self.assertIn("date_to", form.errors)


class NotificationTests(FormTestCase):
    """П. 7 ТЗ: уведомление в Telegram и на почту не позже минуты."""

    @override_settings(NOTIFY_EMAIL="vladelec@example.ru", TELEGRAM_BOT_TOKEN="", TELEGRAM_CHAT_ID="")
    def test_email_is_sent(self):
        self.client.post(reverse("forms:submit", args=["transfer"]), payload())
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Пётр", mail.outbox[0].body)
        self.assertIsNotNone(FormSubmission.objects.get().notified_at)

    @override_settings(TELEGRAM_BOT_TOKEN="token", TELEGRAM_CHAT_ID="42", NOTIFY_EMAIL="")
    @patch("forms.notifications.requests.post")
    def test_telegram_is_called(self, mocked):
        mocked.return_value.raise_for_status.return_value = None
        self.client.post(reverse("forms:submit", args=["transfer"]), payload())
        self.assertTrue(mocked.called)
        url = mocked.call_args[0][0]
        self.assertIn("api.telegram.org/bottoken/sendMessage", url)

    @override_settings(TELEGRAM_BOT_TOKEN="token", TELEGRAM_CHAT_ID="42", NOTIFY_EMAIL="")
    @patch("forms.notifications.requests.post", side_effect=Exception("сеть недоступна"))
    def test_submission_survives_notification_failure(self, mocked):
        """Заявка сохраняется до отправки: если Telegram недоступен,
        данные гостя всё равно не теряются."""
        self.client.post(reverse("forms:submit", args=["transfer"]), payload())
        self.assertEqual(FormSubmission.objects.count(), 1)


class UtmTests(FormTestCase):
    def test_utm_is_captured(self):
        self.client.post(
            reverse("forms:submit", args=["feedback"]),
            payload(utm_source="instagram", utm_medium="stories"),
        )
        submission = FormSubmission.objects.get()
        self.assertEqual(submission.utm_source, "instagram")
        self.assertEqual(submission.utm_medium, "stories")
        self.assertEqual(submission.source_url, "/kak-dobratsya/")


class CsvExportTests(FormTestCase):
    """П. 7.5 ТЗ: заявки выгружаются в CSV."""

    def setUp(self):
        super().setUp()
        self.admin = get_user_model().objects.create_superuser(
            "admin", "a@e.ru", "pw12345678"
        )

    def test_export_contains_submissions(self):
        self.client.post(reverse("forms:submit", args=["transfer"]), payload())
        self.client.force_login(self.admin)

        response = self.client.get(reverse("forms_export_csv"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/csv", response["Content-Type"])

        body = response.content.decode("utf-8")
        self.assertTrue(body.startswith("﻿"), "Без BOM Excel испортит кириллицу")
        self.assertIn("Пётр", body)
        self.assertIn("Версия согласия", body)

    def test_export_requires_login(self):
        response = self.client.get(reverse("forms_export_csv"))
        self.assertNotEqual(response.status_code, 200)


class FormTypesTests(FormTestCase):
    def test_all_four_forms_plus_fallback_exist(self):
        """Раздел 7 ТЗ перечисляет четыре формы, п. 5.6 добавляет пятую —
        резервный сценарий бронирования."""
        from forms.forms import FORM_CLASSES

        self.assertEqual(
            set(FORM_CLASSES),
            {
                FormType.FEEDBACK,
                FormType.TRANSFER,
                FormType.CERTIFICATE,
                FormType.HOUSE_QUESTION,
                FormType.FALLBACK,
            },
        )
