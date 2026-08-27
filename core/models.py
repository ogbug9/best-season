from django.db import models
from modelcluster.fields import ParentalKey
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.contrib.settings.models import BaseSiteSetting, register_setting
from wagtail.fields import RichTextField
from wagtail.models import Orderable, Page
from wagtail.snippets.models import register_snippet

# Ограниченный набор форматирования: п. 8 ТЗ — редактор не должен иметь
# возможности сломать вёрстку произвольной разметкой.
BODY_FEATURES = ["bold", "italic", "link", "ul", "ol"]

# Набор иконок закрыт списком: п. 9.4 ТЗ запрещает иконки вне согласованного набора,
# поэтому редактор выбирает из вариантов, а не вводит произвольное имя.
ICON_CHOICES = [
    ("wifi", "Wi-Fi"),
    ("parking", "Парковка"),
    ("kitchen", "Кухня"),
    ("fridge", "Холодильник"),
    ("stove", "Плита"),
    ("microwave", "Микроволновка"),
    ("kettle", "Чайник"),
    ("dishes", "Посуда"),
    ("shower", "Душ"),
    ("towels", "Полотенца"),
    ("hairdryer", "Фен"),
    ("bed", "Спальное место"),
    ("linen", "Постельное бельё"),
    ("tv", "Телевизор"),
    ("heating", "Отопление"),
    ("conditioner", "Кондиционер"),
    ("fireplace", "Камин"),
    ("terrace", "Терраса"),
    ("bbq", "Мангал"),
    ("gazebo", "Беседка"),
    ("sauna", "Баня"),
    ("pool", "Купель"),
    ("pets", "Можно с животными"),
    ("kids", "Можно с детьми"),
]


class AmenityGroup(models.TextChoices):
    INSIDE = "inside", "В доме"
    KITCHEN = "kitchen", "Кухня"
    BATHROOM = "bathroom", "Ванная"
    OUTSIDE = "outside", "На улице"
    RULES = "rules", "Условия"


@register_snippet
class Amenity(models.Model):
    """Элемент блока «Что входит» (п. 4.1.5 ТЗ).

    Вынесен в справочник, чтобы одни и те же удобства переиспользовались
    на всех домах и редактор не набирал их текстом заново на каждой странице.
    """

    name = models.CharField("Название", max_length=80)
    group = models.CharField(
        "Группа",
        max_length=16,
        choices=AmenityGroup.choices,
        default=AmenityGroup.INSIDE,
    )
    icon = models.CharField("Иконка", max_length=32, choices=ICON_CHOICES, blank=True)
    sort_order = models.PositiveSmallIntegerField("Порядок", default=100)

    panels = [
        FieldPanel("name"),
        FieldPanel("group"),
        FieldPanel("icon"),
        FieldPanel("sort_order"),
    ]

    class Meta:
        verbose_name = "Удобство"
        verbose_name_plural = "Удобства"
        ordering = ["group", "sort_order", "name"]

    def __str__(self):
        return f"{self.get_group_display()} — {self.name}"


