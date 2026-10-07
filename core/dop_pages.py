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

# Сценарии «Чем заняться». Шаг: (время, заголовок, строка, фото, слаг услуги).
# Фото: ("image", точное название) или ("territory", начало названия плитки).
SCENARIOS = [
    {
        "code": "couple", "label": "Вдвоём", "title": "Сбежать вдвоём",
        # Telegram 02.06.2026 «Люди, которые никогда не отдыхают вдвоём…»
        "lead": "Два дня без ролей «родитель» и «начальник» — только вы двое, лес и тишина.",
        "house": "domik-1", "house_note": "Домик №1 — с собственной финской сауной и панорамными окнами.",
        "steps": [
            ("Утро", "Кофе на террасе", "Проснуться без будильника и увидеть солнце в панорамных окнах.", ("image", "BS About story-terrace"), None),
            ("День", "Сапы по Скнижке", "С воды берег выглядит иначе: гнёзда аистов, дикие утки, бобровая хатка.", ("territory", "Река"), "arenda-sapov"),
            ("Вечер", "Сауна с видом на лес", "Финская сауна в Домике №1 не ограничена по времени.", ("territory", "Финская сауна"), None),
            ("Ночь", "Звёзды над поляной", "Вдали от города небо видно целиком.", ("image", "BS About pillar-slow"), None),
        ],
    },
    {
        "code": "kids", "label": "С детьми", "title": "Выходные с детьми",
        "lead": "Животные, батут и костёр — день, после которого дети засыпают сами.",
        "house": "", "house_note": "В каждом домике до четырёх гостей, детям есть где развернуться на террасе.",
        "steps": [
            ("Утро", "Контактная ферма", "Покормить животных вместе с хозяевами и выбрать продукты к завтраку.", ("territory", "Контактная ферма"), None),
            ("День", "Батут и площадка", "Маленьким гостям точно не будет скучно.", ("territory", "Батут"), None),
            ("Вечер", "Костёр", "Собраться всей семьёй у живого огня в костровой зоне.", ("territory", "Костровая зона"), None),
            ("Ночь", "Тихий лес", "Лес с трёх сторон и речка рядом — спится здесь иначе.", ("image", "BS About story-moss"), None),
        ],
    },
    {
        "code": "dog", "label": "С собакой", "title": "Всей семьёй, вместе с питомцем",
        # Telegram 17.04.2026 «pet-friendly»
        "lead": "Не «разрешение на вход», а приглашение для всей семьи. Возьмите любимую лежанку и игрушку.",
        "house": "", "house_note": "Доплата за питомца — 1 000 ₽ (в холке до 45 см) или 1 500 ₽ (выше). Предупредите при бронировании.",
        "steps": [
            ("Утро", "Роса на террасе", "Пёс проверяет утреннюю росу, пока вы варите кофе.", ("image", "BS About story-season"), None),
            ("День", "Прогулка по территории", "Около гектара без заборов и лес сразу за домиками.", ("image", "BS About value-journey"), None),
            ("Вечер", "Терраса и мангал", "У каждого домика своя терраса и зона для мангала.", ("image", "BS About pillar-comfort"), None),
        ],
    },
    {
        "code": "company", "label": "Компанией", "title": "Выходные компанией",
        # Telegram 26.06.2026 «Только свои»; FAQ «Можно ли слушать музыку…»
        "lead": "Баня, большая беседка и костёр — и никто не попросит разойтись раньше.",
        "house": "vyezdy-kompaniy", "house_note": "Можно снять весь глэмпинг: все 4 домика, поляну и беседку «Корабль».",
        "steps": [
            ("День", "Спортивные игры", "Волейбол, бадминтон и детский футбол на поляне.", ("territory", "Спортивные игры"), None),
            ("Вечер", "Русская баня", "Баня на дровах — её затопят к вашему приезду.", ("territory", "Русская баня"), "russkaya-banya"),
            ("Ночь", "Беседка «Корабль»", "Для больших вечеров — вдали от домиков, с русской печью.", ("territory", "Большая беседка"), "bolshaya-besedka"),
        ],
    },
    {
        "code": "work", "label": "Работать", "title": "Неделя на удалёнке",
        # Telegram 12.01.2026; FAQ «Стабильная ли связь и интернет?», «…на месяц или больше?»
        "lead": "Работать можно и уютно: оптоволокно в домике, обед на террасе, баня вечером.",
        "house": "", "house_note": "Можно остаться на неделю и дольше — спросите про длительное проживание.",
        "steps": [
            ("Утро", "Связь без компромиссов", "В домиках оптоволокно без ограничений по скорости.", ("image", "BS About story-terrace"), None),
            ("День", "Обед на террасе", "Перерыв на свежем воздухе вместо офисной кухни.", ("image", "BS About pillar-farm"), None),
            ("Вечер", "Баня после работы", "Лучший способ закрыть ноутбук.", ("territory", "Русская баня"), "russkaya-banya"),
        ],
    },
]

