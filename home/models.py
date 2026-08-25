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
            ],
            heading="О ферме",
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
            HousePage.objects.live().order_by("sort_order_index", "title")[:4]
        )
        context["houses_index"] = HouseIndexPage.objects.live().first()
        context["services"] = Service.objects.filter(is_published=True)[:6]
        context["promotions"] = [p for p in Promotion.objects.all() if p.is_active][:3]
        context["reviews"] = Review.objects.filter(is_published=True)[:3]
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