@register_setting
class SiteSettings(BaseSiteSetting):
    """Контакты, реквизиты и юридические тексты для шапки/подвала.

    Реквизиты ИП в футере и версионирование текста согласия — требования
    раздела 11 ТЗ (факт согласия хранится с датой и версией текста).
    """

    phone = models.CharField(
        "Телефон", max_length=32, blank=True, help_text="В формате +79991234567"
    )
    phone_display = models.CharField(
        "Телефон для показа", max_length=32, blank=True, help_text="+7 (999) 123-45-67"
    )
    email = models.EmailField("Email", blank=True)

    telegram_url = models.URLField("Telegram", blank=True)
    whatsapp_url = models.URLField("WhatsApp", blank=True)
    vk_url = models.URLField("ВКонтакте", blank=True)

    address = models.CharField("Адрес", max_length=255, blank=True)
    yandex_map_url = models.URLField("Ссылка на Яндекс.Карты", blank=True)

    # Компактный блок «Как добраться» на странице дома — п. 4.1.6 ТЗ.
    # Текст общий для всех домов: маршрут до глэмпинга от выбора домика
    # не зависит, дублировать его на четырёх страницах смысла нет.
    directions_short = models.TextField(
        "Как добраться — краткий текст",
        blank=True,
        help_text=(
            "2–3 строки для компактного блока на странице дома. "
            "Полный маршрут — на отдельной странице «Как добраться»."
        ),
    )
    directions_page = models.ForeignKey(
        "wagtailcore.Page",
        verbose_name="Страница «Как добраться»",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Куда ведёт ссылка «Подробный маршрут» из блока на странице дома.",
    )

    legal_name = models.CharField("Наименование ИП", max_length=255, blank=True)
    inn = models.CharField("ИНН", max_length=16, blank=True)
    ogrnip = models.CharField("ОГРНИП", max_length=24, blank=True)
    legal_address = models.CharField("Юридический адрес", max_length=255, blank=True)

    consent_version = models.CharField(
        "Версия текста согласия",
        max_length=16,
        default="1.0",
        help_text="Меняется при правке текста согласия. Сохраняется вместе с каждой заявкой.",
    )
    consent_text = RichTextField(
        "Текст согласия на обработку ПД",
        blank=True,
        features=["bold", "italic", "link"],
    )
    cookie_text = models.TextField("Текст cookie-баннера", blank=True)

    # Виджет Контур.Отеля — раздел 5 ТЗ.
    #
    # hotelId держим здесь, а не только в переменных окружения, намеренно:
    # это не секрет (он и так уходит в браузер каждому посетителю), зато
    # правка в админке применяется сразу, без пересборки контейнера. Когда
    # заказчик пришлёт идентификатор, бронирование включится за минуту.
    kontur_hotel_id = models.CharField(
        "hotelId Контур.Отеля",
        max_length=64,
        blank=True,
        help_text=(
            "Идентификатор из личного кабинета Контур.Отеля. "
            "Пока поле пустое, все кнопки бронирования показывают резервную "
            "форму заявки — сайт остаётся рабочим."
        ),
    )
    booking_lead_text = models.TextField(
        "Подводящий текст над виджетом",
        blank=True,
        default=(
            "Выберите даты и количество гостей — система покажет свободные домики "
            "и стоимость. Бронь подтверждается после предоплаты."
        ),
        help_text="2–3 строки, объясняющие, что произойдёт дальше (п. 5.4.3 ТЗ).",
    )
    yandex_metrika_id = models.CharField(
        "Номер счётчика Яндекс.Метрики",
        max_length=16,
        blank=True,
        help_text="Только цифры. Пока пусто — цели бронирования не отправляются.",
    )

    @property
    def kontur_is_configured(self):
        return bool(self.kontur_hotel_id.strip())

    panels = [
        MultiFieldPanel(
            [
                FieldPanel("phone"),
                FieldPanel("phone_display"),
                FieldPanel("email"),
            ],
            heading="Контакты",
        ),
        MultiFieldPanel(
            [
                FieldPanel("telegram_url"),
                FieldPanel("whatsapp_url"),
                FieldPanel("vk_url"),
            ],
            heading="Мессенджеры и соцсети",
        ),
        MultiFieldPanel(
            [
                FieldPanel("address"),
                FieldPanel("yandex_map_url"),
                FieldPanel("directions_short"),
                FieldPanel("directions_page"),
            ],
            heading="Адрес и маршрут",
        ),
        MultiFieldPanel(
            [
                FieldPanel("legal_name"),
                FieldPanel("inn"),
                FieldPanel("ogrnip"),
                FieldPanel("legal_address"),
            ],
            heading="Реквизиты для подвала",
        ),
        MultiFieldPanel(
            [
                FieldPanel("consent_version"),
                FieldPanel("consent_text"),
                FieldPanel("cookie_text"),
            ],
            heading="Юридические тексты",
        ),
        MultiFieldPanel(
            [
                FieldPanel("kontur_hotel_id"),
                FieldPanel("booking_lead_text"),
                FieldPanel("yandex_metrika_id"),
            ],
            heading="Бронирование и аналитика",
        ),
    ]

    class Meta:
        verbose_name = "Настройки сайта"


