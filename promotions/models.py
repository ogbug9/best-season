from django.db import models
from django.utils import timezone
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.models import Page
from wagtail.fields import RichTextField
from wagtail.snippets.models import register_snippet

BODY_FEATURES = ["bold", "italic", "link", "ul", "ol"]


@register_snippet
class Promotion(models.Model):
    """Акция.

    Тарифы и итоговые цены живут в Контуре — здесь только витринное описание
    предложения и период показа на сайте.
    """

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
    short_description = models.CharField("Краткое описание", max_length=255, blank=True)
    description = RichTextField("Условия акции", blank=True, features=BODY_FEATURES)

    date_from = models.DateField("Показывать с", null=True, blank=True)
    date_to = models.DateField("Показывать до", null=True, blank=True)

    is_published = models.BooleanField("Показывать на сайте", default=True)
    sort_order = models.PositiveSmallIntegerField("Порядок", default=100)

    panels = [
        MultiFieldPanel(
            [
                FieldPanel("title"),
                FieldPanel("slug"),
                FieldPanel("image"),
                FieldPanel("short_description"),
                FieldPanel("description"),
            ],
            heading="Акция",
        ),
        MultiFieldPanel(
            [
                FieldPanel("date_from"),
                FieldPanel("date_to"),
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

    @property
    def is_active(self):
        """Акция показывается, если опубликована и период не истёк."""
        if not self.is_published:
            return False
        today = timezone.localdate()
        if self.date_from and today < self.date_from:
            return False
        if self.date_to and today > self.date_to:
            return False
        return True


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
        context = super().get_context(request)
        context["promotions"] = [p for p in Promotion.objects.all() if p.is_active]
        return context
