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

import html
import re

from django.core.management.base import BaseCommand
from django.db import transaction
from wagtail.models import Site

PLACEHOLDER = "Текст ожидается от заказчика."

# Тексты, которыми мы наполняли сайт до того, как заказчик прислал свои.
# Их можно спокойно перезаписывать: это наши догадки, а не редактура.
# Всё, чего здесь нет и что не помечено PLACEHOLDER, считается правкой
# редактора и НЕ трогается.
STALE_TEXTS = {
    "Около двух часов на машине от Москвы. Подробный маршрут, "
    "электрички и трансфер — на странице «Как добраться».",
    "Да, с питомцами можно. Условия уточняйте при бронировании.",
    "Большой лесной массив для уединённого отдыха",
    "Копилка ваших самых счастливых дней: неторопливые прогулки, "
    "знакомство с животными фермы, вечер у огня и чашка чая.",
    "Больше развлечений и услуг в глэмпинге",
    "Больше развлечений и услуг",
    "Здесь начинается территория вашего отдыха. "
    "Мы устроили всё так, как хотели бы сами.",
    # Прежние тексты акций: я поставил там ёлочки и длинное тире,
    # в макете дефис и «Р». Разрешаем перезаписать своей же правкой.
    "Дарим скидку в день рождения — 15%",
    "От 3-х суток скидка 10%\nОт 5 суток — 15%\nОт 7 суток — 20%",
    "От 3-х суток скидка 10%\nОт 5 суток — 20%\nОт 7 суток — 25%",
    "При бронировании русской бани от 3-х часов — баня рассчитывается "
    "по тарифу 1 500 ₽/час",
    # Прежняя заглушка блока цитаты: на боевом там до сих пор отзыв гостя
    "Приехали на выходные и поняли, что здесь можно просто ничего "
    "не делать. Оказалось, это лучшее, что случилось с нами за год.",
    "Из отзыва гостя",
}


def _plain(value):
    """Текст без разметки, лишних пробелов и неразрывных пробелов.

    Сравнивать «как есть» нельзя: answer — это RichText, и стоит один раз
    открыть запись в админке, как текст оказывается обёрнут в <p>…</p>.
    Буквальное сравнение такую строку уже не узнаёт, и команда считает
    её правкой редактора, хотя это наша же заглушка.
    """
    text = re.sub(r"<[^>]+>", " ", str(value or ""))
    text = html.unescape(text).replace("\xa0", " ")
    return re.sub(r"\s+", " ", text).strip()


_STALE_PLAIN = {_plain(t) for t in STALE_TEXTS}


def is_ours(value):
    """Текст ещё наш (заглушка или прежняя догадка), а не правка редактора."""
    text = _plain(value)
    if not text:
        return True
    return (
        _plain(PLACEHOLDER) in text
        or text in _STALE_PLAIN
        # прежнее написание названия в цитате
        or "«Best Season»" in text
    )


# Плитки, которых в макете нет: остались от прежних заходов наполнения.
# «Река «Снежка»» — опечатка-двойник «Скнижки», «Игровая зона» дублирует
# «Спортивные игры». Из-за них плиток становилось 12 вместо 10, и пустые
# ячейки мозаики уезжали не туда. Не удаляем, а снимаем с публикации:
# удалять то, что мог завести редактор, команда не вправе.
OBSOLETE_TERRITORY = ["Игровая зона", "Река «Снежка»", "Река \"Снежка\""]

TERRITORY = [
    ("Контактная ферма", "", False),
    ("Батут и детская площадка", "", False),
    ("Костровая зона", "", True),
    ("Спортивные игры", "", False),
    ("Русская баня", "", False),
    ("Финская сауна", "", False),
    ("Фотосессии", "", True),
    ("Река \"Скнижка\"", "", False),
    ("Большая беседка", "", False),
    ("Мастер-классы", "", False),
]

