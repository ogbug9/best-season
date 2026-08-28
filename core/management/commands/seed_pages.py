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
        "Размещение",
        {"intro": "Четыре дома на берегу, каждый со своей баней или камином."},
        [],
    ),
    (
        "promotions.PromotionsPage",
        "akcii",
        "Акции",
        {"intro": "Специальные предложения на ближайшие даты."},
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
                "core.ContentPage",
                "razvlecheniya",
                "Развлечения",
                {"intro": "Чем занять себя на территории.", "body": rich(PLACEHOLDER)},
                [],
            ),
            (
                "core.ContentPage",
                "chem-zanyatsya",
                "Чем заняться",
                {"intro": "Маршруты, прогулки и активности.", "body": rich(PLACEHOLDER)},
                [],
            ),
            (
                "services.ServicesPage",
                "uslugi",
                "Доп услуги",
                {
                    "intro": "Баня, беседка, завтраки и другие услуги.",
                },
                [],
            ),
            (
                "core.ContentPage",
                "meropriyatiya",
                "Мероприятия",
                {"intro": "Праздники, съёмки, корпоративные заезды.", "body": rich(PLACEHOLDER)},
                [],
            ),
        ],
    ),
    (
        "core.NearbyPage",
        "interesnoe-ryadom",
        "Интересное рядом",
        {"intro": "Куда съездить и что посмотреть в округе."},
        [],
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
        "pravila-bronirovaniya",
        "Правила бронирования",
        "Условия брони, предоплаты и отмены. " + PLACEHOLDER,
    ),
    (
        "vyezdy-kompaniy",
        "Выезды компаний",
        "Корпоративные заезды и мероприятия. " + PLACEHOLDER,
    ),
    (
        "rassylka",
        "Рассылка",
        "Условия информационной рассылки. " + PLACEHOLDER,
    ),
    (
        "oferta",
        "Оферта",
        "Публичная оферта предоставляется заказчиком (п. 4.6 ТЗ).",
    ),
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


# «Как добраться» в макете шапки нет, но по п. 4.2 ТЗ страница обязательна
# и «не может быть сокращена в первой очереди». Поэтому страница есть, а из
# верхнего меню убрана — ссылки на неё стоят в подвале, в компактном блоке
# на страницах домов и в точке входа №8. Расхождение макета с ТЗ — вопрос
# к заказчику, молча выкидывать страницу нельзя.
NOT_IN_MENU = {"kak-dobratsya"}

# Порядок пунктов в шапке — точно как в макете. Ключ None означает верхний
# уровень, остальные ключи — слаги разделов с выпадающими списками.
MENU_ORDER = {
    None: ["razmeshchenie", "akcii", "territoriya", "interesnoe-ryadom", "o-nas"],
    "territoriya": ["razvlecheniya", "chem-zanyatsya", "uslugi", "meropriyatiya"],
    "o-nas": ["galereya", "otzyvy", "kontakty", "voprosy", "partneram"],
}

# Заголовки, под которыми страница могла быть заведена раньше. Переименовываем
# только их: если заказчик назвал страницу по-своему, его вариант не трогаем.
RENAME = {
    "razmeshchenie": (["Наши домики", "Размещение и цены"], "Размещение"),
    "uslugi": (["Дополнительные услуги"], "Доп услуги"),
    "voprosy": (["Вопросы и ответы"], "FAQ"),
}


