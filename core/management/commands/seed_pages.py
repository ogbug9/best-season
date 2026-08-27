"""Создание структуры страниц сайта.

Зачем командой, а не руками в админке: страниц по карте сайта двенадцать,
у каждой свой тип, а у Amvera нет консоли — разовые команды вызываются из
run.py при старте контейнера.

Команда идемпотентна: страница создаётся только если её ещё нет по слагу.
Существующие страницы НЕ трогаются — ни текст, ни настройки, ни порядок.
Значит её безопасно оставить в run.py: на каждом деплое она просто
досоздаёт то, чего не хватает.

Тексты — заглушки, помеченные как заглушки. Их место займёт то, что
пришлёт заказчик (п. 4.6 ТЗ). Пустая страница на созвоне выглядит хуже,
чем страница с честной пометкой «текст заказчика».
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from wagtail.models import Page

PLACEHOLDER = "Текст ожидается от заказчика."


def rich(*paragraphs):
    return "".join(f"<p>{p}</p>" for p in paragraphs)


# Дерево страниц по карте сайта из макета COMPONENTS.
# Формат: (модуль.Модель, слаг, заголовок, поля, [дети])
TREE = [
    (
        "houses.HouseIndexPage",
        "razmeshchenie",
        "Наши домики",
        {"intro": "Четыре дома на берегу, каждый со своей баней или камином."},
        [],
    ),
    (
        "core.TerritoryPage",
        "territoriya",
        "Территория",
        {
            "intro": "Что есть на территории глэмпинга.",
            "body": rich(
                "Территория фермы — это не только дома. "
                + PLACEHOLDER
            ),
        },
        [
            (
                "core.NearbyPage",
                "interesnoe-ryadom",
                "Интересное рядом",
                {"intro": "Куда съездить и что посмотреть в округе."},
                [],
            ),
            (
                "services.ServicesPage",
                "uslugi",
                "Дополнительные услуги",
                {
                    "intro": "Баня, беседка, завтраки и другие услуги.",
                },
                [],
            ),
            (
                "promotions.PromotionsPage",
                "akcii",
                "Акции",
                {"intro": "Специальные предложения на ближайшие даты."},
                [],
            ),
        ],
    ),
    (
        "core.DirectionsPage",
        "kak-dobratsya",
        "Как добраться",
        {
            "intro": "Дорога занимает около двух часов от Москвы.",
            "car_distance": "уточняется",
            "car_time": "уточняется",
            "car_route": rich(
                "Точный маршрут, ориентиры и съезд с трассы — "
                + PLACEHOLDER
            ),
            "transit_route": rich(
                "Электричка или автобус до станции, дальше трансфер или такси. "
                "Названия станций и время в пути — " + PLACEHOLDER
            ),
            "transfer_price": "уточняется",
            "transfer_note": rich(
                "Трансфер заказывается заранее. Оставьте заявку в форме ниже — "
                "подберём время и назовём точную стоимость."
            ),
        },
        [],
    ),
    (
        "core.ContentPage",
        "o-nas",
        "О нас",
        {
            "intro": "Семейная ферма и глэмпинг на берегу.",
            "body": rich("История фермы и рассказ о хозяевах — " + PLACEHOLDER),
        },
        [
            (
                "core.GalleryPage",
                "galereya",
                "Галерея",
                {"intro": "Фотографии домов, территории и окрестностей."},
                [],
            ),
            (
                "reviews.ReviewsPage",
                "otzyvy",
                "Отзывы",
                {"intro": "Что пишут гости после поездки."},
                [],
            ),
            (
                "core.ContactsPage",
                "kontakty",
                "Контакты",
                {
                    "intro": "Свяжитесь с нами любым удобным способом.",
                    "body": rich(
                        "Контакты и реквизиты берутся из настроек сайта — "
                        "заполните их в разделе «Настройки», и они появятся "
                        "здесь и в подвале одновременно."
                    ),
                },
                [],
            ),
            (
                "core.FaqPage",
                "voprosy",
                "Вопросы и ответы",
                {"intro": "Короткие ответы на частые вопросы гостей."},
                [],
            ),
            (
                "core.ContentPage",
                "partneram",
                "Партнёрам",
                {
                    "intro": "Сотрудничество, съёмки, корпоративные заезды.",
                    "body": rich(PLACEHOLDER),
                },
                [],
            ),
        ],
    ),
]

# Правовые страницы: нужны по разделу 11 ТЗ, но в меню не выводятся —
# ссылки на них стоят в подвале и под чекбоксом согласия.
LEGAL = [
    (
        "politika-konfidencialnosti",
        "Политика конфиденциальности",
        "Текст политики предоставляется заказчиком (п. 4.6 ТЗ). "
        "До этого страница остаётся заглушкой.",
    ),
    (
        "soglasie-na-obrabotku",
        "Согласие на обработку персональных данных",
        "Текст согласия предоставляется заказчиком. Версия текста хранится "
        "вместе с каждой заявкой — раздел 11 ТЗ.",
    ),
]


def get_model(path):
    from django.apps import apps

    app_label, model_name = path.split(".")
    return apps.get_model(app_label, model_name)


class Command(BaseCommand):
    help = "Создаёт недостающие страницы сайта по карте из макета"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Показать, что было бы создано, ничего не записывая",
        )

    def handle(self, *args, **options):
        self.dry = options["dry_run"]
        self.created = 0
        self.skipped = 0

        # Берём корень именно у сайта, а не страницу на фиксированной глубине:
        # глубина зависит от того, как заводили дерево, и на этом легко
        # ошибиться — проверено.
        from wagtail.models import Site

        site = Site.objects.filter(is_default_site=True).first() or Site.objects.first()
        home = site.root_page if site else None
        if home is None:
            self.stderr.write("Главная страница не найдена — нечего заполнять")
            return

        with transaction.atomic():
            self.fix_home(home)
            for node in TREE:
                self.create_node(home, node)
            self.create_legal(home)

            if self.dry:
                transaction.set_rollback(True)

        self.stdout.write(
            f"Страницы: создано {self.created}, уже было {self.skipped}"
            + (" (пробный запуск, ничего не записано)" if self.dry else "")
        )

    def fix_home(self, home):
        """Wagtail создаёт главную с названием «Home» — оно и печатается
        огромными буквами на первом экране, пока редактор не заполнит
        заголовок. Подставляем осмысленный текст, но только если поле
        всё ещё в заводском состоянии: свой заголовок не перетираем.
        """
        page = home.specific
        if not hasattr(page, "hero_title"):
            return

        changed = False
        if page.title in ("Home", "Домашняя страница", "Homepage"):
            page.title = "Лучший Сезон"
            changed = True
        if not page.hero_title:
            page.hero_title = "Глэмпинг на берегу, в двух часах от города"
            changed = True
        if not page.hero_subtitle:
            page.hero_subtitle = (
                "Четыре дома с панорамными окнами, баней и камином — "
                "для отдыха вдвоём и с семьёй."
            )
            changed = True

        if changed and not self.dry:
            page.save()
            page.save_revision().publish()
            self.stdout.write("  главная: заполнены заголовок и подзаголовок")

    def create_node(self, parent, node):
        model_path, slug, title, fields, children = node
        page = self.ensure(parent, get_model(model_path), slug, title, fields)
        for child in children:
            self.create_node(page, child)

    def create_legal(self, home):
        model = get_model("core.ContentPage")
        for slug, title, text in LEGAL:
            self.ensure(
                home,
                model,
                slug,
                title,
                {"body": rich(text), "show_booking_cta": False},
                in_menu=False,
            )

    def ensure(self, parent, model, slug, title, fields, in_menu=True):
        """Создаёт страницу, если её ещё нет. Существующую не трогает."""
        existing = model.objects.filter(slug=slug).first()
        if existing is not None:
            self.skipped += 1
            return existing

        # Слаг может быть занят страницей другого типа — тогда создавать
        # вторую с тем же адресом нельзя, Wagtail просто не даст.
        if Page.objects.filter(slug=slug).exists():
            self.stderr.write(f"Адрес «{slug}» уже занят другой страницей, пропускаю")
            self.skipped += 1
            return Page.objects.get(slug=slug)

        page = model(title=title, slug=slug, show_in_menus=in_menu, **fields)
        parent.add_child(instance=page)
        # Без publish страница осталась бы черновиком и на сайте не появилась —
        # на этом мы уже спотыкались.
        page.save_revision().publish()
        self.created += 1
        self.stdout.write(f"  создана: {title} (/{slug}/)")
        return page