# Telegram 04.07.2026 «Когда идёт дождь…»; камин в каждом домике — описание сообщества VK.
RAINY_DAY = [
    ("Книга", "До которой наконец дойдут руки."),
    ("Чай", "В дождь он почему-то вкуснее."),
    ("Настолки и кино", "Вечер, который затянется сам собой."),
    ("Камин", "В каждом домике — свой."),
]

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
    ("Новый год", "Глэмпинг готовится к праздникам заранее, а на новогоднюю ночь домики бронируют первыми.", ("image", "BS About diary-holidays")),
    ("Выпускной «Только свои»", "Весь глэмпинг для выпускников: поляна, костёр, беседка с печью и баня.", ("territory", "Костровая зона")),
    ("Крещенская купель", "Окунуться в речке, огибающей глэмпинг, и согреться в сауне с видом на лес.", ("territory", "Финская сауна")),
    ("Мастер-классы", "Живопись, флористика, йога-практики — летом и по праздникам.", ("territory", "Мастер-классы")),
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
    ("Съёмки и блогеры", "Локацию уже оценила съёмочная команда Алины Загитовой; о нас снимали выпуск для Rutube и YouTube.",
     "Предлагаем: площадку для съёмок и проживание.", "Ждём: идею и формат публикации.", ("territory", "Фотосессии")),
    ("Ведущие мастер-классов", "Живопись, флористика, йога-практики — летом и по праздникам.",
     "Предлагаем: беседку, поляну и гостей глэмпинга.", "Ждём: программу и даты.", ("territory", "Мастер-классы")),
    ("Местные партнёры", "Экскурсии по округе, теннисный корт, фермерские продукты.",
     "Предлагаем: рассказать о вас гостям и в рубрике #ИнтересноеРядом.", "Ждём: условия для наших гостей.", ("image", "BS About value-sharing")),
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

    slug = page.slug
    services = {service.slug: service for service in Service.objects.filter(is_published=True)}
    if slug == "chem-zanyatsya":
        scenarios = []
        for scenario in SCENARIOS:
            steps = [{"time": time, "title": title, "text": text, "image": _image(photo),
                      "service": services.get(service_slug) if service_slug else None}
                     for time, title, text, photo, service_slug in scenario["steps"]]
            house = Page.objects.live().filter(slug=scenario["house"]).first() if scenario["house"] else None
            scenarios.append({**scenario, "steps": steps, "house_page": house})
        return {"scenarios": scenarios, "rainy_day": RAINY_DAY,
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
        return {"tiles": tiles, "filters": ACTIVITY_FILTERS}
    if slug == "meropriyatiya":
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
        archive += [{"title": title, "text": text, "image": _image(photo)} for title, text, photo in EVENT_ARCHIVE]
        chosen = next((event for event in upcoming if request and str(event.pk) == request.GET.get("event")), None)
        topic = f"{chosen.title}, {chosen.date:%d.%m.%Y}" if chosen else "Ближайшие события"
        return {"upcoming": upcoming, "archive": archive[:8],
                "event_form": EventForm(auto_id="event_%s", initial={"topic": topic}),
                "chosen_event": chosen, "consent_page": _consent_page()}
    if slug == "vyezdy-kompaniy":
        from forms.forms import GroupForm
        from core.models import _consent_page

        occasion = request.GET.get("occasion", "") if request else ""
        occasions = [{"title": title, "text": text, "image": _image(photo)} for title, text, photo in GROUP_OCCASIONS]
        bonfire = TerritoryItem.objects.filter(title="Костровая зона").select_related("image").first()
        return {"group_facts": GROUP_FACTS, "occasions": occasions, "group_faq": _faq(GROUP_FAQ),
                "group_image": bonfire.image if bonfire else None,
                "group_form": GroupForm(auto_id="group_%s", initial={"topic": occasion}),
                "consent_page": _consent_page()}
    if slug == "partneram":
        from forms.forms import PartnerForm
        from core.models import _consent_page

        direction = request.GET.get("direction", "") if request else ""
        directions = [{"title": title, "text": text, "offer": offer, "expect": expect, "image": _image(photo)}
                      for title, text, offer, expect, photo in PARTNER_DIRECTIONS]
        return {"directions": directions, "partner_form": PartnerForm(auto_id="partner_%s", initial={"topic": direction}),
                "consent_page": _consent_page()}
    if slug == "pravila-bronirovaniya":
        legal = Page.objects.live().filter(Q(slug="oferta") | Q(slug="politika-konfidencialnosti"))
        return {"booking_steps": BOOKING_STEPS, "cancel_scale": CANCEL_SCALE, "rules_faq": _faq(RULES_FAQ),
                "legal_pages": legal}
    if slug == "rassylka":
        from core.models import ChannelPost

        return {"channel_posts": ChannelPost.objects.all()[:3],
                "channel_tags": ["#ИнтересноеРядом", "#Кинобайт", "Утреннее"]}
    return {}
