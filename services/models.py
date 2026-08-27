from django.db import models
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.models import Page
from wagtail.fields import RichTextField
from wagtail.snippets.models import register_snippet

BODY_FEATURES = ["bold", "italic", "link", "ul", "ol"]


class PriceUnit(models.TextChoices):
    HOUR = "hour", "за час"
    DAY = "day", "за сутки"
    PERSON = "person", "с человека"
    PIECE = "piece", "за шт."
    FREE = "free", "бесплатно"


@register_snippet
class Service(models.Model):
    """Допуслуга: баня, беседка, велосипеды, завтраки, трансфер.

    Почасовые объекты (баня, беседка) продаются в Контуре только через
    виджет hourlyObjectsList — без него забронировать их с сайта нельзя
    (см. 03-kontur-widget.md). Здесь хранится витринное описание.
    """

    name = models.CharField("Название", max_length=120)
    slug = models.SlugField("Идентификатор", unique=True, max_length=120)
    image = models.ForeignKey(
        "wagtailimages.Image",
        verbose_name="Фото",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    short_description = models.CharField("Краткое описание", max_length=255, blank=True)
    description = RichTextField("Описание", blank=True, features=BODY_FEATURES)

    price = models.PositiveIntegerField("Цена, ₽", null=True, blank=True)
    price_unit = models.CharField(
        "Единица", max_length=12, choices=PriceUnit.choices, default=PriceUnit.HOUR
    )
    price_note = models.CharField(
        "Примечание к цене", max_length=120, blank=True,
        help_text="Например: «минимум 2 часа». Точный расчёт — в виджете Контура.",
    )

    is_hourly = models.BooleanField(
        "Почасовой объект в Контуре",
        default=False,
        help_text="Отмечать для бани, беседки и т.п. — того, что бронируется почасово.",
    )
    is_published = models.BooleanField("Показывать на сайте", default=True)
    sort_order = models.PositiveSmallIntegerField("Порядок", default=100)

    panels = [
        MultiFieldPanel(
            [
                FieldPanel("name"),
                FieldPanel("slug"),
                FieldPanel("image"),
                FieldPanel("short_description"),
                FieldPanel("description"),
            ],
            heading="Описание",
        ),
        MultiFieldPanel(
            [
                FieldPanel("price"),
                FieldPanel("price_unit"),
                FieldPanel("price_note"),
            ],
            heading="Цена",
        ),
        MultiFieldPanel(
            [
                FieldPanel("is_hourly"),
                FieldPanel("is_published"),
                FieldPanel("sort_order"),
            ],
            heading="Публикация",
        ),
    ]

    class Meta:
        verbose_name = "Допуслуга"
        verbose_name_plural = "Допуслуги"
        ordering = ["sort_order", "name"]

    def __str__(self):
        return self.name


class ServicesPage(Page):
    """«Услуги и завтраки» / «Доп услуги». Список берётся из справочника,
    тот же, что показывается блоком на главной и на странице дома."""

    intro = models.CharField("Вступление", max_length=255, blank=True)
    body = RichTextField("Текст", blank=True, features=BODY_FEATURES)

    content_panels = Page.content_panels + [FieldPanel("intro"), FieldPanel("body")]
    max_count = 1

    class Meta:
        verbose_name = "Страница «Услуги»"

    def get_context(self, request):
        context = super().get_context(request)
        context["services"] = Service.objects.filter(is_published=True)
        # Почасовые объекты Контура выделяются отдельно: их нельзя
        # забронировать иначе как через виджет (см. 03-kontur-widget.md)
        context["hourly"] = context["services"].filter(is_hourly=True)
        return context
