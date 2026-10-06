import re

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.models import Page
from wagtail.fields import RichTextField
from wagtail.snippets.models import register_snippet

BODY_FEATURES = ["bold", "italic", "link", "ul", "ol"]
DAY_MONTH = RegexValidator(r'^(0[1-9]|[12]\d|3[01])\.(0[1-9]|1[0-2])$', 'Формат ДД.ММ, например 30.04')


def _day_month(value):
    day, month = map(int, value.split('.'))
    return month, day


def in_season(today, start, end):
    """Ежегодное окно «с ДД.ММ по ДД.ММ» включительно; окно может переходить через Новый год."""
    current, first, last = (today.month, today.day), _day_month(start), _day_month(end)
    if first <= last:
        return first <= current <= last
    return current >= first or current <= last


@register_snippet
class Promotion(models.Model):
    """Акция.

    Тарифы и итоговые цены живут в Контуре — здесь только витринное описание
    предложения и период показа на сайте.
    """

    class CTAType(models.TextChoices):
        BOOKING = 'booking', 'Забронировать'
        REQUEST = 'request', 'Оставить заявку'

    title = models.CharField("Заголовок", max_length=160)
    slug = models.SlugField("Идентификатор", unique=True, max_length=160)
    image = models.ForeignKey(
        "wagtailimages.Image",
        verbose_name="Изображение",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    # TextField, а не CharField: в админке однострочный input срезает
    mobile_image = models.ForeignKey(
        'wagtailimages.Image', verbose_name='Фото для мобильного макета',
        null=True, blank=True, on_delete=models.SET_NULL, related_name='+',
    )
    # переносы, а описание акции в макете стоит в три строки.
    short_description = models.TextField("Краткое описание", max_length=255, blank=True)
    description = RichTextField("Условия акции", blank=True, features=BODY_FEATURES)
    cta_type = models.CharField('Действие кнопки', max_length=16, choices=CTAType.choices, default=CTAType.BOOKING)
    cta_label = models.CharField('Подпись кнопки', max_length=80, blank=True)
    is_visible = models.BooleanField('Показывать на сайте', default=True)

    date_from = models.DateField("Показывать с", null=True, blank=True)
    date_to = models.DateField("Показывать до", null=True, blank=True)
    # Сезонные тарифы сменяют друг друга каждый год сами: «С мая по сентябрь»
    # и «С октября по апрель» стоят на одном месте (одинаковый порядок).
    season_start = models.CharField(
        "Каждый год показывать с (ДД.ММ)", max_length=5, blank=True, validators=[DAY_MONTH],
        help_text="Например 30.04. Пусто — показывать круглый год.")
    season_end = models.CharField(
        "по (ДД.ММ)", max_length=5, blank=True, validators=[DAY_MONTH],
        help_text="Включительно, например 29.09. Окно может переходить через Новый год.")

    is_published = models.BooleanField("Опубликована", default=True)
    sort_order = models.PositiveSmallIntegerField("Порядок", default=100)

    panels = [
        MultiFieldPanel(
            [
                FieldPanel("title"),
                FieldPanel("slug"),
                FieldPanel("image"),
                FieldPanel("mobile_image"),
                FieldPanel("short_description"),
                FieldPanel("description"),
                FieldPanel("cta_type"),
                FieldPanel("cta_label"),
                FieldPanel("is_visible"),
            ],
            heading="Акция",
        ),
        MultiFieldPanel(
            [
                FieldPanel("date_from"),
                FieldPanel("date_to"),
                FieldPanel("season_start"),
                FieldPanel("season_end"),
                FieldPanel("is_published"),
                FieldPanel("sort_order"),
            ],
            heading="Период и публикация",
        ),
    ]

    class Meta:
        verbose_name = "Акция"
        verbose_name_plural = "Акции"
        ordering = ["sort_order", "-date_from"]

    def __str__(self):
        return self.title

    def clean(self):
        super().clean()
        if bool(self.season_start) != bool(self.season_end):
            raise ValidationError({'season_end': 'Заполните обе даты сезона или оставьте обе пустыми.'})

    @property
    def is_active(self):
        """Акция показывается, если опубликована и период не истёк."""
        if not self.is_published or not self.is_visible:
            return False
        today = timezone.localdate()
        if self.date_from and today < self.date_from:
            return False
        if self.date_to and today > self.date_to:
            return False
        if self.season_start and self.season_end:
            if all(re.fullmatch(r'\d\d\.\d\d', v) for v in (self.season_start, self.season_end)):
                return in_season(today, self.season_start, self.season_end)
        return True

    @property
    def button_label(self):
        return self.cta_label or self.get_cta_type_display()

    @property
    def request_form_type(self):
        return 'certificate' if self.slug == 'podarochnyy-sertifikat' else 'feedback'


class PromotionsPage(Page):
    """Страница «Акции». Показывает только те, у которых период показа
    не истёк, — логика в свойстве is_active самой акции."""

    intro = models.CharField("Вступление", max_length=255, blank=True)
    body = RichTextField("Текст", blank=True, features=BODY_FEATURES)

    content_panels = Page.content_panels + [FieldPanel("intro"), FieldPanel("body")]
    max_count = 1

    class Meta:
        verbose_name = "Страница «Акции»"

    def get_context(self, request):
        from core.models import FaqItem

        context = super().get_context(request)
        context["promotions"] = [p for p in Promotion.objects.all() if p.is_active]
        from forms.forms import FeedbackForm, CertificateForm
        selected = next((p for p in context['promotions'] if p.slug == request.GET.get('promotion')), None)
        topic = f'Акция: {selected.title}' if selected else ''
        context['promotion_request_topic'] = topic
        context['promotion_feedback_form'] = FeedbackForm(auto_id='promo_feedback_%s', initial={'topic': topic})
        context['promotion_certificate_form'] = CertificateForm(auto_id='promo_certificate_%s', initial={'topic': topic})
        from core.faq_sets import PROMOTION_FAQ, page_faq

        context["faq"] = page_faq(PROMOTION_FAQ)
        return context
