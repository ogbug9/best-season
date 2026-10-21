from django.db import models
from django.utils.functional import cached_property
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.models import Page
from wagtail.fields import RichTextField
from wagtail.snippets.models import register_snippet

from core.models import InProgressMixin

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
    gallery_images = models.ManyToManyField(
        'wagtailimages.Image', blank=True, related_name='+', verbose_name='Дополнительные фото',
    )
    description = RichTextField("Описание", blank=True, features=BODY_FEATURES)

    price = models.PositiveIntegerField("Цена, ₽", null=True, blank=True)
    price_unit = models.CharField(
        "Единица", max_length=12, choices=PriceUnit.choices, default=PriceUnit.HOUR
    )
    @cached_property
    def display_image(self):
        """Своё фото услуги либо фото одноимённой карточки территории."""
        if self.image_id:
            return self.image
        from core.models import TerritoryItem

        name = " ".join(self.name.casefold().split())
        for item in TerritoryItem.objects.filter(is_published=True).exclude(image=None).select_related("image"):
            if " ".join(item.title.casefold().split()) == name:
                return item.image
        return None

    @cached_property
    def page_url(self):
        """Отдельная страница услуги (баня, беседка, фотосессии), если заведена."""
        from core.temp_pages import service_page_url

        return service_page_url(self.slug)

    @property
    def price_display(self):
        """Цена с неразрывным пробелом в разряде тысяч — как в макете."""
        if self.price is None:
            return ""
        return f"{self.price:,}".replace(",", "\u00a0")

    @property
    def card_slides(self):
        images = [self.display_image] if self.display_image else []
        ids = {image.pk for image in images}
        for image in self.gallery_images.all():
            if image.pk not in ids:
                images.append(image)
                ids.add(image.pk)
        return images

    includes = models.CharField(
        "Что входит", max_length=160, blank=True,
        help_text="Одна строка на странице услуг, например: веники и травяной чай.",
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
                FieldPanel("gallery_images"),
                FieldPanel("short_description"),
                FieldPanel("includes"),
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


class ServicesPage(InProgressMixin, Page):
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
        # Блоки страницы услуг (docs/dop-stranicy/11-uslugi.md).
        from core.models import FaqItem, TerritoryItem, _consent_page
        from forms.forms import CertificateForm
        from wagtail.models import Page

        context["group_page"] = Page.objects.live().filter(slug="vyezdy-kompaniy").first()
        bonfire = TerritoryItem.objects.filter(title="Костровая зона").select_related("image").first()
        context["group_image"] = bonfire.image if bonfire else None
        context["gift_answer"] = (FaqItem.objects.filter(is_published=True, question__startswith="Есть ли подарочные сертификаты")
                                  .values_list("answer", flat=True).first())
        context["certificate_form"] = CertificateForm(auto_id="services_certificate_%s")
        from houses.models import HousePage

        context["calc_houses"] = HousePage.objects.live().order_by("path")
        context["calc_banya"] = context["services"].filter(slug="russkaya-banya").first()
        context["calc_besedka"] = context["services"].filter(slug="bolshaya-besedka").first()
        context["consent_page"] = _consent_page()
        return context
