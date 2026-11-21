import json
from functools import lru_cache
from pathlib import Path

from django.conf import settings


@lru_cache(maxsize=1)
def archive_index():
    base = Path(settings.BASE_DIR) / "config/static/img/guest-archive"
    records = {}
    for filename in ("index.json", "locations.json"):
        for record in json.loads((base / filename).read_text(encoding="utf-8")):
            records.setdefault(record["key"], []).extend(record["entries"])
    return records


def add_archive(items, houses, imported, removed):
    """Share identical archive photos across their house and season filters."""
    by_title = {item["image"].title: item for item in items}
    redundant = set()
    for key, entries in archive_index().items():
        entries = [e for e in entries if e["path"] not in removed
                   and ("house" not in e or e["house"] in houses)]
        if not entries:
            continue
        matches = []
        for entry in entries:
            item = (imported.get(entry["path"]) or by_title.get("BS original " + entry["path"])
                    or by_title.get(entry.get("legacy")))
            if item is not None and all(item is not match for match in matches):
                matches.append(item)
        if matches:
            item = matches[0]
            for duplicate in matches[1:]:
                redundant.add(id(duplicate))
                for field, values in duplicate["tags"].items():
                    item["tags"][field].extend(v for v in values if v not in item["tags"][field])
                if not item["alt"]:
                    item["alt"] = duplicate["alt"]
        else:
            house = houses.get(entries[0].get("house"))
            category = "houses" if house else "territory"
            season = entries[0]["season"]
            path = "img/guest-archive/" + key
            item = {"static_image": path + ".webp", "thumbnail": path + "-480.webp",
                    "house": house, "category": category, "season": season,
                    "alt": house.title if house else ("Глэмпинг зимой" if season == "winter" else "Глэмпинг летом"),
                    "tags": {"house": [], "season": [], "what": [category]}}
            items.append(item)
        for entry in entries:
            house = houses.get(entry.get("house"))
            if house and house.slug not in item["tags"]["house"]:
                item["tags"]["house"].append(house.slug)
            if house and "houses" not in item["tags"]["what"]:
                item["tags"]["what"].append("houses")
            if entry["season"] not in item["tags"]["season"]:
                item["tags"]["season"].append(entry["season"])
            item["season"] = item["season"] or entry["season"]
    items[:] = [item for item in items if id(item) not in redundant]


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


def add_illustrations(items, archive_images):
    seasons = {item["season"] for item in items}
    locations = {item["category"] for item in items}
    for season, category, path, alt in ILLUSTRATIONS:
        if (season and season not in seasons) or (category and category not in locations):
            key = path.removeprefix(ARCHIVE_ASSET_ROOT).removesuffix(".webp")
            existing = archive_images.get(key)
            if existing:
                for field, tag, value in (("category", "what", category), ("season", "season", season)):
                    if value and value not in existing["tags"][tag]:
                        existing["tags"][tag].append(value)
                        existing[field] = value
            else:
                items.append({"season": season, "category": category, "static_image": path, "alt": alt})
            seasons.add(season)
            locations.add(category)


def sections(items):
    def cards(entries, field):
        photos = {}
        for item in items:
            photos.setdefault(item[field], item)
        parameter = "season" if field == "season" else "what"
        return [(label, text, photos.get(key), f"{parameter}={key}") for key, label, text in entries]

    return [
        ("Сезон по сезонам", "Поляна одна, но зимой и летом вы побываете как будто в разных местах.",
         cards(SEASONS, "season")),
        ("Лучший сезон в деталях и локациях", "Если смотрите перед бронью — начните отсюда.",
         cards(LOCATIONS, "category")),
    ]
