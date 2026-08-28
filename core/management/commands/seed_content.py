"""Наполнение справочников и главной текстами из макета.

Зачем: блоки главной выводятся только при наличии данных — пустой
справочник означает, что секции на странице просто нет. Пока заказчик
не прислал свои тексты (п. 4.6 ТЗ), сайт выглядел бы наполовину пустым.

Тексты и заголовки взяты из макета Figma, то есть это не выдумка, а то,
что дизайнер уже согласовал. Абзацы, которые в макете не читаются,
помечены как ожидающие текста заказчика.

Команда идемпотентна: запись создаётся только если её ещё нет по
названию. Существующие записи не трогаются, поэтому её безопасно
вызывать при каждом старте контейнера.
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from wagtail.models import Site

PLACEHOLDER = "Текст ожидается от заказчика."

TERRITORY = [
    ("Батут и детская площадка", "", True),
    ("Игровая зона", "", False),
    ("Спортивные игры", "", False),
    ("Контактная ферма", "", False),
    ("Русская баня", "", False),
    ("Финская сауна", "", False),
    ("Фотосессии", "", False),
    ("Река «Снежка»", "", False),
    ("Большая беседка", "", False),
    ("Мастер-классы", "", False),
]

NEARBY = [
    (
        "Усадьба «Поленово»",
        "В 15 км от нас — усадьба художника Василия Поленова: "
        "дом-музей, парк и виды на Оку. " + PLACEHOLDER,
    ),
    (
        "Деревня Ф. Конюхова",
        "Деревня путешественника Фёдора Конюхова с часовней и "
        "мастерскими. " + PLACEHOLDER,
    ),
    (
        "Деревня «Бехово»",
        "Смотровая площадка над Окой и церковь Троицы — одно из самых "
        "красивых мест в округе. " + PLACEHOLDER,
    ),
]

FAQ = [
    (
        "Как добраться до глэмпинга?",
        "Около двух часов на машине от Москвы. Подробный маршрут, "
        "электрички и трансфер — на странице «Как добраться».",
    ),
    (
        "Какие условия бронирования и отмены?",
        "Бронь подтверждается после предоплаты. Условия отмены — "
        "на странице «Правила бронирования». " + PLACEHOLDER,
    ),
    (
        "Есть ли завтраки?",
        PLACEHOLDER,
    ),
    (
        "Можно ли кормить животных глэмпинга?",
        "На контактной ферме — да, корм выдаём мы. " + PLACEHOLDER,
    ),
    (
        "Можно ли с животными?",
        "Да, с питомцами можно. Условия уточняйте при бронировании.",
    ),
    (
        "Можно ли арендовать домик на месяц или больше?",
        "Да, длительное проживание обсуждается отдельно. " + PLACEHOLDER,
    ),
]

HOUSES = [
    ("Первый домик", "Стильный лофт с панорамным окном и камином", 6000, 4, 42),
    ("Второй домик", "Стильный лофт с панорамным окном и камином", 6000, 4, 42),
    ("Третий домик", "Стильный лофт с панорамным окном и баней", 6000, 4, 42),
    ("Четвёртый домик", "Стильный лофт с панорамным окном и баней", 6000, 4, 42),
]

HOME_TEXT = {
    "about_title": "О нас",
    "about_text": (
        "<p>Лучший сезон — это место, куда приезжают, чтобы побыть вместе. "
        "Мы любим встречать утро на террасе с ароматным кофе и близкими, "
        "днём гулять, изучая лесные тропы зверей, а вечером собираемся "
        "у бани с ужином и разговорами.</p>"
        "<p>Территория окружена плотным лесным массивом, рядом — река "
        "и открытые поля. Здесь тихо настолько, что слышно, как "
        "просыпается лес. " + PLACEHOLDER + "</p>"
    ),
    # Текст цитаты в макете не читается — ставим осмысленную заглушку
    # в той же интонации, заменить на реальный отзыв при получении.
    "quote_text": (
        "Приехали на выходные и поняли, что здесь можно просто ничего "
        "не делать. Оказалось, это лучшее, что случилось с нами за год."
    ),
    "quote_author": "Из отзыва гостя",
    "slogan": "Не ждите подходящего момента, ваш лучший сезон уже начался",
    "territory_lead": "Большой лесной массив для уединённого отдыха",
    "territory_more_label": "Больше развлечений и услуг в глэмпинге",
    "nearby_more_label": "Больше интересных мест рядом",
    "gallery_title": "Фотогалерея",
    "gallery_text": (
        "Копилка ваших самых счастливых дней: неторопливые прогулки, "
        "знакомство с животными фермы, вечер у огня и чашка чая."
    ),
    # Отдельного блока «Как добраться» на главной в макете нет — поля
    # намеренно не заполняем, шаблон тогда секцию не выводит. Сама
    # страница и ссылки на неё остаются (п. 4.2 ТЗ).
}


class Command(BaseCommand):
    help = "Наполняет справочники и главную текстами из макета"

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        self.dry = options["dry_run"]
        self.created = 0

        with transaction.atomic():
            self.fill_snippets()
            self.fill_houses()
            self.fill_home()
            if self.dry:
                transaction.set_rollback(True)

        self.stdout.write(f"Контент: создано записей {self.created}")

    # ---------- справочники ----------

    def fill_snippets(self):
        from core.models import FaqItem, NearbyPlace, TerritoryItem

        for order, (title, text, large) in enumerate(TERRITORY, start=1):
            if TerritoryItem.objects.filter(title=title).exists():
                continue
            if not self.dry:
                TerritoryItem.objects.create(
                    title=title, description=text, is_large=large,
                    sort_order=order * 10, is_published=True,
                )
            self.mark(f"территория: {title}")

        for order, (title, text) in enumerate(NEARBY, start=1):
            if NearbyPlace.objects.filter(title=title).exists():
                continue
            if not self.dry:
                NearbyPlace.objects.create(
                    title=title, description=text,
                    sort_order=order * 10, is_published=True,
                )
            self.mark(f"рядом: {title}")

        for order, (question, answer) in enumerate(FAQ, start=1):
            if FaqItem.objects.filter(question=question).exists():
                continue
            if not self.dry:
                FaqItem.objects.create(
                    question=question, answer=answer,
                    sort_order=order * 10, is_published=True,
                )
            self.mark(f"вопрос: {question}")

    # ---------- дома ----------

    def fill_houses(self):
        from houses.models import HouseIndexPage, HousePage

        index = HouseIndexPage.objects.first()
        if index is None:
            return

        for order, (title, desc, price, capacity, area) in enumerate(HOUSES, start=1):
            if HousePage.objects.filter(title=title).exists():
                continue
            if self.dry:
                self.mark(f"дом: {title}")
                continue
            page = HousePage(
                title=title,
                slug=f"domik-{order}",
                short_description=desc,
                price_from=price,
                capacity=capacity,
                area=area,
                show_in_menus=False,
            )
            index.add_child(instance=page)
            page.save_revision().publish()
            self.mark(f"дом: {title}")

    # ---------- главная ----------

    def fill_home(self):
        site = Site.objects.filter(is_default_site=True).first() or Site.objects.first()
        if site is None:
            return
        home = site.root_page.specific

        changed = False
        for field, value in HOME_TEXT.items():
            if not hasattr(home, field):
                continue
            if getattr(home, field):
                # Своё уже заполнено — не перетираем.
                continue
            setattr(home, field, value)
            changed = True

        # Ссылки «подробнее» ведут на реальные страницы, если они заведены.
        from wagtail.models import Page

        links = {
            "about_page": "o-nas",
            "territory_more_page": "territoriya",
            "nearby_more_page": "interesnoe-ryadom",
            "gallery_page": "galereya",
            "hero_cta_page": "razmeshchenie",
        }
        for field, slug in links.items():
            if not hasattr(home, field) or getattr(home, field) is not None:
                continue
            page = Page.objects.filter(slug=slug).first()
            if page is not None:
                setattr(home, field, page)
                changed = True

        if changed and not self.dry:
            home.save()
            home.save_revision().publish()
            self.mark("главная: тексты и ссылки")

    def mark(self, what):
        self.created += 1
        self.stdout.write(f"  {what}")