@register_snippet
class TerritoryItem(models.Model):
    """Плитка блока «Наша территория».

    Отдельным справочником, а не полями на главной: по макету этот же
    набор идёт и на отдельную страницу «Территория», а редактор не
    должен заводить одно и то же дважды.
    """

    title = models.CharField("Название", max_length=120)
    image = models.ForeignKey(
        "wagtailimages.Image", verbose_name="Фото",
        null=True, blank=True, on_delete=models.SET_NULL, related_name="+",
    )
    description = models.CharField("Краткое описание", max_length=255, blank=True)
    is_large = models.BooleanField(
        "Крупная плитка", default=False,
        help_text="Занимает две ячейки в мозаике. Отмечать не больше двух-трёх.",
    )
    is_published = models.BooleanField("Показывать на сайте", default=True)
    sort_order = models.PositiveSmallIntegerField("Порядок", default=100)

    panels = [
        FieldPanel("title"),
        FieldPanel("image"),
        FieldPanel("description"),
        FieldPanel("is_large"),
        FieldPanel("is_published"),
        FieldPanel("sort_order"),
    ]

    class Meta:
        verbose_name = "Плитка территории"
        verbose_name_plural = "Наша территория"
        ordering = ["sort_order", "title"]

    def __str__(self):
        return self.title


@register_snippet
class NearbyPlace(models.Model):
    """Карточка блока «Интересное рядом».

    В макете их три, с номерами 01/02/03. Номер считается по порядку
    вывода, вручную его никто не проставляет — иначе при удалении
    средней карточки нумерация поедет.
    """

    title = models.CharField("Название", max_length=120)
    image = models.ForeignKey(
        "wagtailimages.Image", verbose_name="Фото",
        null=True, blank=True, on_delete=models.SET_NULL, related_name="+",
    )
    description = models.TextField("Описание", blank=True)
    link_url = models.URLField(
        "Ссылка «Подробнее»", blank=True,
        help_text="Внешний адрес: сайт музея, статья. Пусто — кнопки не будет.",
    )
    is_published = models.BooleanField("Показывать на сайте", default=True)
    sort_order = models.PositiveSmallIntegerField("Порядок", default=100)

    panels = [
        FieldPanel("title"),
        FieldPanel("image"),
        FieldPanel("description"),
        FieldPanel("link_url"),
        FieldPanel("is_published"),
        FieldPanel("sort_order"),
    ]

    class Meta:
        verbose_name = "Место рядом"
        verbose_name_plural = "Интересное рядом"
        ordering = ["sort_order", "title"]

    def __str__(self):
        return self.title


@register_snippet
class FaqItem(models.Model):
    """Вопрос-ответ.

    По макету аккордеон стоит и на главной, и на отдельной странице FAQ,
    поэтому справочник общий. На главной показываются отмеченные галочкой.
    """

    question = models.CharField("Вопрос", max_length=255)
    answer = RichTextField(
        "Ответ", features=["bold", "italic", "link", "ul", "ol"]
    )
    show_on_home = models.BooleanField(
        "Показывать на главной", default=True,
    )
    is_published = models.BooleanField("Показывать на сайте", default=True)
    sort_order = models.PositiveSmallIntegerField("Порядок", default=100)

    panels = [
        FieldPanel("question"),
        FieldPanel("answer"),
        FieldPanel("show_on_home"),
        FieldPanel("is_published"),
        FieldPanel("sort_order"),
    ]

    class Meta:
        verbose_name = "Вопрос и ответ"
        verbose_name_plural = "Ответы на вопросы"
        ordering = ["sort_order", "question"]

    def __str__(self):
        return self.question


def _consent_page():
    """Страница политики обработки ПД для ссылки под чекбоксом согласия.

    Ищется по слагу, а не хранится настройкой: так редактору не нужно
    ничего связывать вручную, а если страницы ещё нет — ссылка просто
    не выводится, форма продолжает работать.
    """
    from wagtail.models import Page

    return Page.objects.live().filter(slug__in=["politika", "politika-pd"]).first()


