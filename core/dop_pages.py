"""Наполнение доп. страниц на ContentPage (docs/dop-stranicy/18–20).

Факты — с сайта (FAQ, карточки, услуги) и из соцсетей «Лучшего сезона»;
источник указан у каждого блока. Тексты здесь — стартовые: если редактор
заполнит у страницы поле «Текст», он выводится над этими блоками.
Фото берутся только из уже загруженных изображений.
"""

TEMPLATES = {
    "chem-zanyatsya": "core/dop/chem_zanyatsya.html",
    "razvlecheniya": "core/dop/razvlecheniya.html",
    "meropriyatiya": "core/dop/meropriyatiya.html",
    "vyezdy-kompaniy": "core/dop/vyezdy.html",
    "partneram": "core/dop/partneram.html",
    "pravila-bronirovaniya": "core/dop/pravila.html",
    "rassylka": "core/dop/rassylka.html",
}

# 09.10: временные страницы питомцев, дневника и услуг (core/temp_pages.py).
from core.temp_pages import TEMPLATES as _TEMP_TEMPLATES  # noqa: E402

TEMPLATES.update(_TEMP_TEMPLATES)

# Сценарии, кубик, дождь и «Что взять» «Чем заняться» — core/things_content.py (макет 25.10).

# Развлечения: метки плиток по названию (бесплатно/платно, детям, в дождь).
ACTIVITY_TAGS = {
    "Контактная ферма": "free kids",
    "Батут": "free kids",
    "Костровая зона": "free kids",
    "Спортивные игры": "free kids",
    "Русская баня": "paid rain",
    "Финская сауна": "paid rain",
    "Фотосессии": "paid",
    "Река": "free",
    "Большая беседка": "paid rain",
    "Мастер-классы": "paid kids rain",
    "Аренда сапов": "paid",
    "Аренда велосипедов": "paid kids",
}
ACTIVITY_FILTERS = [("free", "Бесплатно"), ("paid", "Платно"), ("kids", "Детям"), ("rain", "В дождь")]

# Архив событий из постов Telegram (даты постов: 15.12.2025, 26.06.2026, 18.01.2025).
EVENT_ARCHIVE = [
    ("new-year", "Новый год", "Глэмпинг готовится к праздникам заранее, а на новогоднюю ночь домики бронируют первыми.", None),
    ("graduation", "Выпускной «Только свои»", "Весь глэмпинг для выпускников: поляна, костёр, беседка с печью и баня.", ("territory", "Костровая зона")),
    ("", "Крещенская купель", "Окунуться в речке, огибающей глэмпинг, и согреться в сауне с видом на лес.", ("territory", "Финская сауна")),
    ("creative", "Мастер-классы", "Живопись, флористика, йога-практики — летом и по праздникам.", ("territory", "Мастер-классы")),
]

GROUP_FACTS = [("4 домика", "до 16 гостей на ночь"), ("до 50", "гостей в беседке с русской печью"),
               ("баня", "на дровах, затопят к приезду"), ("в подарок", "фермерский завтрак на всю компанию")]
GROUP_OCCASIONS = [
    ("День рождения", "Скажите заранее — сделаем скидку, если повод день рождения.", ("territory", "Костровая зона")),
    ("Выпускной", "Свой праздник на природе, без чужих столиков рядом.", ("territory", "Спортивные игры")),
    ("Девичник", "Баня, беседка и вечер, который никто не прервёт.", ("territory", "Русская баня")),
    ("Выезд команды", "Перезагрузка вдали от офиса: поляна, игры, костёр.", ("territory", "Большая беседка")),
    ("Семейный праздник", "Все поколения вместе, а у детей — ферма и батут.", ("territory", "Контактная ферма")),
]
GROUP_FAQ = ("Можно ли слушать музыку", "Какая нужна предоплата", "Что если планы изменятся")

