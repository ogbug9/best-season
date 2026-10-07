from django.db import models
from django.utils.html import strip_tags
from modelcluster.fields import ParentalKey
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.contrib.settings.models import BaseSiteSetting, register_setting
from wagtail.fields import RichTextField, StreamField
from wagtail.models import Orderable, Page
from wagtail.snippets.models import register_snippet
from .content_blocks import AboutContentBlock, LEGAL_BLOCKS

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
    # Иконки карточек-фактов и блока брони на странице дома
    ("capacity", "Вместимость"),
    ("guest", "Гость"),
    ("calendar", "Календарь"),
    ("camera", "Фотоаппарат"),
    ("area", "Площадь"),
    ("layout", "Планировка"),
    ("sofa_bed", "Диван-кровать"),
    ("bunk_bed", "Двухэтажная кровать"),
    ("moon", "Ночи"),
]


@register_snippet
class AmenityGroup(models.Model):
    """Группа удобств: «Кухня», «Сауна», «Внешняя территория» и т.д.

    Раньше это был закрытый TextChoices на пять значений. В макете
    развёрнутого описания групп восемь, и набор явно продолжит расти —
    держать его в коде значит гонять миграцию ради каждой строчки,
    поэтому группы заведены справочником.
    """

    name = models.CharField("Название", max_length=80, unique=True)
    # Колонка развёрнутого описания. В макете раскладка жёсткая — три
    # колонки по 320 с разной высотой, и автоматическая разбивка её не
    # повторяет: браузер выравнивает колонки по высоте и переносит
    # группы не туда. Поэтому колонку выбирает редактор.
    column = models.PositiveSmallIntegerField(
        "Колонка в развёрнутом описании",
        choices=[(1, "Первая"), (2, "Вторая"), (3, "Третья")],
        default=1,
    )
    sort_order = models.PositiveSmallIntegerField("Порядок", default=100)

    panels = [FieldPanel("name"), FieldPanel("column"), FieldPanel("sort_order")]

    class Meta:
        verbose_name = "Группа удобств"
        verbose_name_plural = "Группы удобств"
        ordering = ["sort_order", "name"]

    def __str__(self):
        return self.name


