from django.db import models
from modelcluster.fields import ParentalKey
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.fields import RichTextField
from wagtail.models import Orderable, Page

BODY_FEATURES = ["bold", "italic", "link", "ul", "ol"]


class HomePage(Page):
    """Главная. Состав первого экрана — по п. 9.2.1 ТЗ:
    надпись-описание, кнопка «Посмотреть дома» и живое фото-слайд-шоу на фоне.
    Плюс точка входа в бронирование №2 из таблицы п. 5.1.

    Блоки ниже собираются автоматически из уже заведённого контента
    (дома, допуслуги, акции, отзывы) — редактор не составляет главную
    вручную и не может её развалить, п. 8 ТЗ.
    """

    hero_title = models.CharField(
        "Заголовок первого экрана", max_length=120, blank=True,
        help_text="Короткая надпись-описание под логотипом.",
    )
    hero_subtitle = models.CharField(
        "Подзаголовок", max_length=200, blank=True,
    )
    hero_cta_text = models.CharField(
        "Текст кнопки", max_length=40, default="Посмотреть дома",
    )
    hero_cta_page = models.ForeignKey(
        "wagtailcore.Page",
        verbose_name="Куда ведёт кнопка",
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Обычно раздел «Наши домики».",
    )

    about_title = models.CharField("Заголовок блока о ферме", max_length=120, blank=True)
    about_text = RichTextField("Текст о ферме", blank=True, features=BODY_FEATURES)
    about_image = models.ForeignKey(
        "wagtailimages.Image", verbose_name="Фото к блоку",
        null=True, blank=True, on_delete=models.SET_NULL, related_name="+",
    )

    about_page = models.ForeignKey(
        "wagtailcore.Page",
        verbose_name="Страница «О нас»",
        null=True, blank=True, on_delete=models.SET_NULL, related_name="+",
        help_text="Куда ведёт кнопка «Подробнее» из блока о ферме.",
    )

    territory_lead = models.CharField(
        "Подпись под заголовком «Наша территория»", max_length=200, blank=True,
        help_text="По макету: «Большой лесной массив для уединённого отдыха».",
    )
    territory_more_label = models.CharField(
        "Текст плитки-ссылки в мозаике", max_length=80, blank=True,
        default="Больше развлечений и услуг",
    )
    territory_more_page = models.ForeignKey(
        "wagtailcore.Page", verbose_name="Куда ведёт плитка-ссылка",
        null=True, blank=True, on_delete=models.SET_NULL, related_name="+",
    )

    nearby_more_label = models.CharField(
        "Текст кнопки под блоком «Интересное рядом»", max_length=80, blank=True,
        default="Больше интересных мест рядом",
    )
    nearby_more_page = models.ForeignKey(
        "wagtailcore.Page", verbose_name="Куда ведёт кнопка",
        null=True, blank=True, on_delete=models.SET_NULL, related_name="+",
    )

    quote_text = models.TextField(
        "Текст блока-цитаты", blank=True,
        help_text="Крупная выдержка между блоками «О нас» и «Наши домики».",
    )
    quote_author = models.CharField("Подпись под цитатой", max_length=120, blank=True)
    quote_image = models.ForeignKey(
        "wagtailimages.Image", verbose_name="Фото к цитате",
        null=True, blank=True, on_delete=models.SET_NULL, related_name="+",
    )

    slogan = models.CharField(
        "Слоган", max_length=200, blank=True,
        help_text="Одна строка во всю ширину. По макету: «Не ждите подходящего момента…».",
    )

    gallery_title = models.CharField(
        "Заголовок фотогалереи", max_length=120, blank=True, default="Фотогалерея",
    )
    gallery_text = models.TextField("Текст под заголовком галереи", blank=True)
    gallery_page = models.ForeignKey(
        "wagtailcore.Page",
        verbose_name="Страница «Галерея»",
        null=True, blank=True, on_delete=models.SET_NULL, related_name="+",
    )

    directions_title = models.CharField(
        "Заголовок блока «Как добраться»", max_length=120, blank=True,
        default="Как добраться",
    )
    directions_teaser = models.CharField(
        "Краткий текст о дороге", max_length=255, blank=True,
        help_text="Например: «2 часа от МКАД по Симферопольскому шоссе».",
    )
    directions_page = models.ForeignKey(
        "wagtailcore.Page",
        verbose_name="Страница «Как добраться»",
        null=True, blank=True, on_delete=models.SET_NULL, related_name="+",
    )

    content_panels = Page.content_panels + [
        MultiFieldPanel(
            [
                FieldPanel("hero_title"),
                FieldPanel("hero_subtitle"),
                FieldPanel("hero_cta_text"),
                FieldPanel("hero_cta_page"),
            ],
            heading="Первый экран",
        ),
        InlinePanel(
            "hero_links",
            label="Кнопки-разделы на первом экране",
            help_text="По макету их три. Пусто — ряд не показывается.",
            max_num=4,
        ),
        InlinePanel(
            "slides",
            label="Фото для слайд-шоу",
            help_text="От 3 до 5 фото. Первое — самое важное, оно грузится сразу.",
            max_num=5,
        ),
        MultiFieldPanel(
            [
                FieldPanel("about_title"),
                FieldPanel("about_text"),
                FieldPanel("about_image"),
                FieldPanel("about_page"),
            ],
            heading="О ферме",
        ),
        MultiFieldPanel(
            [
                FieldPanel("quote_text"),
                FieldPanel("quote_author"),
                FieldPanel("quote_image"),
            ],
            heading="Блок-цитата",
        ),
        FieldPanel("slogan"),
        MultiFieldPanel(
            [
                FieldPanel("territory_lead"),
                FieldPanel("territory_more_label"),
                FieldPanel("territory_more_page"),
            ],
            heading="Наша территория",
        ),
        MultiFieldPanel(
            [
                FieldPanel("nearby_more_label"),
                FieldPanel("nearby_more_page"),
            ],
            heading="Интересное рядом",
        ),
        MultiFieldPanel(
            [
                FieldPanel("gallery_title"),
                FieldPanel("gallery_text"),
                FieldPanel("gallery_page"),
            ],
            heading="Фотогалерея",
        ),
        InlinePanel(
            "gallery_images",
            label="Фото галереи",
            help_text="От 6 до 10 фото для мозаики на главной.",
            max_num=10,
        ),
        MultiFieldPanel(
            [
                FieldPanel("directions_title"),
                FieldPanel("directions_teaser"),
                FieldPanel("directions_page"),
            ],
            heading="Как добраться — короткий блок",
        ),
    ]

    class Meta:
        verbose_name = "Главная страница"

    def get_context(self, request):
        from houses.models import HouseIndexPage, HousePage
        from promotions.models import Promotion
        from reviews.models import Review
        from services.models import Service

        context = super().get_context(request)
        context["houses"] = (
            # Порядок — как в дереве страниц админки: редактор перетаскивает
            # дома мышью и ожидает увидеть тот же порядок на главной.
            # Сортировка по названию давала «Второй, Первый, Третий».
            HousePage.objects.live().order_by("path")[:4]
        )
        context["houses_index"] = HouseIndexPage.objects.live().first()
        context["services"] = Service.objects.filter(is_published=True)[:6]
        context["promotions"] = [p for p in Promotion.objects.all() if p.is_active][:3]
        context["reviews"] = Review.objects.filter(is_published=True)[:3]

        from core.models import FaqItem, NearbyPlace, TerritoryItem

        context["territory"] = TerritoryItem.objects.filter(is_published=True)
        context["nearby"] = NearbyPlace.objects.filter(is_published=True)[:3]
        context["faq"] = FaqItem.objects.filter(is_published=True, show_on_home=True)
        return context