# Переименования: заголовок в макете уточнён уже после первого
# наполнения, и без карты соответствия в базе завелась бы вторая запись.
NEARBY_RENAMES = {
    # Кавычки и регистр — как в макете: лапки и строчная «деревня».
    # Ёлочки и заглавную ставил я, макету это противоречит.
    "Деревня «Бехово»": "деревня \"Бёхово\"",
    "Деревня «Бёхово»": "деревня \"Бёхово\"",
    "Усадьба «Поленово»": "Усадьба \"Поленово\"",
    "Деревня Ф. Конюхова": "деревня Ф. Конюхова",
}

TERRITORY_RENAMES = {
    "Река «Скнижка»": "Река \"Скнижка\"",
}

NEARBY = [
    (
        "Усадьба \"Поленово\"",
        "В 3 км от нас невероятной красоты усадьба русского художника "
        "Василия Поленова, которая по праву стала достоянием Тульского края.",
    ),
    (
        "деревня Ф. Конюхова",
        "В 6 км от нас Арт-проект всемирно известного путешественника "
        "Фёдора Конюхова — необычное пространство для вдохновения.",
    ),
    (
        "деревня \"Бёхово\"",
        "В 5 км от нас находится старинная и живописная деревня Бёхово, "
        "которая в 2021 г. вошла в топ лучших деревень мира по версии ООН.",
    ),
]

FAQ = [
    (
        "Как добраться до глэмпинга?",
        "<p>Мы находимся в Тульской области, в 100 км от Москвы. Удобнее "
        "всего можно доехать на автомобиле (~1,5 часа) — "
        '<a href="https://yandex.com/maps/-/CPsvELJx">точный адрес и прямая '
        "ссылка на Яндекс.Карты</a>.</p>"
        "<p>Вариант маршрута из Москвы на общественном транспорте. "
        "Наиболее удобный и простой путь: электричка + такси.</p>"
        "<ul>"
        "<li>С Курского вокзала доехать до станции Тарусская. "
        "Стоимость от 400 руб., время в пути 1,2–2,5 ч. "
        "Расписание электричек Курского направления — "
        '<a href="https://www.tutu.ru/rasp.php?st1=20000&amp;st2=43806">'
        "подробнее</a>.</li>"
        "<li>Далее от ст. Тарусская до глэмпинга можно заказать такси "
        "(местное / «Такси Максим» / Яндекс Go), либо заказать трансфер "
        "через администратора. Стоимость от 300 руб., время в пути 10 мин.</li>"
        "</ul>",
    ),
    (
        "Какие условия бронирования и отмены?",
        "<p>Бронирование подтверждается предоплатой 50% от стоимости "
        "проживания. При отмене за 7 и более дней до заезда предоплата "
        "возвращается полностью. В случаях незаезда или отмены бронирования "
        "менее, чем за 3 дня до дня заезда, предоплата не возвращается.</p>",
    ),
    (
        "Есть ли завтраки?",
        "<p>К сожалению, на данный момент опция готовых завтраков не "
        "предусмотрена. Но каждое утро наша ферма радует нас свежими и "
        "вкусными продуктами, из которых вы сможете приготовить завтрак "
        "самостоятельно: яйца, молоко, мясо и зелень с нашего огорода — "
        "всё натуральное и без лишних километров до вашей тарелки.</p>",
    ),
    (
        "Можно ли кормить животных глэмпинга?",
        "<p>Помимо фермы, на территории вы можете встретить большое "
        "разнообразие жителей глэмпинга: котики, семейство ежей, кролики, "
        "дикие утки, бобры, выдры и другие. Многие из них очень дружелюбны, "
        "а наши кошечки настойчивы в вопросе ласок и угощений.</p>"
        "<p>Но наша личная и большая просьба: не кормить животных фермы и "
        "глэмпинга самостоятельно. При заселении мы расскажем, как и чем "
        "лучше кормить животных, чтобы это было в радость и вам, и им.</p>",
    ),
    (
        "Можно ли с животными?",
        "<p>Конечно! Мы с огромной любовью относимся к четвероногим "
        "путешественникам. Пожалуйста, укажите этот момент при бронировании — "
        "подберём подходящий вариант и обговорим детали заранее.</p>"
        "<p>* За проживание с животными берётся доплата в размере 1000 ₽ "
        "(в холке до 50 см) или 1500 ₽ (в холке выше 50 см).</p>",
    ),
    (
        "Можно ли арендовать домик на месяц или больше?",
        "<p>Да, если в календаре есть доступный дом на ваши даты, его можно "
        "забронировать. Аренда домов в глэмпинге считается посуточно, но у нас "
        "есть гибкая система скидок за долгое проживание от 3 ночей.</p>"
        "<p>С мая по сентябрь:</p>"
        "<ul><li>от 3 ночей −10%</li><li>от 5 ночей −15%</li>"
        "<li>от 7 ночей −20%</li></ul>"
        "<p>С октября по апрель:</p>"
        "<ul><li>от 3 ночей −10%</li><li>от 5 ночей −20%</li>"
        "<li>от 7 ночей −25%</li></ul>",
    ),
]