@register_snippet
class Amenity(models.Model):
    """Элемент блока «Что входит» (п. 4.1.5 ТЗ).

    Вынесен в справочник, чтобы одни и те же удобства переиспользовались
    на всех домах и редактор не набирал их текстом заново на каждой странице.
    """

    name = models.CharField("Название", max_length=80)
    group = models.ForeignKey(
        AmenityGroup,
        verbose_name="Группа",
        null=True,
        on_delete=models.PROTECT,
        related_name="amenities",
    )
    # Плитки-теги в блоке «Удобства» на странице дома — короткий список
    # главного. Остальное уходит в развёрнутое описание ниже, иначе
    # блок из восьми групп встал бы на первый экран.
    is_featured = models.BooleanField(
        "Показывать плиткой в «Удобствах»",
        default=False,
        help_text="Короткий список главного над развёрнутым описанием.",
    )
    # Флаги независимы: на макете «Телевизор» и «Кондиционер» стоят и
    # плиткой, и в списке, а «Большая терраса» — только плиткой, потому
    # что в списке то же самое названо «Крытая терраса 24 м²».
    in_list = models.BooleanField(
        "Показывать в развёрнутом описании",
        default=True,
        help_text="Снимите, если плитка дублирует пункт списка другим названием.",
    )
    icon = models.CharField("Иконка", max_length=32, choices=ICON_CHOICES, blank=True)
    sort_order = models.PositiveSmallIntegerField("Порядок", default=100)
    # Порядок плиток свой: в списке «Умная колонка Алиса» одиннадцатая
    # по Кухне, а плиткой стоит шестой. Одним полем это не выразить.
    featured_order = models.PositiveSmallIntegerField(
        "Порядок среди плиток", default=100
    )

    panels = [
        FieldPanel("name"),
        FieldPanel("group"),
        FieldPanel("is_featured"),
        FieldPanel("featured_order"),
        FieldPanel("in_list"),
        FieldPanel("icon"),
        FieldPanel("sort_order"),
    ]

    class Meta:
        verbose_name = "Удобство"
        verbose_name_plural = "Удобства"
        ordering = ["group__sort_order", "group__name", "sort_order", "name"]

    def __str__(self):
        return f"{self.group} — {self.name}" if self.group_id else self.name


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

    work_hours = models.CharField(
        "Часы работы", max_length=64, blank=True, help_text="Например: 10:00 — 22:00"
    )

    telegram_url = models.URLField("Telegram", blank=True)
    # Канал — для подписки; сообщения гости пишут администратору (07.10).
    telegram_chat_url = models.URLField(
        "Telegram для сообщений", blank=True,
        help_text="Чат администратора, например https://t.me/BestSeason_adm. Пусто — используется ссылка Telegram выше.",
    )
    whatsapp_url = models.URLField("WhatsApp", blank=True)
    vk_url = models.URLField("ВКонтакте", blank=True)
    tiktok_url = models.URLField("TikTok", blank=True)
    # Instagram принадлежит Meta, признанной в РФ экстремистской организацией.
    # Рядом со ссылкой обязана стоять сноска — она в подвале выводится
    # автоматически, как только заполнено это поле.
    instagram_url = models.URLField("Instagram", blank=True)

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
    # Подписи под счётчиками гостей на странице дома. Условия размещения
    # одинаковы для всех домиков, поэтому живут в настройках сайта,
    # а не повторяются в каждой странице.
    guests_adults_note = models.CharField(
        "Подпись у счётчика «Взрослые»", max_length=120, blank=True,
        default="Возраст от 7 лет",
    )
    guests_children_note = models.CharField(
        "Подпись у счётчика «Дети»", max_length=120, blank=True,
        default="Бесплатно до 7 лет",
    )
    # --- Надбавки к цене домика (п. 30 правок 09.09) ---
    # Базовая цена своя у каждого домика, а надбавки одинаковые везде,
    # поэтому живут здесь, а не повторяются на четырёх страницах.
    guests_included = models.PositiveSmallIntegerField(
        "Гостей в базовой цене", default=2,
        help_text="Сколько платных гостей входит в цену домика без доплаты.",
    )
    extra_guest_fee = models.PositiveIntegerField(
        "Доплата за гостя сверх базы, ₽/сутки", default=1000,
        help_text="За каждого платного гостя сверх «Гостей в базовой цене».",
    )
    pet_small_fee = models.PositiveIntegerField(
        "Доплата за питомца до 45 см, ₽/сутки", default=1000,
    )
    pet_large_fee = models.PositiveIntegerField(
        "Доплата за питомца выше 45 см, ₽/сутки", default=1500,
    )
    child_free_max_age = models.PositiveSmallIntegerField(
        "Дети бесплатно до возраста включительно", default=7,
        help_text="Ребёнок этого возраста и младше не оплачивается. "
                  "Старше — считается обычным гостем.",
    )
    yandex_metrika_id = models.CharField(
        "Номер счётчика Яндекс.Метрики",
        max_length=16,
        blank=True,
        help_text="Только цифры. Пока пусто — цели бронирования не отправляются.",
    )

    form_reply_time = models.CharField(
        "Срок ответа на заявку", max_length=160, blank=True,
        help_text="например: в течение 30 минут с 9:00 до 21:00",
    )
    booking_show_hourly = models.BooleanField(
        "Показывать баню и беседки в окне бронирования", default=True,
    )
    booking_show_search_fields = models.BooleanField(
        "Показывать даты и гостей над кнопкой бронирования", default=False,
        help_text="Главная и «Размещение». Выбор в самом виджете остаётся доступным.",
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
                FieldPanel("work_hours"),
                FieldPanel("form_reply_time"),
            ],
            heading="Контакты",
        ),
        MultiFieldPanel(
            [
                FieldPanel("telegram_url"),
                FieldPanel("telegram_chat_url"),
                FieldPanel("whatsapp_url"),
                FieldPanel("vk_url"),
                FieldPanel("tiktok_url"),
                FieldPanel("instagram_url"),
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
                FieldPanel("booking_show_hourly"),
                FieldPanel("booking_show_search_fields"),
                FieldPanel("guests_adults_note"),
                FieldPanel("guests_children_note"),
                FieldPanel("guests_included"),
                FieldPanel("extra_guest_fee"),
                FieldPanel("pet_small_fee"),
                FieldPanel("pet_large_fee"),
                FieldPanel("child_free_max_age"),
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
    link_url = models.URLField(
        "Ссылка «Подробнее»", blank=True,
        help_text="Адрес страницы карточки. Пусто — кнопка не показывается.",
    )
    is_large = models.BooleanField(
        "Крупная плитка", default=False,
        help_text="Не используется в блоке «Наша территория»: по замерам "
                  "макета все плитки там строго квадратные, 295×295.",
    )
    spacer_before = models.BooleanField(
        "Пустая ячейка перед этим блоком", default=False,
        help_text="В макете мозаика намеренно разрежена — две ячейки "
                  "оставлены пустыми. Отметьте, чтобы сдвинуть этот блок "
                  "на одну ячейку вправо.",
    )
    GROUPS = [("kids", "С детьми и животными"), ("warm", "Тепло и пар"), ("water", "Вода и события")]
    group = models.CharField("Группа на странице «Территория»", max_length=8, choices=GROUPS, blank=True)
    is_published = models.BooleanField("Показывать на сайте", default=True)
    sort_order = models.PositiveSmallIntegerField("Порядок", default=100)

    panels = [
        FieldPanel("title"),
        FieldPanel("image"),
        FieldPanel("description"),
        FieldPanel("link_url"),
        FieldPanel("group"),
        FieldPanel("spacer_before"),
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
    # Страница «Интересное рядом» (docs/dop-stranicy/12-interesnoe-ryadom.md);
    # на главной эти поля не выводятся.
    SEASONS = [("spring", "Весна"), ("summer", "Лето"), ("autumn", "Осень"), ("winter", "Зима")]
    distance_label = models.CharField("Расстояние", max_length=40, blank=True, help_text="Например: 3 км или ≈30 мин на машине.")
    seasons = models.CharField(
        "Сезоны", max_length=40, blank=True,
        help_text="Через пробел: spring summer autumn winter. Пусто — круглый год.",
    )
    tags = models.CharField("Метки", max_length=120, blank=True, help_text="Через запятую, например: с детьми.")
    route_url = models.URLField("Маршрут", blank=True, help_text="Пусто — маршрут в Яндекс Картах строится по названию.")
    is_published = models.BooleanField("Показывать на сайте", default=True)
    sort_order = models.PositiveSmallIntegerField("Порядок", default=100)

    panels = [
        FieldPanel("title"),
        FieldPanel("image"),
        FieldPanel("description"),
        FieldPanel("link_url"),
        MultiFieldPanel([FieldPanel("distance_label"), FieldPanel("seasons"), FieldPanel("tags"), FieldPanel("route_url")],
                        heading="Страница «Интересное рядом»"),
        FieldPanel("is_published"),
        FieldPanel("sort_order"),
    ]

    @property
    def season_codes(self):
        codes = [code for code in self.seasons.split() if code in dict(self.SEASONS)]
        return codes or [code for code, _ in self.SEASONS]

    @property
    def tag_list(self):
        return [tag.strip() for tag in self.tags.split(",") if tag.strip()]

    @property
    def route_link(self):
        from urllib.parse import quote
        return self.route_url or f"https://yandex.ru/maps/?rtext=~{quote(self.title)}"

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
    TOPICS = [
        ("booking", "Бронь и оплата"),
        ("checkin", "Заезд"),
        ("houses", "Домики"),
        ("pets", "Животные"),
        ("road", "Дорога"),
        ("promo", "Акции"),
    ]
    topic = models.CharField("Тема", max_length=16, choices=TOPICS, blank=True,
                             help_text="Чип-фильтр на странице «Ответы на вопросы».")
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
        FieldPanel("topic"),
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
    """Страница согласия на обработку ПД для ссылки под чекбоксом.

    Ищется по слагу, а не хранится настройкой: так редактору не нужно
    ничего связывать вручную, а если страницы ещё нет — ссылка просто
    не выводится, форма продолжает работать.
    """
    from wagtail.models import Page

    return Page.objects.live().filter(slug="soglasie-na-obrabotku").first()


# =========================================================================
# Страницы второй очереди вёрстки (Фаза 6)
#
# Все типы страниц описаны структурными полями, а не свободным StreamField:
# по п. 8 ТЗ редактор физически не должен уметь сломать вёрстку. Он правит
# содержимое, а порядок и оформление блоков задаёт шаблон.
# =========================================================================


class ArchivePhotoImport(models.Model):
    """Последняя импортированная версия; позволяет сохранять замену редактора."""
    source_key = models.CharField(max_length=500, unique=True)
    sha256 = models.CharField(max_length=64)
    image = models.ForeignKey('wagtailimages.Image', null=True, on_delete=models.SET_NULL, related_name='+')


@register_snippet
class Event(models.Model):
    """Событие для страницы «Мероприятия» (docs/dop-stranicy/18).

    Ближайшие показываются лентой с записью, прошедшие сами уходят в
    «Как это было» на следующий день после окончания.
    """

    title = models.CharField("Название", max_length=120)
    date = models.DateField("Дата")
    end_date = models.DateField("Дата окончания", null=True, blank=True, help_text="Для событий на несколько дней.")
    time_label = models.CharField("Время", max_length=40, blank=True, help_text="Например: 13:00 или весь день.")
    description = models.TextField("Описание", blank=True)
    price = models.PositiveIntegerField("Цена, ₽", null=True, blank=True, help_text="Пусто — «стоимость по запросу».")
    places = models.PositiveSmallIntegerField("Мест", null=True, blank=True)
    image = models.ForeignKey("wagtailimages.Image", verbose_name="Фото", null=True, blank=True,
                              on_delete=models.SET_NULL, related_name="+")
    is_published = models.BooleanField("Показывать на сайте", default=True)

    panels = [
        FieldPanel("title"), FieldPanel("date"), FieldPanel("end_date"), FieldPanel("time_label"),
        FieldPanel("description"), FieldPanel("price"), FieldPanel("places"), FieldPanel("image"),
        FieldPanel("is_published"),
    ]

    class Meta:
        ordering = ["date"]
        verbose_name = "Событие"
        verbose_name_plural = "Мероприятия"

    def __str__(self):
        return f"{self.title} ({self.date:%d.%m.%Y})"

    @property
    def last_day(self):
        return self.end_date or self.date


@register_snippet
class VideoClip(models.Model):
    """Ролик для места под видео (docs/dop-stranicy/01-komponenty.md, K3).

    Пока ролика нет, на месте стоит заглушка. Загрузите файл MP4 в
    «Документы», выберите его здесь и место — заглушка сменится сама:
    обложка остаётся, видео грузится только по нажатию.
    """

    SLOTS = [
        ("territory-walk", "Территория: прогулка по глэмпингу"),
        ("directions-road", "Как добраться: последний километр и въезд"),
        ("gallery-morning-1", "Галерея: «Утреннее» 1"),
        ("gallery-morning-2", "Галерея: «Утреннее» 2"),
        ("gallery-morning-3", "Галерея: «Утреннее» 3"),
        ("group-evening", "Выезды компаний: вечер в полном составе"),
        ("scenario-day", "Чем заняться: один день в «Лучшем сезоне»"),
    ]
    slot = models.CharField("Место на сайте", max_length=32, choices=SLOTS, unique=True)
    file = models.ForeignKey("wagtaildocs.Document", verbose_name="Файл видео (MP4)", on_delete=models.PROTECT, related_name="+")
    poster = models.ForeignKey("wagtailimages.Image", verbose_name="Обложка", null=True, blank=True,
                               on_delete=models.SET_NULL, related_name="+")
    title = models.CharField("Подпись", max_length=120, blank=True)
    is_published = models.BooleanField("Показывать на сайте", default=True)

    panels = [FieldPanel("slot"), FieldPanel("file"), FieldPanel("poster"), FieldPanel("title"), FieldPanel("is_published")]

    class Meta:
        verbose_name = "Видео"
        verbose_name_plural = "Видео на сайте"

    def __str__(self):
        return self.get_slot_display()


class ChannelPost(models.Model):
    """Превью последних постов канала Telegram для «Рассылки» (docs/dop-stranicy/20).

    Заполняется командой fetch_telegram_preview из публичной страницы t.me/s/…;
    вручную не редактируется.
    """

    url = models.URLField(unique=True)
    published_at = models.DateTimeField()
    text = models.TextField(blank=True)
    image_url = models.URLField(blank=True, max_length=500)

    class Meta:
        ordering = ["-published_at"]
        verbose_name = "Пост канала"
        verbose_name_plural = "Посты канала"

    def __str__(self):
        return self.url

    @property
    def first_line(self):
        line = next((part.strip() for part in self.text.splitlines() if part.strip()), "")
        return line if len(line) <= 140 else line[:139].rstrip() + "…"


@register_snippet
class InterfaceText(models.Model):
    key = models.CharField(max_length=120, unique=True, editable=False)
    label = models.CharField('Где используется', max_length=255, editable=False)
    text = models.TextField('Текст (без HTML и стилей)', blank=True)
    panels = [FieldPanel('text')]

    class Meta:
        verbose_name = 'Подпись интерфейса'
        verbose_name_plural = 'Подписи интерфейса'
        ordering = ['label']

    def __str__(self):
        return self.label


def image_titled(title):
    """Изображение из библиотеки по точному названию; None, если его нет."""
    from wagtail.images import get_image_model
    return get_image_model().objects.filter(title=title).first()


def home_hero_image():
    """Первый кадр первого экрана главной — временный фон «О нас» и заглушек (06.10)."""
    from home.models import HomeSlide
    slide = (HomeSlide.objects.filter(page__live=True, image__isnull=False)
             .select_related("image").order_by("page_id", "sort_order").first())
    return slide.image if slide else None


class InProgressMixin(models.Model):
    """Плашка «Раздел дополняется»: страница живая, но ещё растёт.

    Пока галочка стоит, гость видит плашку со ссылками на мессенджеры,
    а поисковики не индексируют страницу (docs/dop-stranicy/01-komponenty.md, K1).
    """

    in_progress = models.BooleanField(
        "Раздел дополняется", default=False,
        help_text="Показать плашку «Раздел дополняется» и закрыть страницу от поисковиков, пока она не готова.",
    )

    settings_panels = Page.settings_panels + [FieldPanel("in_progress")]

    class Meta:
        abstract = True


class ContentPage(InProgressMixin, Page):
    """Простая текстовая страница: «О нас», правовые, «Цены и условия»,
    «Партнёрам». Всё, что не требует особой структуры."""

    intro = models.CharField("Короткое вступление", max_length=255, blank=True)
    hero_image = models.ForeignKey(
        "wagtailimages.Image", verbose_name="Фото в шапке страницы",
        null=True, blank=True, on_delete=models.SET_NULL, related_name="+",
    )
    body = RichTextField("Текст", blank=True, features=BODY_FEATURES)
    legal_body = StreamField(LEGAL_BLOCKS,
                             blank=True, use_json_field=True, verbose_name='Полный текст документа')
    legal_source_sha256 = models.CharField(max_length=64, blank=True, editable=False)
    about_content = StreamField(
        [('content', AboutContentBlock())],
        blank=True, max_num=1, use_json_field=True, verbose_name='Содержимое «О нас»',
    )
    about_initialized = models.BooleanField(default=False, editable=False)
    show_booking_cta = models.BooleanField(
        "Показывать кнопку бронирования внизу", default=True,
    )

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
        FieldPanel("hero_image"),
        FieldPanel("body"),
        FieldPanel("legal_body"),
        FieldPanel("about_content"),
        FieldPanel("show_booking_cta"),
    ]

    def get_template(self, request, *args, **kwargs):
        from core.dop_pages import TEMPLATES

        if self.slug == "o-nas":
            return "core/about_page.html"
        if self.slug in TEMPLATES:
            return TEMPLATES[self.slug]
        return super().get_template(request, *args, **kwargs)

    @property
    def awaiting_copy(self):
        """Текста ещё нет: пусто или служебная пометка из сида — показываем заглушку."""
        from core.dop_pages import TEMPLATES

        if self.slug == "o-nas" or self.slug in TEMPLATES or self.legal_body or self.about_content:
            return False
        text = " ".join(strip_tags(str(self.body or "")).split())
        return not text or "Текст ожидается от заказчика" in text

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        if self.awaiting_copy:
            context["placeholder_image"] = home_hero_image()
        from core.dop_pages import context_for

        context.update(context_for(self, request))
        if self.slug == "o-nas":
            if self.about_content:
                context['about'] = self.about_content[0].value
                context.update(about_pillars=context['about']['pillars'], about_values=context['about']['values'],
                               about_pets=context['about']['pets'], about_diary=context['about']['diary'])
            # 06.10: пока нет ролика, первый экран берёт первый кадр первого экрана главной.
            context["about_hero_image"] = home_hero_image()
            context["about_contacts"] = Page.objects.live().descendant_of(self).filter(slug="kontakty").first()
            contacts = context["about_contacts"]
            # Reuse the CMS map from Contacts, or the approved organisation
            # already linked by the site's FAQ and Yandex reviews.
            context["about_map_embed_url"] = (
                getattr(contacts.specific, "map_embed_url", "") if contacts else ""
            ) or "https://yandex.ru/map-widget/v1/?ol=biz&oid=3306085141&z=16"
        return context

    class Meta:
        verbose_name = "Текстовая страница"
        verbose_name_plural = "Текстовые страницы"


class DirectionsPage(InProgressMixin, Page):
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

    # Шаги на электричке (docs/dop-stranicy/13-kak-dobratsya.md). Если станция
    # заполнена, страница показывает шаги, иначе — текст маршрута выше.
    train_station = models.CharField("Станция", max_length=80, blank=True, help_text="Например: Тарусская.")
    train_time = models.CharField("Время в пути на электричке", max_length=80, blank=True)
    train_price = models.CharField("Стоимость электрички", max_length=80, blank=True)
    train_schedule_url = models.URLField("Ссылка на расписание", blank=True)

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
                FieldPanel("train_station"),
                FieldPanel("train_time"),
                FieldPanel("train_price"),
                FieldPanel("train_schedule_url"),
            ],
            heading="Шаги на электричке",
        ),
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
        context["route_facts"] = self.route_facts()
        return context

    def route_facts(self):
        """Карточки-факты: крупное значение и подпись (K4). Служебные пометки пропускаются."""
        from core.templatetags.content_tags import filled

        facts = []
        distance = filled(self.car_distance)
        if distance:
            value, sep, rest = distance.partition(" от ")
            facts.append((value, f"от {rest}" if sep else "до глэмпинга"))
        if filled(self.car_time):
            facts.append((self.car_time, "на машине"))
        if filled(self.train_price):
            facts.append((self.train_price, "электричка с Курского вокзала"))
        return facts


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
        # «Встретим вас лично» — ответ FAQ про заселение, кадр истории с «О нас».
        context["checkin_answer"] = (FaqItem.objects.filter(is_published=True, question__startswith="Как проходит заселение")
                                     .values_list("answer", flat=True).first())
        context["hosts_image"] = image_titled("BS About story-terrace")
        return context