class HomeSlide(Orderable):
    """Кадр фонового слайд-шоу первого экрана.

    Перелистывание сделано на CSS без JavaScript: слайд-шоу на скриптах
    утяжелило бы первый экран, а скорость на мобильных — предмет приёмки
    по п. 1.2 ТЗ.
    """

    page = ParentalKey(HomePage, on_delete=models.CASCADE, related_name="slides")
    image = models.ForeignKey(
        "wagtailimages.Image", verbose_name="Фото",
        on_delete=models.CASCADE, related_name="+",
    )
    alt = models.CharField(
        "Описание фото", max_length=200, blank=True,
        help_text="Что на фото. Нужно для доступности и поиска.",
    )

    panels = [FieldPanel("image"), FieldPanel("alt")]

    class Meta(Orderable.Meta):
        verbose_name = "Фото слайд-шоу"
        verbose_name_plural = "Фото слайд-шоу"


class HomeGalleryImage(Orderable):
    """Фото мозаики «Фотогалерея» на главной."""

    page = ParentalKey(HomePage, on_delete=models.CASCADE, related_name="gallery_images")
    image = models.ForeignKey(
        "wagtailimages.Image", verbose_name="Фото",
        on_delete=models.CASCADE, related_name="+",
    )
    alt = models.CharField("Описание фото", max_length=200, blank=True)
    is_large = models.BooleanField(
        "Крупная плитка", default=False,
        help_text="Занимает две ячейки. Отмечать одну-две.",
    )

    panels = [FieldPanel("image"), FieldPanel("alt"), FieldPanel("is_large")]

    class Meta(Orderable.Meta):
        verbose_name = "Фото галереи"
        verbose_name_plural = "Фото галереи"


class HeroLink(Orderable):
    """Кнопка-раздел в ряду на первом экране — по макету их три."""

    page = ParentalKey(HomePage, on_delete=models.CASCADE, related_name="hero_links")
    label = models.CharField("Подпись", max_length=60)
    link_page = models.ForeignKey(
        "wagtailcore.Page", verbose_name="Куда ведёт",
        null=True, blank=True, on_delete=models.SET_NULL, related_name="+",
    )

    panels = [FieldPanel("label"), FieldPanel("link_page")]

    class Meta(Orderable.Meta):
        verbose_name = "Кнопка-раздел"
        verbose_name_plural = "Кнопки-разделы"
