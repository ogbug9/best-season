from django.core.exceptions import ValidationError
from django.db import models
from modelcluster.fields import ParentalKey, ParentalManyToManyField
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.fields import RichTextField
from wagtail.models import Orderable, Page
from wagtail.search import index

# Требование п. 4.1.2 ТЗ: галерея не меньше 15 фото на дом.
MIN_GALLERY_IMAGES = 15

# Ограниченный набор форматирования: п. 8 ТЗ — редактор не должен иметь
# возможности сломать вёрстку. Заголовки и произвольный HTML недоступны.
BODY_FEATURES = ["bold", "italic", "link", "ul", "ol"]


class HouseIndexPage(Page):
    """Раздел «Наши домики» / «Размещение» — родитель для страниц домов."""

    intro = RichTextField("Вступительный текст", blank=True, features=BODY_FEATURES)

    content_panels = Page.content_panels + [FieldPanel("intro")]

    subpage_types = ["houses.HousePage"]
    max_count = 1

    class Meta:
        verbose_name = "Раздел «Наши домики»"

    def get_context(self, request):
        context = super().get_context(request)
        context["houses"] = (
            HousePage.objects.child_of(self).live().order_by("sort_order_index", "title")
        )
        return context


class HousePage(Page):
    """Страница дома. Порядок блоков на странице зафиксирован в шаблоне
    по п. 4.1 ТЗ и редактором не меняется — он правит только содержимое.
    """

    # Точное название категории, как заведено в PMS Контура.
    # Предвыбор дома в виджете технически невозможен (см. 03-kontur-widget.md),
    # поэтому название выводится подписью рядом с кнопкой бронирования — п. 5.3.2 ТЗ.
    pms_name = models.CharField(
        "Название категории в Контуре",
        max_length=255,
        blank=True,
        help_text=(
            "Точно как заведено в PMS Контур.Отеля. "
            "Выводится подписью у кнопки бронирования."
        ),
    )

    hero_image = models.ForeignKey(
        "wagtailimages.Image",
        verbose_name="Фото первого экрана",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    short_description = models.CharField(
        "Краткое описание", max_length=255, blank=True,
        help_text="Одна строка под названием на первом экране и в карточке дома.",
    )
    description = RichTextField("Описание", blank=True, features=BODY_FEATURES)

    capacity = models.PositiveSmallIntegerField("Вместимость, чел.", default=2)
    area = models.DecimalField(
        "Площадь, м²", max_digits=6, decimal_places=1, null=True, blank=True
    )
    highlight = models.CharField(
        "Особенность", max_length=120, blank=True,
        help_text="Коротко: «с камином», «с панорамным окном». Показывается в характеристиках.",
    )
    price_from = models.PositiveIntegerField(
        "Цена от, ₽/сутки", null=True, blank=True,
        help_text="Справочно для витрины. Итоговый расчёт — всегда в виджете Контура.",
    )

    amenities = ParentalManyToManyField(
        "core.Amenity", verbose_name="Что входит", blank=True
    )

    sort_order_index = models.PositiveSmallIntegerField(
        "Порядок в списке", default=100
    )

    content_panels = Page.content_panels + [
        MultiFieldPanel(
            [
                FieldPanel("hero_image"),
                FieldPanel("short_description"),
                FieldPanel("pms_name"),
            ],
            heading="Первый экран и бронирование",
        ),
        InlinePanel("gallery_images", label="Фото галереи", min_num=0),
        FieldPanel("description"),
        MultiFieldPanel(
            [
                FieldPanel("capacity"),
                FieldPanel("area"),
                FieldPanel("highlight"),
                FieldPanel("price_from"),
            ],
            heading="Характеристики",
        ),
        FieldPanel("amenities"),
        FieldPanel("sort_order_index"),
    ]

    search_fields = Page.search_fields + [
        index.SearchField("short_description"),
        index.SearchField("description"),
    ]

    parent_page_types = ["houses.HouseIndexPage"]
    subpage_types = []

    class Meta:
        verbose_name = "Страница дома"
        verbose_name_plural = "Страницы домов"

    def clean(self):
        super().clean()
        # Мягкая проверка: блокируем только публикацию неполной галереи,
        # черновик сохранить можно.
        if self.live and self.pk:
            count = self.gallery_images.count()
            if 0 < count < MIN_GALLERY_IMAGES:
                raise ValidationError(
                    {
                        "title": (
                            f"По п. 4.1.2 ТЗ в галерее дома нужно не меньше "
                            f"{MIN_GALLERY_IMAGES} фото, сейчас {count}."
                        )
                    }
                )

    @property
    def amenities_by_group(self):
        """Удобства, сгруппированные для блока «Что входит»."""
        groups = {}
        for amenity in self.amenities.all():
            groups.setdefault(amenity.get_group_display(), []).append(amenity)
        return groups

    @property
    def other_houses(self):
        """Ссылки на 3 других дома — п. 4.1.9 ТЗ."""
        return (
            HousePage.objects.live()
            .exclude(pk=self.pk)
            .order_by("sort_order_index", "title")[:3]
        )

    @property
    def house_reviews(self):
        """2–3 отзыва о домике — п. 4.1.7 ТЗ."""
        from reviews.models import Review

        return Review.objects.filter(house=self, is_published=True)[:3]


class HouseGalleryImage(Orderable):
    page = ParentalKey(
        HousePage, on_delete=models.CASCADE, related_name="gallery_images"
    )
    image = models.ForeignKey(
        "wagtailimages.Image",
        verbose_name="Фото",
        on_delete=models.CASCADE,
        related_name="+",
    )
    caption = models.CharField(
        "Подпись", max_length=200, blank=True,
        help_text="Используется как alt. Пустая подпись — alt соберётся из названия дома.",
    )

    panels = [FieldPanel("image"), FieldPanel("caption")]

    class Meta(Orderable.Meta):
        verbose_name = "Фото галереи"
        verbose_name_plural = "Фото галереи"

    def __str__(self):
        return self.caption or f"Фото {self.sort_order}"
