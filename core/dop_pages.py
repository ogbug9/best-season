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
    ("Съёмки и блогеры", "Лес, река, терраса и поляна без заборов — фон, который не нужно строить. Свет утром и на закате у нас особенно хорош.",
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

    from core import temp_pages

    if page.slug in temp_pages.SLUGS:
        return temp_pages.context(page, request)
    slug = page.slug
    services = {service.slug: service for service in Service.objects.filter(is_published=True)}
    if slug == "chem-zanyatsya":
        from core import things_content as things

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
        return {"things": things, "scenarios": scenarios,
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
        from core import dop_content as dc

        calendar = [{"num": n, "name": name, "items": dc.SEASON_CALENDAR[n]} for n, name in enumerate(dc.MONTHS, start=1)]
        return {"calendar": calendar, "current_month": today.month,
                "upcoming": upcoming, "archive": archive[:8],
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
        directions = [{"title": title, "text": text, "offer": offer, "expect": expect, "image": _image(photo)}
                      for title, text, offer, expect, photo in PARTNER_DIRECTIONS]
        from core import dop_content as dc

        audience = [(value, label, dc.SRC.get(src)) for value, label, src in dc.AUDIENCE]
        return {"audience": audience, "directions": directions,
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