PARTNER_DIRECTIONS = [
    ("Компании и команды", "День рождения, встреча друзей, корпоративный выезд или стратегическая сессия — у нас найдётся место для любого повода собраться вместе. Можно арендовать все четыре домика, провести время в большой беседке и организовать ужин на свежем воздухе.",
     "Предлагаем: размещение во всех четырёх домиках, большую беседку, баню и костровую зону.", "Ждём: повод для встречи, желаемые даты и количество гостей.", None),
    ("Ретриты и выездные программы", "Йога-выезды, оздоровительные практики, обучающие программы, творческие и писательские резиденции. Уединённая территория, лес вокруг и возможность разместить группу в четырёх домиках создают условия для программ, которым важно пространство и спокойная обстановка.",
     "Предлагаем: размещение группы в четырёх домиках, площадки для занятий и возможность аренды всей территории.", "Ждём: описание программы, желаемые даты и количество участников.", None),
    ("Коммерческие съёмки", "Фотосессии, видео, съёмки брендов и каталогов. На одной территории собраны разные локации: домики и террасы, лес, река, озеро, поляна, баня, беседка и ферма.",
     "Предлагаем: площадку в аренду, по часам или на день.", "Ждём: задачу, размер группы и даты. Стоимость зависит от масштаба.", None),
    ("Ведущие мастер-классов и местные партнёры", "Живопись, флористика, ремёсла и другие занятия, которыми хочется делиться с людьми. Если вы создаёте что-то своё и ищете место для встреч, мастер-классов или выездных занятий, будем рады обсудить сотрудничество.",
     "Предлагаем: отдельные локации или всю территорию.", "Ждём: программу, даты и количество участников.", None),
    ("Блогеры и медиа", "Лес, река, терраса и поляна без заборов — фон, который не нужно строить. Свет утром и на закате здесь особенно хорош.",
     "Предлагаем: проживание в домике и свободу снимать где угодно.", "Ждём: идею, формат публикации и даты.", None),
]

PARTNER_FAQ = [
    {"pk": "partner-1", "question": "Сколько человек помещается?", "answer": "<p>С ночёвкой в домиках — до 16, если приехать с палатками — до 150 человек. На дневном мероприятии в крытой беседке помещается до 100 человек. Если людей больше, чем спальных мест, часть группы можно разместить в соседнем глэмпинге.</p>"},
    {"pk": "partner-2", "question": "Можно ли арендовать глэмпинг целиком?", "answer": "<p>Да, это основной формат для выездных мероприятий и корпоративов. На время аренды посторонних на территории нет.</p>"},
    {"pk": "partner-3", "question": "Есть ли питание?", "answer": "<p>В каждом доме оснащённая кухня и своя мангальная зона, в беседке — русская печь. Можно привезти своего повара или заказать доставку. Продукты с нашей фермы — молоко, яйца, сыр — закажите заранее.</p>"},
    {"pk": "partner-4", "question": "Можно ли приехать посмотреть заранее?", "answer": "<p>Да, и мы это советуем. Напишите, договоримся на удобный день. С организаторами, которые приезжают издалека, можем сделать видеосозвон.</p>"},
    {"pk": "partner-5", "question": "Какая нужна предоплата и что с отменой?", "answer": "<p>Предоплата 50 %, в праздничные дни — 100 %. При отмене за 2 недели и более возвращаем 100 % предоплаты, от 7 до 14 дней — 50 %, менее чем за 7 дней предоплата не возвращается. Для комплексной аренды правила строже, чем для обычной брони.</p>"},
    {"pk": "partner-6", "question": "Нужен ли договор?", "answer": "<p>Для компаний и организаторов — да, работаем по договору, закрывающие документы предоставляем.</p>"},
    {"pk": "partner-7", "question": "Берёте ли блогеров?", "answer": "<p>Одна-две коллаборации в месяц. Интересны тревел и лайфстайл с живой аудиторией из Москвы и Тулы. Напишите, что предлагаете и на какие даты.</p>"},
    {"pk": "partner-8", "question": "Можно ли проводить съёмки?", "answer": "<p>Да, коммерческие съёмки и фотосессии возможны. Условия зависят от масштаба: частная фотосессия и съёмочная группа с оборудованием — разные истории.</p>"},
]

# Правила бронирования собираются из тех же ответов FAQ (правка в одном месте).
RULES_FAQ = (
    "Какая нужна предоплата", "Что если планы изменятся", "Во сколько заезд и выезд", "Как проходит заселение",
    "Можно ли с животными", "Можно ли слушать музыку", "Действует ли скидка", "Суммируются ли скидки",
    "Действуют ли акции",
)
# FAQ «Какие условия бронирования и отмены?»
CANCEL_SCALE = [("100 %", "предоплаты вернём при отмене за 7 дней и раньше"),
                ("50 %", "при отмене за 6–4 дня"),
                ("0 %", "при отмене менее чем за 3 дня или незаезде")]
BOOKING_STEPS = [("Выбрать даты", "в календаре домика или в окне брони"),
                 ("Предоплата 50 %", "остальное — при заселении"),
                 ("Подтверждение", "пришлём детали и как добраться"),
                 ("Заезд с 14:00", "выезд до 12:00, встретим лично")]