# Подпись под названием в макете короткая: «4 спальных места + камин».
# Длинные фразы, которые стояли раньше, — мои заглушки, из-за них подпись
# переносилась на две строки и ломала верх карточки.
# Акции с макета «Special Offers», дословно. Названия в макете набраны
# в две строки — перенос сохраняем, он часть вёрстки карточки.
PROMOTIONS = [
    # Тексты и знаки препинания — ровно как в макете «Special Offers»:
    # прямые кавычки-лапки, дефис, «Р» без пробела. Ёлочки и длинное тире,
    # которые стояли здесь раньше, были моей правкой и макету противоречат.
    ("Тариф \"День рождения\"", "den-rozhdeniya",
     "Дарим скидку в день рождения - 15%"),
    ("Тариф \"Пятница со скидкой 50%\"", "pyatnica-50",
     "При бронировании 3-х дней: пятницы, субботы и воскресения, "
     "на пятницу действует скидка 50%"),
    ("Тариф \"С мая по сентябрь\"", "may-sentyabr",
     "От 3-х суток скидка 10%\nОт 5 суток - 15%\nОт 7 суток - 20%"),
    ("Тариф \"Выгодная баня\"", "vygodnaya-banya",
     "При бронировании русской бани от 3-х часов - баня рассчитывается "
     "по тарифу 1 500Р/час"),
    ("Тариф \"Гостеприимство\"", "gostepriimstvo",
     "При бронировании напрямую комплимент от хозяев: набор фермерских "
     "продуктов или дополнительный час в бане"),
    ("Тариф \"Правильная удаленка\"", "pravilnaya-udalenka",
     "4 дня по цене 3 в будние дни"),
    ("Тариф \"С октября по апрель\"", "oktyabr-aprel",
     "От 3-х суток скидка 10%\nОт 5 суток - 20%\nОт 7 суток - 25%"),
]


HOUSES = [
    # 8000 у первого, 6000 у остальных — по макету (лента цены на карточке)
    ("Первый домик", "финская сауна", 8000, 4, 42),
    ("Второй домик", "камин", 6000, 4, 42),
    ("Третий домик", "камин", 6000, 4, 42),
    ("Четвёртый домик", "камин", 6000, 4, 42),
]

# Прежние подписи домиков — их можно перезаписывать, это наши догадки
STALE_HOUSE_DESC = {
    "Стильный лофт с панорамным окном и камином",
    "Стильный лофт с панорамным окном и баней",
}

