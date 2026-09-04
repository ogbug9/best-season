from django.db import models
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.fields import RichTextField
from wagtail.models import Page
from wagtail.snippets.models import register_snippet


class ReviewSource(models.TextChoices):
    SITE = "site", "Форма на сайте"
    YANDEX = "yandex", "Яндекс.Карты"
    AVITO = "avito", "Авито"
    OTHER = "other", "Другое"


@register_snippet
class Review(models.Model):
    """Отзыв.

    Публикация только ручная — по разделу 2 ТЗ модерация на стороне владельца.
    Отзыв без привязки к дому попадает в общий пул для страницы «Отзывы»,
    с привязкой — показывается ещё и на странице дома (п. 4.1.7).
    """

    author_name = models.CharField("Имя автора", max_length=120)
    # В макете страницы дома над каждым отзывом стоит фотография.
    # Необязательная: на странице «Отзывы» отзывы идут без фото.
    image = models.ForeignKey(
        "wagtailimages.Image",
        verbose_name="Фото к отзыву",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    text = models.TextField("Текст отзыва")
    rating = models.PositiveSmallIntegerField(
        "Оценка",
        null=True,
        blank=True,
        choices=[(i, str(i)) for i in range(1, 6)],
    )
    visit_date = models.DateField("Дата поездки", null=True, blank=True)

    house = models.ForeignKey(
        "houses.HousePage",
        verbose_name="Дом",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reviews",
        help_text="Пусто — отзыв идёт только в общий пул на страницу «Отзывы».",
    )
    source = models.CharField(
        "Источник", max_length=16, choices=ReviewSource.choices, default=ReviewSource.SITE
    )

    is_published = models.BooleanField(
        "Опубликован",
        default=False,
        help_text="Отзывы публикуются только вручную после проверки.",
    )
    sort_order = models.PositiveSmallIntegerField("Порядок", default=100)
    created_at = models.DateTimeField("Добавлен", auto_now_add=True)

    panels = [
        MultiFieldPanel(
            [
                FieldPanel("author_name"),
                FieldPanel("text"),
                FieldPanel("image"),
                FieldPanel("rating"),
                FieldPanel("visit_date"),
            ],
            heading="Отзыв",
        ),
        MultiFieldPanel(
            [
                FieldPanel("house"),
                FieldPanel("source"),
                FieldPanel("is_published"),
                FieldPanel("sort_order"),
            ],
            heading="Привязка и публикация",
        ),
    ]

    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"
        ordering = ["sort_order", "-created_at"]

    def __str__(self):
        target = self.house.title if self.house else "общий"
        return f"{self.author_name} ({target})"


class ReviewsPage(Page):
    """Страница «Отзывы». Показывает общий пул: и отзывы без привязки
    к дому, и привязанные — по разделу 2 ТЗ публикация только ручная,
    так что сюда попадает лишь проверенное."""

    intro = models.CharField("Вступление", max_length=255, blank=True)
    body = RichTextField(
        "Текст", blank=True, features=["bold", "italic", "link", "ul", "ol"]
    )

    content_panels = Page.content_panels + [FieldPanel("intro"), FieldPanel("body")]
    max_count = 1

    class Meta:
        verbose_name = "Страница «Отзывы»"

    def get_context(self, request):
        context = super().get_context(request)
        context["reviews"] = Review.objects.filter(is_published=True)
        return context