def _image(source):
    from core.models import TerritoryItem, image_titled

    kind, value = source
    if kind == "image":
        return image_titled(value)
    item = TerritoryItem.objects.filter(title__startswith=value).select_related("image").first()
    return item.image if item else None


def _faq(starts):
    from core.models import FaqItem

    items = list(FaqItem.objects.filter(is_published=True))
    return [item for start in starts for item in items if item.question.startswith(start)]


def context_for(page, request):
    """Контекст доп. страницы по слагу; пустой словарь для остальных."""
    from django.db.models import Q
    from wagtail.models import Page

    from core.models import TerritoryItem
    from services.models import Service

    from core import temp_pages

    if page.slug in temp_pages.SLUGS:
        return temp_pages.context(page, request)
    slug = page.slug
    services = {service.slug: service for service in Service.objects.filter(is_published=True)}
    if slug == "chem-zanyatsya":
        from django.utils.html import format_html

        from core import things_content as things
        from core.models import SiteSettings
        from core.templatetags.marketing_tags import marketing_url

        tiles = {item.title: item.image for item in TerritoryItem.objects.filter(is_published=True).select_related("image")}

        def tile_image(start):
            return next((image for title, image in tiles.items() if start and title.startswith(start)), None)

        scenarios = []
        for scenario in things.SCENARIOS:
            steps = [{"time": time, "title": title, "text": text, "image": tile_image(tile),
                      "service": services.get(service_slug) if service_slug else None}
                     for time, title, text, tile, service_slug in scenario["steps"]]
            house = Page.objects.live().filter(slug=scenario["house"]).first() if scenario.get("house") else None
            scenarios.append({**scenario, "steps": steps, "house_page": house})
        from core import dop_content as dc

        second_day = [place for place in dc.GUIDE if place["key"] in ("polenovo", "behovo", "konyukhov")]
        faq = [item.copy() for item in dc.THINGS_FAQ]
        chat_url = SiteSettings.for_request(request).telegram_chat_url
        if chat_url:
            phrase = "сообщить о своих планах заранее"
            link = format_html('<a href="{}">{}</a>', marketing_url(chat_url, 'chem_zanyatsya'), phrase)
            faq[2]["answer"] = faq[2]["answer"].replace(phrase, link)
        return {"things": things, "scenarios": scenarios, "second_day": second_day,
                "things_faq": faq,
                "nearby_page": Page.objects.live().filter(slug="interesnoe-ryadom").first(),
                "houses_page": Page.objects.live().filter(slug="razmeshchenie").first()}
    if slug == "razvlecheniya":
        tiles = []
        for item in TerritoryItem.objects.filter(is_published=True).select_related("image"):
            tiles.append({"title": item.title, "text": item.description, "image": item.image})
        for service in services.values():
            if not any(" ".join(tile["title"].split()) == " ".join(service.name.split()) for tile in tiles):
                tiles.append({"title": " ".join(service.name.split()), "text": service.short_description,
                              "image": service.display_image})
        for tile in tiles:
            tile["tags"] = next((tags for start, tags in ACTIVITY_TAGS.items() if tile["title"].startswith(start)), "free")
            tile["service"] = next((s for s in services.values()
                                    if " ".join(s.name.split()) == " ".join(tile["title"].split())), None)
        from django.utils import timezone

        from core import dop_content as dc

        for tile in tiles:
            detail = next((d for start, d in dc.ACTIVITY_DETAILS.items() if tile["title"].startswith(start)), None)
            tile["detail"] = detail
            tile["months"] = " ".join(f"m{m}" for m in (detail["months"] if detail else range(1, 13)))
        month = timezone.localdate().month
        return {"tiles": tiles, "filters": ACTIVITY_FILTERS, "months": list(enumerate(dc.MONTHS, start=1)),
                "current_month": month}
    if slug == "meropriyatiya":
        from calendar import Calendar
        from datetime import date

        from forms.forms import EventForm
        from core.models import _consent_page

        from django.db.models import Q as _Q
        from django.utils import timezone

        from core.models import Event

        today = timezone.localdate()
        published = Event.objects.filter(is_published=True).select_related("image")
        upcoming = list(published.filter(_Q(end_date__gte=today) | _Q(end_date__isnull=True, date__gte=today)))
        past = list(published.filter(_Q(end_date__lt=today) | _Q(end_date__isnull=True, date__lt=today)).order_by("-date")[:6])
        # Прошедшие события из админки идут первыми, затем архив из постов Telegram.
        archive = [{"title": event.title, "text": event.description, "image": event.image} for event in past]
        archive += [{"title": title, "text": text, "image": _image(photo) if photo else None, "category": category}
                    for category, title, text, photo in EVENT_ARCHIVE]
        chosen = next((event for event in upcoming if request and str(event.pk) == request.GET.get("event")), None)
        topic = f"{chosen.title}, {chosen.date:%d.%m.%Y}" if chosen else "Ближайшие события"
        from core import dop_content as dc

        november_year = today.year + (11 < today.month)
        november_holiday = date(november_year, 11, 4).weekday() < 5
        calendar = [
            {
                "num": n, "name": dc.MONTHS[n - 1], "items": dc.SEASON_CALENDAR[n] if n != 11 else (
                    "День народного единства в начале месяца",
                    "Самый спокойный месяц в году: лес, тишина и никого вокруг",
                ),
                "days_off": sum(bool(day) for week in Calendar().monthdayscalendar(today.year + (n < today.month), n)
                                for day in week[5:]) + (n == 11 and november_holiday),
                "activities": (
                    ["Ферма", "Баня", "Финская сауна", "Костровая зона", "Беседки", "Фотосессии", "Спортивные игры", "Детская площадка"]
                    if n == 11 else [name for name, details in dc.ACTIVITY_DETAILS.items() if n in details["months"]]
                ),
            }
            for n in (*range(today.month, 13), *range(1, today.month))
        ]
        archive_categories = [
            ("new-year", "Новый год"), ("graduation", "Выпускные"), ("birthday", "Дни рождения"),
            ("wedding", "Свадьбы"), ("creative", "Творчество"), ("sport", "Спорт"), ("", "Все"),
        ]
        return {"calendar": calendar, "current_month": today.month,
                "upcoming": upcoming, "archive": archive, "archive_categories": archive_categories,
                "event_form": EventForm(auto_id="event_%s", initial={"topic": topic}),
                "chosen_event": chosen, "consent_page": _consent_page()}
    if slug == "vyezdy-kompaniy":
        from forms.forms import GroupForm
        from core.models import _consent_page

        occasion = request.GET.get("occasion", "") if request else ""
        occasions = [{"title": title, "text": text, "image": _image(photo)} for title, text, photo in GROUP_OCCASIONS]
        bonfire = TerritoryItem.objects.filter(title="Костровая зона").select_related("image").first()
        from core import dop_content as dc

        return {"group_timeline": dc.GROUP_TIMELINE, "group_checklist": dc.GROUP_CHECKLIST,
                "group_facts": GROUP_FACTS, "occasions": occasions, "group_faq": _faq(GROUP_FAQ),
                "group_image": bonfire.image if bonfire else None,
                "group_form": GroupForm(auto_id="group_%s", initial={"topic": occasion}),
                "consent_page": _consent_page()}
    if slug == "partneram":
        from forms.forms import PartnerForm
        from core.models import _consent_page

        direction = request.GET.get("direction", "") if request else ""
        directions = [{"title": title, "text": text, "offer": offer, "expect": expect, "image": _image(photo) if photo else None}
                      for title, text, offer, expect, photo in PARTNER_DIRECTIONS]
        from core import dop_content as dc

        audience = [(value, label, dc.SRC.get(src)) for value, label, src in dc.AUDIENCE]
        return {"audience": audience, "directions": directions, "partner_faq": PARTNER_FAQ,
                "partner_form": PartnerForm(auto_id="partner_%s", initial={"topic": direction}),
                "consent_page": _consent_page()}
    if slug == "pravila-bronirovaniya":
        legal = Page.objects.live().filter(Q(slug="oferta") | Q(slug="politika-konfidencialnosti"))
        from houses.booking import rates

        fees = rates()
        return {"booking_steps": BOOKING_STEPS, "cancel_scale": CANCEL_SCALE, "rules_faq": _faq(RULES_FAQ),
                "legal_pages": legal, "pet_small_fee": fees.pet_small_fee, "pet_large_fee": fees.pet_large_fee}
    if slug == "rassylka":
        from core.models import ChannelPost

        import datetime

        from core import dop_content as dc

        highlights = [{"date": datetime.date.fromisoformat(d), "title": t, "text": x, "url": u}
                      for d, t, x, u in dc.CHANNEL_HIGHLIGHTS]
        return {"channel_posts": ChannelPost.objects.all()[:3], "highlights": highlights,
                "rubrics": dc.CHANNEL_RUBRICS}
    return {}