def walk(nodes):
    """Разворачивает дерево в плоский список — по нему проверяем дубли."""
    for node in nodes:
        yield node
        yield from walk(node[4])


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
            self.hide_duplicates()
            self.order_menu(home)

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

        # Тексты первого экрана взяты из макета: там крупно стоит название
        # бренда, а описание уходит в подзаголовок — не наоборот.
        HERO_TITLE = "Лучший сезон"
        HERO_SUBTITLE = (
            "Мы создаём место, где можно замедлиться, восстановиться "
            "и прожить простые моменты радости в окружении природы, "
            "тепла и настоящей жизни."
        )
        # Заголовки, которые команда писала сама в прошлых версиях. Их
        # перезаписываем, чужой текст — никогда.
        OURS = {"", "Глэмпинг на берегу, в двух часах от города"}
        OURS_SUB = {
            "",
            "Четыре дома с панорамными окнами, баней и камином — "
            "для отдыха вдвоём и с семьёй.",
        }

        changed = False
        if page.title in ("Home", "Домашняя страница", "Homepage"):
            page.title = "Лучший Сезон"
            changed = True
        if page.hero_title in OURS:
            page.hero_title = HERO_TITLE
            changed = True
        if page.hero_subtitle in OURS_SUB:
            page.hero_subtitle = HERO_SUBTITLE
            changed = True

        if changed and not self.dry:
            page.save()
            page.save_revision().publish()
            self.stdout.write("  главная: заполнены заголовок и подзаголовок")

    def order_menu(self, home):
        """Расставляет пункты меню в порядке макета.

        Wagtail отдаёт детей в порядке дерева, поэтому порядок в шапке — это
        порядок страниц в разделе. Переставляем только если он уже не такой:
        каждый move меняет пути в дереве, дёргать его на каждом деплое зря
        не стоит.
        """
        for parent_slug, order in MENU_ORDER.items():
            parent = home if parent_slug is None else Page.objects.filter(slug=parent_slug).first()
            if parent is None:
                continue

            children = list(parent.get_children())
            current = [p.slug for p in children if p.slug in order]
            if current == order:
                continue

            # Каждый move переписывает пути в дереве, поэтому объект нужно
            # перечитывать прямо перед перемещением. На устаревших копиях
            # Wagtail расставляет страницы не туда — проверено.
            ids = {p.slug: p.pk for p in children}
            previous_pk = None
            for slug in order:
                pk = ids.get(slug)
                if pk is None:
                    continue
                if self.dry:
                    previous_pk = pk
                    continue
                page = Page.objects.get(pk=pk)
                if previous_pk is None:
                    page.move(parent, pos="first-child")
                else:
                    page.move(Page.objects.get(pk=previous_pk), pos="right")
                previous_pk = pk

            self.stdout.write(
                f"  порядок меню «{parent.title}»: {' → '.join(order)}"
            )

    def hide_duplicates(self):
        """Убирает из меню лишние копии одиночных страниц.

        Такая копия могла появиться до того, как команда научилась искать
        по типу: в меню было два пункта «Наши домики». Страницу НЕ удаляем —
        только снимаем с публикации и убираем из меню. Действие обратимо,
        а с удалением ошибиться нельзя.

        Оставляем ту копию, у которой есть дочерние страницы, а при равенстве —
        созданную раньше. Пустышку без детей и трогать не жалко.
        """
        seen = set()
        for node in walk(TREE):
            seen.add(node[0])

        for model_path in seen:
            model = get_model(model_path)
            if getattr(model, "max_count", None) != 1:
                continue

            pages = list(model.objects.all().order_by("path"))
            if len(pages) < 2:
                continue

            keep = max(pages, key=lambda p: (p.get_children().count(), -p.pk))
            for page in pages:
                if page.pk == keep.pk or page.get_children().exists():
                    continue
                if not page.show_in_menus and not page.live:
                    continue
                page.show_in_menus = False
                if not self.dry:
                    page.save()
                    page.unpublish()
                self.stdout.write(
                    f"  дубль «{page.title}» (/{page.slug}/) убран из меню, "
                    f"оставлена «{keep.title}» (/{keep.slug}/)"
                )

    def create_node(self, parent, node):
        model_path, slug, title, fields, children = node
        page = self.ensure(
            parent, get_model(model_path), slug, title, fields,
            in_menu=slug not in NOT_IN_MENU,
        )
        self.reconcile(page, parent, slug)
        for child in children:
            self.create_node(page, child)

    def reconcile(self, page, parent, slug):
        """Приводит уже существующую страницу к структуре из макета.

        Только две вещи: родитель и заголовок из списка известных старых
        названий. Тексты, адреса и всё остальное не трогаем — их мог
        поправить заказчик.
        """
        page = page.specific
        changed = False

        old_titles, new_title = RENAME.get(slug, ([], None))
        if new_title and page.title in old_titles:
            page.title = new_title
            changed = True

        want_in_menu = slug not in NOT_IN_MENU
        if page.show_in_menus != want_in_menu:
            page.show_in_menus = want_in_menu
            changed = True

        if changed and not self.dry:
            page.save()
            if page.live:
                page.save_revision().publish()
            self.stdout.write(f"  обновлена: {page.title} (/{page.slug}/)")

        # Перенос в правильный раздел: в макете «Акции» и «Интересное рядом»
        # стоят на верхнем уровне, а не внутри «Территории», куда их положила
        # первая версия этой команды.
        if page.get_parent().pk != parent.pk and not self.dry:
            page.move(parent, pos="last-child")
            self.stdout.write(f"  перенесена: {page.title} → «{parent.title}»")

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

        # Страница такого типа может уже быть заведена вручную под другим
        # адресом. Wagtail проверяет max_count только в админке и молча
        # пропускает программное создание — на этом мы получили в меню два
        # пункта «Наши домики». Для одиночных типов ищем по типу, а не по слагу.
        if getattr(model, "max_count", None) == 1:
            existing = model.objects.first()
            if existing is not None:
                self.skipped += 1
                self.stdout.write(
                    f"  «{existing.title}» уже есть (/{existing.slug}/), вторую не создаю"
                )
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