class TerritoryPage(InProgressMixin, Page):
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
        items = list(TerritoryItem.objects.filter(is_published=True))
        # Тот же запасной адрес, что и в блоке на главной: кнопка есть у
        # каждой карточки, даже если своя ссылка не заведена.
        own_url = self.get_url(request) or ""
        # Страница (docs/dop-stranicy/10-territoriya.md): цена-флажок из услуг
        # с тем же названием, у сауны — переход на Домик №1.
        from services.models import Service
        from wagtail.models import Page

        services = {" ".join(service.name.split()).lower(): service
                    for service in Service.objects.filter(is_published=True)}
        house_one = Page.objects.live().filter(slug="domik-1").first()
        for item in items:
            item.details_url = item.link_url or own_url
            item.details_label = ""
            service = services.get(" ".join(item.title.split()).lower())
            item.service = service if service and service.price else None
            if "сауна" in item.title.lower() and house_one and not item.link_url:
                item.details_url = house_one.get_url(request)
                item.details_label = "Домик №1 с сауной"
        context["territory"] = items
        context["groups"] = [(value, label) for value, label in TerritoryItem.GROUPS
                             if any(item.group == value for item in items)]
        context["aerial"] = image_titled("BS About aerial")
        context["neighbours"] = [image for image in (
            next((item.image for item in items if "ферма" in item.title.lower()), None),
            image_titled("BS About pet-snezhka"), image_titled("BS About pet-dymok"), image_titled("BS About diary-ayka"),
        ) if image]
        context["animals_answer"] = (FaqItem.objects.filter(is_published=True, question__startswith="Можно ли кормить животных")
                                     .values_list("answer", flat=True).first())
        return context