# =========================================================================
# Страницы второй очереди вёрстки (Фаза 6)
#
# Все типы страниц описаны структурными полями, а не свободным StreamField:
# по п. 8 ТЗ редактор физически не должен уметь сломать вёрстку. Он правит
# содержимое, а порядок и оформление блоков задаёт шаблон.
# =========================================================================


class ContentPage(Page):
    """Простая текстовая страница: «О нас», правовые, «Цены и условия»,
    «Партнёрам». Всё, что не требует особой структуры."""

    intro = models.CharField("Короткое вступление", max_length=255, blank=True)
    hero_image = models.ForeignKey(
        "wagtailimages.Image", verbose_name="Фото в шапке страницы",
        null=True, blank=True, on_delete=models.SET_NULL, related_name="+",
    )
    body = RichTextField("Текст", blank=True, features=BODY_FEATURES)
    show_booking_cta = models.BooleanField(
        "Показывать кнопку бронирования внизу", default=True,
    )

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
        FieldPanel("hero_image"),
        FieldPanel("body"),
        FieldPanel("show_booking_cta"),
    ]

    class Meta:
        verbose_name = "Текстовая страница"
        verbose_name_plural = "Текстовые страницы"


class DirectionsPage(Page):
    """«Как добраться» — п. 4.2 ТЗ.

    Страница закрывает главный барьер аудитории и не может быть сокращена
    в первой очереди. Состав полей повторяет требования п. 4.2 один в один,
    чтобы на приёмке было видно соответствие.
    """

    intro = models.CharField("Короткое вступление", max_length=255, blank=True)

    # 4.2.1 — маршрут на автомобиле
    car_distance = models.CharField(
        "Расстояние на авто", max_length=80, blank=True,
        help_text="Например: 100 км от Москвы.",
    )
    car_time = models.CharField("Время в пути на авто", max_length=80, blank=True)
    car_route = RichTextField("Описание маршрута на авто", blank=True, features=BODY_FEATURES)
    yandex_route_url = models.URLField(
        "Ссылка на маршрут в Яндекс.Картах", blank=True,
    )

    # 4.2.2 — маршрут без автомобиля
    transit_route = RichTextField(
        "Маршрут на электричке или автобусе", blank=True, features=BODY_FEATURES,
        help_text="С названиями станций и ориентировочным временем — требование п. 4.2.",
    )

    # 4.2.3 — трансфер
    transfer_price = models.CharField("Стоимость трансфера", max_length=120, blank=True)
    transfer_note = RichTextField(
        "Порядок заказа трансфера", blank=True, features=BODY_FEATURES,
    )

    # 4.2.5 — карта
    map_image = models.ForeignKey(
        "wagtailimages.Image", verbose_name="Превью карты",
        null=True, blank=True, on_delete=models.SET_NULL, related_name="+",
        help_text="Скриншот карты. Показывается вместо самой карты до клика — "
                  "так карта не тянет чужие скрипты при загрузке страницы.",
    )
    map_embed_url = models.URLField(
        "Адрес карты для встраивания", blank=True,
        help_text="Ссылка «Поделиться → Код для вставки» из Яндекс.Карт, только адрес из src.",
    )

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
        MultiFieldPanel(
            [
                FieldPanel("car_distance"),
                FieldPanel("car_time"),
                FieldPanel("car_route"),
                FieldPanel("yandex_route_url"),
            ],
            heading="На автомобиле (п. 4.2.1)",
        ),
        FieldPanel("transit_route"),
        MultiFieldPanel(
            [
                FieldPanel("transfer_price"),
                FieldPanel("transfer_note"),
            ],
            heading="Трансфер (п. 4.2.3)",
        ),
        MultiFieldPanel(
            [
                FieldPanel("map_image"),
                FieldPanel("map_embed_url"),
            ],
            heading="Карта (п. 4.2.5)",
        ),
    ]

    max_count = 1

    class Meta:
        verbose_name = "Страница «Как добраться»"

    def get_context(self, request):
        from forms.forms import TransferForm

        context = super().get_context(request)
        context["transfer_form"] = TransferForm()
        context["consent_page"] = _consent_page()
        return context


