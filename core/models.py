from django.db import models
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.contrib.settings.models import BaseSiteSetting, register_setting
from wagtail.fields import RichTextField
from wagtail.snippets.models import register_snippet

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
            ],
            heading="Адрес",
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
    ]

    class Meta:
        verbose_name = "Настройки сайта"