class NearbyPage(InProgressMixin, Page):
    """«Интересное рядом». Карточки из справочника NearbyPlace."""

    intro = models.CharField("Вступление", max_length=255, blank=True)
    body = RichTextField("Текст", blank=True, features=BODY_FEATURES)
    facts = models.TextField(
        "Факты", blank=True,
        help_text="По строке на карточку: значение | подпись. Например: 44 из 170 | деревень мира в списке ООН.",
    )
    day_route = models.TextField(
        "Маршрут на день", blank=True,
        help_text="По строке на точку: время | место | одна строка о нём.",
    )

    content_panels = Page.content_panels + [FieldPanel("intro"), FieldPanel("body"), FieldPanel("facts"), FieldPanel("day_route")]
    max_count = 1

    class Meta:
        verbose_name = "Страница «Интересное рядом»"

    @staticmethod
    def _rows(text, size):
        rows = []
        for line in (text or "").splitlines():
            parts = [part.strip() for part in line.split("|")]
            if parts[0]:
                rows.append(tuple((parts + [""] * size)[:size]))
        return rows

    def get_context(self, request):
        from django.utils import timezone

        context = super().get_context(request)
        month = timezone.localdate().month
        season = ["winter", "winter", "spring", "spring", "spring", "summer",
                  "summer", "summer", "autumn", "autumn", "autumn", "winter"][month - 1]
        places = list(NearbyPlace.objects.filter(is_published=True))
        # Сначала то, что хорошо сейчас; остальное ниже с пометкой «лучше …».
        places.sort(key=lambda place: season not in place.season_codes)
        for place in places:
            place.off_season = season not in place.season_codes
            place.best_label = ", ".join(label.lower() for code, label in NearbyPlace.SEASONS if code in place.season_codes)
        context.update(places=places, season=season, seasons=NearbyPlace.SEASONS,
                       place_facts=self._rows(self.facts, 2), route_points=self._rows(self.day_route, 3))
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
        used = set(context["faq"].values_list("topic", flat=True))
        context["topics"] = [(value, label) for value, label in FaqItem.TOPICS if value in used]
        return context


