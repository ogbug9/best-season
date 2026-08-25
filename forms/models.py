from django.db import models


class FormType(models.TextChoices):
    """Четыре формы первой очереди — раздел 7 ТЗ."""

    FEEDBACK = "feedback", "Обратная связь"
    TRANSFER = "transfer", "Заказ трансфера"
    CERTIFICATE = "certificate", "Подарочный сертификат"
    HOUSE_QUESTION = "house_question", "Вопрос со страницы дома"
    FALLBACK = "fallback", "Резервный сценарий бронирования"


class SubmissionStatus(models.TextChoices):
    NEW = "new", "Новая"
    IN_PROGRESS = "in_progress", "В работе"
    DONE = "done", "Обработана"
    SPAM = "spam", "Спам"


class FormSubmission(models.Model):
    """Заявка с сайта.

    Состав полей — минимально необходимый по разделу 11 ТЗ: имя, телефон,
    email, даты, текст. Факт согласия хранится вместе с датой и версией
    текста политики, действовавшей на момент отправки.

    Тип FALLBACK — заявка из резервного сценария п. 5.6, когда виджет
    Контура не загрузился.
    """

    form_type = models.CharField(
        "Тип формы", max_length=24, choices=FormType.choices, db_index=True
    )

    name = models.CharField("Имя", max_length=120)
    phone = models.CharField("Телефон", max_length=32, blank=True)
    email = models.EmailField("Email", blank=True)
    message = models.TextField("Сообщение", blank=True)

    date_from = models.DateField("Дата заезда", null=True, blank=True)
    date_to = models.DateField("Дата выезда", null=True, blank=True)
    guests = models.PositiveSmallIntegerField("Гостей", null=True, blank=True)

    house = models.ForeignKey(
        "houses.HousePage",
        verbose_name="Дом",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="submissions",
    )
    source_url = models.CharField("Страница отправки", max_length=500, blank=True)

    utm_source = models.CharField("utm_source", max_length=120, blank=True)
    utm_medium = models.CharField("utm_medium", max_length=120, blank=True)
    utm_campaign = models.CharField("utm_campaign", max_length=120, blank=True)
    utm_content = models.CharField("utm_content", max_length=120, blank=True)
    utm_term = models.CharField("utm_term", max_length=120, blank=True)

    consent_given = models.BooleanField("Согласие на обработку ПД", default=False)
    consent_version = models.CharField("Версия текста согласия", max_length=16, blank=True)
    consent_at = models.DateTimeField("Дата согласия", null=True, blank=True)

    status = models.CharField(
        "Статус",
        max_length=16,
        choices=SubmissionStatus.choices,
        default=SubmissionStatus.NEW,
        db_index=True,
    )
    notified_at = models.DateTimeField(
        "Уведомление отправлено", null=True, blank=True,
        help_text="Проставляется после успешной отправки в Telegram и на email.",
    )
    created_at = models.DateTimeField("Получена", auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "Заявка"
        verbose_name_plural = "Заявки"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_form_type_display()} — {self.name} ({self.created_at:%d.%m.%Y %H:%M})"
