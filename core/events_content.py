"""Тексты раздела «Как это бывает» и настройки баннера мероприятий."""

EVENT_CATEGORIES = [
    ("new-year", "Новый год"),
    ("graduation", "Выпускные"),
    ("birthday", "Дни рождения"),
    ("wedding", "Свадьбы"),
    ("creative", "Творчество"),
    ("sport", "Спорт"),
]

ARCHIVE_COPY = {
    "new-year": (
        "Новогодне-Рождественское",
        ("Подготовка к Новому году здесь начинается\n задолго до 31 декабря. Мы украшаем домики\n и территорию, готовимся к празднику,\n а гости бронируют любимые даты ещё осенью.",),
    ),
    "graduation": (
        "Выпускные",
        (
            "Выпускной — это всегда больше, чем просто праздник. Будь то школа, университет, отряд из летнего лагеря или друзья, решившие собраться спустя годы, — мы рады стать местом вашей встречи.",
            'Первые выпускные прошли здесь, когда ещё не было самого "Сезона". Это были два особенно трогательных вечера выпускников из ДРП «Поленово», которые останутся в памяти самыми теплыми воспоминаниями.',
        ),
    ),
    "birthday": (
        "Дни рождения в Сезоне",
        ("Отличный повод собрать близких и провести время вместе — за большим столом, на террасе или на поляне под открытым небом — у каждого праздника здесь получается своя история.",),
    ),
    "wedding": (
        "Свадьбы",
        ("Небольшой полуостров, окруженный лесом и рекой, создаёт особенную атмосферу для камерной свадьбы. Близкие люди рядом, праздничный ужин под огнями гирлянд и вечер у костра — нам особенно нравится, когда вместо строгого сценария получается тёплый праздник, в котором всё по-настоящему.",),
    ),
    "creative": (
        "Творческое лето",
        ("Мастер-классы, творческие встречи, занятия и вечера на свежем воздухе. Кто-то приезжает рисовать, кто-то — делиться знаниями, а кто-то просто ищет вдохновение в новых местах и людях.",),
    ),
    "sport": (
        "Спорт и активности",
        ("Здесь есть место и для движения: йога-практики, ретриты, оздоровительные и командные выезды.",),
    ),
    "all": (
        "Прошедшие события",
        ("Праздники, творческие встречи и выезды в «Лучшем сезоне».",),
    ),
}


def archive_panels(archive, *, include_all=False):
    from core.models import EventArchive

    albums = {
        album.category: album
        for album in EventArchive.objects.select_related("photo_1", "photo_2", "photo_3")
    }
    by_category = {entry["category"]: entry for entry in archive if entry.get("category")}
    panels = []
    categories = [*EVENT_CATEGORIES, ("all", "Все")] if include_all else EVENT_CATEGORIES
    for key, label in categories:
        title, paragraphs = ARCHIVE_COPY[key]
        album = albums.get(key)
        if album and album.description.strip():
            paragraphs = album.description.strip().splitlines()

        if key == "new-year":
            photos = [{"static_image": f"img/events/new-year-{number}.webp"} for number in range(1, 4)]
        elif key == "all":
            photos = archive.copy()
            seen = {photo["image"].pk for photo in photos if photo["image"]}
            for panel in panels:
                for photo in panel["photos"]:
                    if photo and photo.get("static_image"):
                        photos.append(photo)
                    elif photo and photo["image"].pk not in seen:
                        seen.add(photo["image"].pk)
                        photos.append(photo)
        else:
            fallback = by_category.get(key)
            photos = [fallback] if fallback and fallback["image"] else []
        photos += [None] * max(0, 3 - len(photos))
        if album:
            for index, photo in enumerate((album.photo_1, album.photo_2, album.photo_3)):
                if photo:
                    photos[index] = {"image": photo}
        panels.append({
            "key": key,
            "label": label,
            "title": (album.title if album else "") or title,
            "paragraphs": [paragraph for paragraph in paragraphs if paragraph.strip()],
            "photos": photos,
            "video_slot": f"events-{key}",
            "poster": "img/events/new-year-poster.webp" if key == "new-year" else "",
        })
    return panels