class GalleryPage(InProgressMixin, Page):
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

    HOUSE_PHOTOS = 6

    def get_context(self, request, *args, **kwargs):
        """Фото галереи и по шесть фото каждого домика (docs/dop-stranicy/14-galereya.md)."""
        from houses.models import HousePage

        context = super().get_context(request, *args, **kwargs)
        items = [{"image": photo.image, "alt": photo.alt, "large": photo.is_large,
                  "category": photo.category or "territory", "season": photo.season, "house": None}
                 for photo in self.photos.select_related("image")]
        for house in HousePage.objects.live().order_by("path"):
            for item in house.gallery_images.select_related("image")[: self.HOUSE_PHOTOS]:
                items.append({"image": item.image, "alt": house.title, "large": False,
                              "category": "houses", "season": "", "house": house})
        used = {item["category"] for item in items}
        context["gallery_items"] = items
        context["gallery_categories"] = [(v, l) for v, l in GalleryPhoto.CATEGORIES if v in used]
        context["gallery_seasons"] = NearbyPlace.SEASONS
        context["telegram_url"] = SiteSettings.for_request(request).telegram_url if request else ""
        return context


class GalleryPhoto(Orderable):
    page = ParentalKey(GalleryPage, on_delete=models.CASCADE, related_name="photos")
    image = models.ForeignKey(
        "wagtailimages.Image", verbose_name="Фото",
        on_delete=models.CASCADE, related_name="+",
    )
    alt = models.CharField("Описание фото", max_length=200, blank=True)
    is_large = models.BooleanField("Крупная плитка", default=False)
    CATEGORIES = [("houses", "Домики"), ("territory", "Территория"), ("animals", "Животные"), ("around", "Окрестности")]
    category = models.CharField("Что на фото", max_length=12, choices=CATEGORIES, blank=True)
    season = models.CharField("Сезон", max_length=8, choices=NearbyPlace.SEASONS, blank=True)

    panels = [FieldPanel("image"), FieldPanel("alt"), FieldPanel("category"), FieldPanel("season"), FieldPanel("is_large")]

    class Meta(Orderable.Meta):
        verbose_name = "Фото"
        verbose_name_plural = "Фотографии"