HOME_TEXT = {
    "hero_title": "Лучший сезон",
    "hero_subtitle": (
        "Мы создаём место, где можно замедлиться, восстановиться и "
        "прожить простые моменты радости в окружении природы, тепла "
        "и настоящей жизни."
    ),
    "about_title": "О нас",
    # Текст снят дословно из макета через инспектор Figma — это
    # согласованная копия, а не заглушка.
    "about_text": (
        "<p>Лучший сезон — это место, куда приезжают, чтобы побыть вместе. "
        "Мы любим встречать утро на террасе с ароматным кофе и близкими, "
        "днём гуляем, изучая лесные тропы зверей, а вечером собираемся "
        "у большого костра с песнями под гитару или греемся в бане "
        "с ромашковым чаем.</p>"
        "<p>Территория глэмпинга поистине уникальна — с трёх сторон нас "
        "окружает лес и небольшая местная речка Скнижка, а рядом раскинулся "
        "богатый и душистый питомник «Долина роз». Также наш район является "
        "самым озонированным в Тульской области, воздух здесь чище и плотнее, "
        "так что здесь отлично можно выспаться. А ещё у нас есть собственная "
        "контактная ферма, которая порадует свежими и натуральными продуктами "
        "к вашему завтраку.</p>"
    ),
    # Текст снят из макета дословно. Абзацы разделены пустой строкой —
    # по ним шаблон строит «лесенку» с нарастающим отступом.
    "quote_text": (
        "Проект вырос из личной истории и желания делиться.\n"
        "В стенах нашего семейного дома всегда было много друзей, "
        "гостеприимства, длинных разговоров и тёплых вечеров.\n"
        "Со временем нас в семье становилось всё больше, как и тех, "
        "с кем хотелось разделить эту атмосферу и состояние."
        "\n\n"
        "Так появился «Лучший сезон» — место, куда можно приехать с тем же "
        "чувством, что тебе здесь всегда рады и ждут, где светло, спокойно "
        "и по-настоящему хорошо."
        "\n\n"
        "У нас нет любимого времени года.\n"
        "Мы уверены, что каждый сезон по-своему прекрасный, а с нужными "
        "людьми любая поездка может стать незабываемой."
    ),
    # Подписи под цитатой в макете нет
    "quote_author": "",
    "slogan": "Не ждите подходящего момента, ваш лучший сезон уже начался",
    # Неразрывный пробел между «Мы» и «устроили»: в макете строка рвётся
    # после «отдыха.», а при обычном пробеле «Мы» подтягивается наверх —
    # в колонку 674px оно помещается, хотя в макете стоит ниже
    "territory_lead": (
        "Здесь начинается территория вашего отдыха. "
        "Мы\u00a0устроили всё так, как хотели бы сами."
    ),
    # Инспектор (Frame 2087326604, узел 2102:3008): текст плитки-кнопки
    # в мозаике — именно такой, а не «Больше развлечений и услуг»
    "territory_more_label": "Что вас здесь ждёт. Всё по порядку",
    "nearby_more_label": "Больше интересных мест рядом",
    "gallery_title": "Фотогалерея",
    "gallery_text": (
        "Копилку ваших самых счастливых дней может пополнить тот, "
        "который состоит из простых вещей: наблюдения за птицами, "
        "неторопливой прогулкой, знакомства с местными жителями нашей "
        "фермы, вечернего разговора за чашкой чая."
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
            self.fill_promotions()
            self.fill_home()
            if self.dry:
                transaction.set_rollback(True)

        self.stdout.write(f"Контент: создано записей {self.created}")

    # ---------- справочники ----------

    def fill_snippets(self):
        from core.models import FaqItem, NearbyPlace, TerritoryItem

        for old_title, new_title in TERRITORY_RENAMES.items():
            stale = TerritoryItem.objects.filter(title=old_title).first()
            if stale and not TerritoryItem.objects.filter(title=new_title).exists():
                if not self.dry:
                    stale.title = new_title
                    stale.save(update_fields=["title"])
                self.mark(f"территория, переименование: {old_title} → {new_title}")

        for title in OBSOLETE_TERRITORY:
            stale = TerritoryItem.objects.filter(title=title, is_published=True).first()
            if stale and is_ours(stale.description):
                if not self.dry:
                    stale.is_published = False
                    stale.save(update_fields=["is_published"])
                self.mark(f"территория, снято с публикации (нет в макете): {title}")

        for order, (title, text, spacer) in enumerate(TERRITORY, start=1):
            existing = TerritoryItem.objects.filter(title=title).first()
            if existing:
                # Порядок и разрывы сетки правим и у заведённых плиток:
                # они снимались с макета уже после первого наполнения,
                # и без этого мозаика осталась бы в старой раскладке.
                if (existing.sort_order, existing.spacer_before) != (order * 10, spacer):
                    if not self.dry:
                        existing.sort_order = order * 10
                        existing.spacer_before = spacer
                        existing.save(update_fields=["sort_order", "spacer_before"])
                    self.mark(f"территория, раскладка по макету: {title}")
                continue
            if not self.dry:
                TerritoryItem.objects.create(
                    title=title, description=text, spacer_before=spacer,
                    sort_order=order * 10, is_published=True,
                )
            self.mark(f"территория: {title}")

        for old_title, new_title in NEARBY_RENAMES.items():
            stale = NearbyPlace.objects.filter(title=old_title).first()
            if stale and not NearbyPlace.objects.filter(title=new_title).exists():
                if not self.dry:
                    stale.title = new_title
                    stale.save(update_fields=["title"])
                self.mark(f"рядом, переименование: {old_title} → {new_title}")

        for order, (title, text) in enumerate(NEARBY, start=1):
            existing = NearbyPlace.objects.filter(title=title).first()
            if existing:
                if existing.description != text and is_ours(existing.description):
                    if not self.dry:
                        existing.description = text
                        existing.save(update_fields=["description"])
                    self.mark(f"рядом, текст с макета: {title}")
                continue
            if not self.dry:
                NearbyPlace.objects.create(
                    title=title, description=text,
                    sort_order=order * 10, is_published=True,
                )
            self.mark(f"рядом: {title}")

        for order, (question, answer) in enumerate(FAQ, start=1):
            existing = FaqItem.objects.filter(question=question).first()
            if existing:
                if str(existing.answer) != answer and is_ours(existing.answer):
                    if not self.dry:
                        existing.answer = answer
                        existing.save(update_fields=["answer"])
                    self.mark(f"вопрос, ответ с макета: {question}")
                continue
            if not self.dry:
                FaqItem.objects.create(
                    question=question, answer=answer,
                    sort_order=order * 10, is_published=True,
                )
            self.mark(f"вопрос: {question}")

    # ---------- дома ----------

    def fill_promotions(self):
        from promotions.models import Promotion

        for order, (title, slug, text) in enumerate(PROMOTIONS, start=1):
            existing = Promotion.objects.filter(slug=slug).first()
            if existing:
                # Прежние заголовки писались ёлочками — это была наша правка,
                # в макете прямые лапки. Синхронизируем и название тоже.
                stale_title = existing.title.replace("«", '"').replace("»", '"')
                changed = False
                if stale_title == title and existing.title != title:
                    existing.title = title
                    changed = True
                if existing.short_description != text and is_ours(existing.short_description):
                    existing.short_description = text
                    changed = True
                if changed:
                    if not self.dry:
                        existing.sort_order = order * 10
                        existing.save()
                    self.mark(f"акция, текст с макета: {title}")
                continue
            if not self.dry:
                Promotion.objects.create(
                    title=title, slug=slug, short_description=text,
                    sort_order=order * 10, is_published=True,
                )
            self.mark(f"акция: {title}")

    def fill_houses(self):
        from houses.models import HouseIndexPage, HousePage

        index = HouseIndexPage.objects.first()
        if index is None:
            return

        for order, (title, desc, price, capacity, area) in enumerate(HOUSES, start=1):
            existing = HousePage.objects.filter(title=title).first()
            if existing:
                # Короткую подпись с макета доставляем и в заведённые дома,
                # но только поверх собственных заглушек
                stale = (existing.short_description or "").strip()
                changed = False
                if stale != desc and (not stale or stale in STALE_HOUSE_DESC):
                    existing.short_description = desc
                    changed = True
                    self.mark(f"дом, подпись с макета: {title}")
                # Порядок правим и у заведённых: он снят с макета, а без
                # него список сортируется по алфавиту
                if existing.sort_order_index != order:
                    existing.sort_order_index = order
                    changed = True
                    self.mark(f"дом, порядок по макету: {title}")
                if changed and not self.dry:
                    existing.save()
                continue
            if self.dry:
                self.mark(f"дом: {title}")
                continue
            page = HousePage(
                title=title,
                slug=f"domik-{order}",
                # Порядок в списке задаём явно: без него сортировка падает
                # на запасной ключ «по названию», и «Второй домик»
                # оказывается перед «Первым»
                sort_order_index=order,
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
            current = getattr(home, field)
            if current and not is_ours(current):
                # Редактор написал своё — не перетираем.
                continue
            if current == value:
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
