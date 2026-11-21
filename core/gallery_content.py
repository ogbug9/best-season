SEASONS = (
    ("winter", "Зима", "Снег по колено, дым над баней и тишина, которой в городе не бывает"),
    ("spring", "Весна", "Река поднимается, лес просыпается, а комаров ещё нет"),
    ("summer", "Лето", "Поздние закаты, прогулки по лесу, шашлыки и костер на поляне"),
    ("autumn", "Осень", "Туман по утрам, камин по вечерам и золото со всех сторон"),
)

LOCATIONS = (
    ("houses", "Дома", "Четыре дома, по 30 м², с панорамными окнами и террасой"),
    ("terrace", "Терраса", "Ротанговая мебель, вид на лес, место, где проходит большая часть дня"),
    ("banya", "Баня", "Настоящая русская баня на дровах, топим заранее"),
    ("gazebo", "Беседка «Корабль»", "Русская печь, крытая, работает круглый год"),
    ("farm", "Ферма", "Около сотни овец, а ещё коровы, козы, кролики и разные виды птиц"),
    ("river", "Река", "Скнижка течёт вдоль территории, до воды пара минут"),
    ("clearing", "Поляна", "Костровая зона, площадка для игр и очень много неба"),
)

LOCATION_FILTERS = [
    (key, "Беседка" if key == "gazebo" else label)
    for key, label, _ in LOCATIONS
]

HOUSE_FILTERS = (
    ("domik-1", "№1 с сауной"), ("domik-2", "№2"), ("domik-3", "№3"), ("domik-4", "№4"),
)

ARCHIVE_ASSET_ROOT = "img/content-gallery/"
ILLUSTRATIONS = (
    ("winter", "clearing", "img/territory/hero-field-600.webp", "Зимняя поляна"),
    ("spring", "", "img/diary-edition/zheltoe-chudo.webp", "Утёнок на ферме"),
    ("summer", "clearing", ARCHIVE_ASSET_ROOT + "gallery/f8df1d7dad76.webp", "Прогулка по поляне"),
    ("autumn", "", "img/diary-edition/griby-na-mangale.webp", "Грибы на мангале"),
    ("", "houses", "img/territory/hero-house-900.webp", "Домик зимой"),
    ("", "terrace", "img/about-20261103/story-terrace.webp", "Терраса домика"),
    ("", "banya", ARCHIVE_ASSET_ROOT + "service-russkaya-banya/712c87168100.webp", "Веники для бани"),
    ("", "gazebo", ARCHIVE_ASSET_ROOT + "service-bolshaya-besedka/6258b2a4c509.webp", "Беседка вечером"),
    ("", "farm", ARCHIVE_ASSET_ROOT + "gallery/281de0fa11e1.webp", "Овца на ферме"),
    ("", "river", ARCHIVE_ASSET_ROOT + "gallery/59e3b806265c.webp", "Река среди деревьев"),
)


def add_illustrations(items):
    seasons = {item["season"] for item in items}
    locations = {item["category"] for item in items}
    for season, category, path, alt in ILLUSTRATIONS:
        if (season and season not in seasons) or (category and category not in locations):
            items.append({"season": season, "category": category, "static_image": path, "alt": alt})
            seasons.add(season)
            locations.add(category)


def sections(items):
    def cards(entries, field):
        photos = {}
        for item in items:
            photos.setdefault(item[field], item)
        return [(label, text, photos.get(key)) for key, label, text in entries]

    return [
        ("Сезон по сезонам", "Поляна одна, но зимой и летом вы побываете как будто в разных местах.",
         cards(SEASONS, "season")),
        ("Лучший сезон в деталях и локациях", "Если смотрите перед бронью — начните отсюда.",
         cards(LOCATIONS, "category")),
    ]
