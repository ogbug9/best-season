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

    hero_image = models.ForeignKey(
        "wagtailimages.Image",
        verbose_name="Фото первого экрана",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    # Заголовок на странице и название в меню — это разные вещи: в меню
    # пункт называется «Размещение», а на самой странице в макете стоит
    # «Наши домики». Раньше H1 брался из title и на странице печаталось
    # название пункта меню.
    heading = models.CharField(
        "Заголовок на странице", max_length=120, blank=True,
        help_text="Если пусто — берётся название страницы",
    )
    # Подпись под заголовком «Доп услуги». В макете она в две строки,
    # перенос расставлен руками — держим его в самом тексте.
    services_intro = models.TextField(
        "Подпись под заголовком «Доп услуги»", blank=True,
        help_text="Перенос строки задаётся переводом строки",
    )
    intro = RichTextField("Вступительный текст", blank=True, features=BODY_FEATURES)

    content_panels = Page.content_panels + [
        FieldPanel("heading"),
        FieldPanel("hero_image"),
        FieldPanel("intro"),
        FieldPanel("services_intro"),
    ]

    subpage_types = ["houses.HousePage"]
    max_count = 1

    class Meta:
        verbose_name = "Раздел «Наши домики»"

    def get_context(self, request):
        from services.models import Service

        context = super().get_context(request)
        context["houses"] = (
            HousePage.objects.child_of(self)
            .live()
            .select_related("hero_image")
            .order_by("sort_order_index", "title")
        )
        # П. 9.2.2 ТЗ: «Размещение» = раздел с домиками + доп услуги —
        # одна страница, а не две. В макете доп услуги показаны двумя
        # рядами: почасовые объекты (баня, беседка) — крупными карточками
        # 610×500, остальное — плитками 295×295 с одним названием.
        services = Service.objects.filter(is_published=True)
        context["services"] = services
        context["hourly_services"] = services.filter(is_hourly=True)
        context["tile_services"] = services.filter(is_hourly=False)
        # Тот же аккордеон, что на главной — набор вопросов общий
        from core.models import FaqItem

        context["faq"] = FaqItem.objects.filter(is_published=True, show_on_home=True)
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

    @property
    def gallery_is_short(self):
        """Не добрана ли галерея до требования п. 4.1.2 ТЗ.

        Публикацию это не блокирует: на этапе разработки фото добираются
        постепенно, и жёсткий запрет мешал бы собирать страницы. Вместо
        запрета при публикации показывается предупреждение, а полный
        список недобранных домов виден в отчёте «Галереи домов».
        Требование остаётся в силе — к приёмке недобор должен быть закрыт.
        """
        if not self.pk:
            return False
        return self.gallery_images.count() < MIN_GALLERY_IMAGES

    @property
    def price_display(self):
        """Цена с разделителем тысяч, как в макете: «8 000», а не «8000».

        Пробел неразрывный: иначе число может разорваться переносом
        строки внутри ленты, а лента узкая.
        """
        if self.price_from is None:
            return ""
        return f"{self.price_from:,}".replace(",", "\u00a0")

    @property
    def gallery_count(self):
        return self.gallery_images.count() if self.pk else 0

    # В макете под фото карточки три точки, то есть листаются три кадра.
    # Больше не берём: карточка на главной — витрина, а не галерея,
    # весь набор лежит на странице дома.
    CARD_SLIDES = 3

    @property
    def card_slides(self):
        """Кадры для карусели в карточке на главной: обложка плюс галерея."""
        if not self.pk:
            return []
        slides = [self.hero_image] if self.hero_image else []
        for item in self.gallery_images.all()[: self.CARD_SLIDES]:
            if item.image and item.image not in slides:
                slides.append(item.image)
            if len(slides) >= self.CARD_SLIDES:
                break
        return slides

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
            .select_related("hero_image")
            .order_by("sort_order_index", "title")[:3]
        )

    def get_context(self, request):
        from core.models import _consent_page
        from forms.forms import HouseQuestionForm

        context = super().get_context(request)
        # Дом подставляется сразу, чтобы владелец видел, о чём вопрос (п. 7 ТЗ)
        context["question_form"] = HouseQuestionForm(initial={"house": self.pk})
        context["consent_page"] = _consent_page()
        return context

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