class ContactsPage(Page):
    """Контакты. Телефон, почта и реквизиты берутся из настроек сайта,
    чтобы не расходиться с подвалом."""

    intro = models.CharField("Вступление", max_length=255, blank=True)
    body = RichTextField("Дополнительный текст", blank=True, features=BODY_FEATURES)
    map_image = models.ForeignKey(
        "wagtailimages.Image", verbose_name="Превью карты",
        null=True, blank=True, on_delete=models.SET_NULL, related_name="+",
    )
    map_embed_url = models.URLField("Адрес карты для встраивания", blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
        FieldPanel("body"),
        MultiFieldPanel([FieldPanel("map_image"), FieldPanel("map_embed_url")], heading="Карта"),
    ]

    max_count = 1

    class Meta:
        verbose_name = "Страница «Контакты»"

    def get_context(self, request):
        from forms.forms import FeedbackForm

        context = super().get_context(request)
        context["feedback_form"] = FeedbackForm()
        context["consent_page"] = _consent_page()
        return context


class TerritoryPage(Page):
    """«Наша территория». Плитки берутся из справочника TerritoryItem —
    того же, что выводится блоком на главной."""

    intro = models.CharField("Вступление", max_length=255, blank=True)
    body = RichTextField("Текст", blank=True, features=BODY_FEATURES)

    content_panels = Page.content_panels + [FieldPanel("intro"), FieldPanel("body")]
    max_count = 1

    class Meta:
        verbose_name = "Страница «Территория»"

    def get_context(self, request):
        context = super().get_context(request)
        context["territory"] = TerritoryItem.objects.filter(is_published=True)
        return context


class NearbyPage(Page):
    """«Интересное рядом». Карточки из справочника NearbyPlace."""

    intro = models.CharField("Вступление", max_length=255, blank=True)
    body = RichTextField("Текст", blank=True, features=BODY_FEATURES)

    content_panels = Page.content_panels + [FieldPanel("intro"), FieldPanel("body")]
    max_count = 1

    class Meta:
        verbose_name = "Страница «Интересное рядом»"

    def get_context(self, request):
        context = super().get_context(request)
        context["places"] = NearbyPlace.objects.filter(is_published=True)
        return context


class FaqPage(Page):
    """Страница вопросов. Берёт весь справочник, а не только отмеченное
    для главной."""

    intro = models.CharField("Вступление", max_length=255, blank=True)

    content_panels = Page.content_panels + [FieldPanel("intro")]
    max_count = 1

    class Meta:
        verbose_name = "Страница «Ответы на вопросы»"

    def get_context(self, request):
        context = super().get_context(request)
        context["faq"] = FaqItem.objects.filter(is_published=True)
        return context


class GalleryPage(Page):
    """Фотогалерея. Отдельный набор фото, не тот, что на главной."""

    intro = models.CharField("Вступление", max_length=255, blank=True)
    body = RichTextField("Текст", blank=True, features=BODY_FEATURES)

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
        FieldPanel("body"),
        InlinePanel("photos", label="Фотографии"),
    ]
    max_count = 1

    class Meta:
        verbose_name = "Страница «Галерея»"


class GalleryPhoto(Orderable):
    page = ParentalKey(GalleryPage, on_delete=models.CASCADE, related_name="photos")
    image = models.ForeignKey(
        "wagtailimages.Image", verbose_name="Фото",
        on_delete=models.CASCADE, related_name="+",
    )
    alt = models.CharField("Описание фото", max_length=200, blank=True)
    is_large = models.BooleanField("Крупная плитка", default=False)

    panels = [FieldPanel("image"), FieldPanel("alt"), FieldPanel("is_large")]

    class Meta(Orderable.Meta):
        verbose_name = "Фото"
        verbose_name_plural = "Фотографии"
