"""Apply the photographs embedded in the supplied Desktop.svg reference.

Runs once after seed_content at deployment. This command assigns reference
photos and publishes the house reviews transcribed from the supplied design.
"""

from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from wagtail.images import get_image_model
from wagtail.models import Site

from core.models import NearbyPlace, TerritoryItem
from home.models import HomeGalleryImage, HomeSlide
from houses.models import HouseGalleryImage, HousePage
from promotions.models import Promotion
from reviews.models import Review, ReviewSource
from services.models import Service


PHOTO_DIR = Path(settings.BASE_DIR) / "config" / "static" / "img" / "design-reference"
ORIGINAL_PHOTOS = {10: "nearby-konyukhov-original.jpg"}


def photo_source(number):
    return PHOTO_DIR / ORIGINAL_PHOTOS.get(number, f"ref-{number:02d}.webp")

TERRITORY_PHOTOS = {
    "Контактная ферма": 21,
    "Батут и детская площадка": 18,
    "Костровая зона": 12,
    "Спортивные игры": 17,
    "Русская баня": 15,
    "Финская сауна": 13,
    "Фотосессии": 19,
    'Река "Скнижка"': 16,
    "Большая беседка": 14,
    "Мастер-классы": 20,
}

NEARBY_PHOTOS = {
    'Усадьба "Поленово"': 9,
    "деревня Ф. Конюхова": 10,
    'деревня "Бёхово"': 11,
}

PROMOTION_PHOTOS = {
    "den-rozhdeniya": 46,
    "pyatnica-50": 48,
    "may-sentyabr": 50,
    "vygodnaya-banya": 51,
    "gostepriimstvo": 52,
    "pravilnaya-udalenka": 53,
    "oktyabr-aprel": 54,
}
# По pattern135–143 в Desktop.svg: видимое окно фото 360:220.
# Значения переводят вертикальный сдвиг pattern в focal point Wagtail.
PROMOTION_FOCAL_Y = {46: 525, 48: 920, 50: 992, 51: 379,
                     52: 251, 53: 457, 54: 865}

SERVICE_PHOTOS = {
    "russkaya-banya": 37,
    "bolshaya-besedka": 14,
    "arenda-sapov": 16,
    "master-klassy": 20,
    "fotosessii": 19,
    "arenda-velosipedov": 6,
}

HOUSE_PHOTOS = {
    # Первое фото — обложка карточки; ещё пять — мозаика страницы дома.
    "Первый домик": [22, 55, 51, 57, 58, 59],
    "Второй домик": [23, 63, 64, 65, 66, 67],
    "Третий домик": [24, 72, 73, 74, 75, 76],
    "Четвёртый домик": [25, 80, 81, 82, 83, 84],
}

# Тексты и фото из четырёх фреймов домов в Desktop.svg. Даты и оценки в
# макете не указаны, поэтому не создаём их. Источник OTHER отделяет эти
# материалы от отзывов, пришедших через форму или внешнюю площадку.
HOUSE_REVIEWS = {
    "Первый домик": [
        (60, "Элина Т.", "Были в домике №1, место прекрасное, мы остались довольны! Очень понравилась идея финской сауны с панорамными окнами - зимой это невероятно атмосферно. За теплые полы - отдельное спасибо! Идеальный баланс природы и городского комфорта."),
        (61, "Наталья Е.", "Отдыхали здесь с подругами. Атмосфера волшебная: уют, тишина, природа вокруг. Домики чистые, продуманные до мелочей - от теплых пледов до ватных дисков. Особенно порадовала большая терраса и финская сауна - идеальное место для вечерних посиделок."),
        (62, "Михаил Б.", "Были в июне 2025 года. Завораживающий вид, классное расположение, уют, комфорт\nв сочетании с радушной встречей оставили обалденные впечатления!\nВ домиках чисто, белье новое, есть\nвся утварь для приготовления."),
    ],
    "Второй домик": [
        (69, "Марина Ю.", "Отдыхали в этом чудесном месте и остались в полном восторге. В домиках есть всё необходимое для комфортного проживания. Очень понравились большие уютные веранды, здорово сидеть по вечерам, слушать тишину и смотреть на лес."),
        (70, "Арина К.", "Отличный отдых!\nВ доме как в элитном отеле: стерильная чистота; изысканный дизайн; кухня со всеми принадлежностями; ванная комната. Очень ухоженная территория, трава всегда скошенная, деревья в один рост, детская площадка с батутом."),
        (71, "Наталья Н.", "Очень довольна своим выбором. Внутри домика есть всё, что нужно, и даже больше. И ещё я была очень довольна наличием крючков и поверхностей! Панорамные окна, печка, шум дождя по крыше - всё очень душевно и целительно для уставшего городского жителя."),
    ],
    "Третий домик": [
        (77, "Марина Т.", "Чудесное уникальное место! Большая территория без заборов, сквозь панорамные окна видна красивая природа. Место, где мы с семьей полностью расслабились за три дня.\nЕсть ферма, где можно погладить козу, угостить яблоками теленка."),
        (78, "Анастасия З.", "Отличное место для загородного отдыха! Очень понравилась идея самих домиков - из транспортных контейнеров. Внутри все функционально: теплый пол, кондиционер, блекаут шторы - это супер. У каждого домика своя веранда, мангал и небольшой участок, огороженный туями."),
        (79, "Алексей К.", "Дом замечательный! Просторный участок с прекрасно обустроенной территорией. Внутри дома уютная атмосфера: чистота, комфорт и современность интерьера. Здесь есть все необходимое для комфортного проживания. Обязательно вернемся!"),
    ],
    "Четвёртый домик": [
        (85, "Николай Л.", "Все отлично, домики уютные\nи чистые, имеется все необходимое,\nкровать удобная, что очень важно!\nЧувствуется что хозяева хотели создать\nуют как в домиках, так и в зоне отдыха\nна улице. Природа шикарная, тишина\nи чистый воздух!"),
        (86, "Николай Л.", "Отличное соотношение цена-качество.\nВ домике есть все необходимое для автономного проживания и даже больше. Удобное местоположение ко всем местным локациям."),
        (87, "Екатерина П.", "Мы остались очень довольны своим пребыванием в этом доме, он безумно уютный не смотря на его габариты, чистота и порядок поддерживаются на высоком уровне. Атмосфера отличная\n- камин, шашлык, тишина и спокойствие."),
    ],
}

HOME_GALLERY = [
    (0, "Кофе на террасе"),
    (2, "Керамика"),
    (5, "Гуси на ферме"),
    (7, "Вечер у огня"),
    (8, "Костёр"),
    (3, "Свежие яйца"),
    (6, "Прогулка по полю"),
    (1, "Овца на ферме"),
    (4, "Друзья вместе"),
]


class Command(BaseCommand):
    help = "Ставит точные фотографии из Desktop.svg в главную, территорию и домики"

    def add_arguments(self, parser):
        parser.add_argument(
            "--if-not-applied", action="store_true",
            help="Пропустить импорт, если его последняя фотография уже сохранена",
        )

    def handle(self, *args, **options):
        # Весь импорт ниже проходит одной транзакцией. Последний номер
        # появляется в БД только после успешного завершения команды.
        if options["if_not_applied"] and get_image_model().objects.filter(
            title="BS Desktop review #87"
        ).exists():
            self.stdout.write("Макет Desktop.svg уже применён")
            return

        used = {28, 29, 30, 31, 32}
        used.update(TERRITORY_PHOTOS.values())
        used.update(NEARBY_PHOTOS.values())
        used.update(PROMOTION_PHOTOS.values())
        used.update(SERVICE_PHOTOS.values())
        used.update(number for number, _ in HOME_GALLERY)
        used.update(number for numbers in HOUSE_PHOTOS.values() for number in numbers)
        review_numbers = {number for reviews in HOUSE_REVIEWS.values()
                          for number, _, _ in reviews}
        missing = [str(photo_source(number)) for number in used
                   if not photo_source(number).is_file()]
        missing += [str(PHOTO_DIR / f"review-{number:02d}.webp")
                    for number in review_numbers
                    if not (PHOTO_DIR / f"review-{number:02d}.webp").is_file()]
        if missing:
            raise CommandError("Не найдены фотографии: " + ", ".join(missing))

        image_model = get_image_model()
        images = {}
        with transaction.atomic():
            for number in sorted(used):
                title = ("BS Desktop original IMG_3551" if number == 10
                         else f"BS Desktop reference #{number:02d}")
                image = image_model.objects.filter(title=title).first()
                if image is None:
                    source = photo_source(number)
                    image = image_model(title=title)
                    with source.open("rb") as file:
                        image.file.save(source.name, File(file), save=False)
                    image.save()
                focal_y = PROMOTION_FOCAL_Y.get(number)
                if focal_y is not None and (
                    image.focal_point_y != focal_y or image.focal_point_width != 1
                ):
                    image.focal_point_x = round(image.width / 2)
                    image.focal_point_y = focal_y
                    image.focal_point_width = 1
                    image.focal_point_height = 1
                    image.save(update_fields=[
                        "focal_point_x", "focal_point_y",
                        "focal_point_width", "focal_point_height",
                    ])
                    image.renditions.all().delete()
                images[number] = image

            review_images = {}
            for number in sorted(review_numbers):
                title = f"BS Desktop review #{number:02d}"
                image = image_model.objects.filter(title=title).first()
                if image is None:
                    source = PHOTO_DIR / f"review-{number:02d}.webp"
                    image = image_model(title=title)
                    with source.open("rb") as file:
                        image.file.save(source.name, File(file), save=False)
                    image.save()
                review_images[number] = image

            site = Site.objects.filter(is_default_site=True).first() or Site.objects.first()
            if site is None:
                raise CommandError("Нет главной страницы Wagtail")
            home = site.root_page.specific
            home.about_image = images[31]
            home.quote_image = images[29]
            home.save()
            slides = list(home.slides.order_by("sort_order", "pk"))
            if slides:
                slides[0].image = images[32]
                slides[0].alt = "Лесная тропа в глэмпинге Лучший сезон"
                slides[0].save()
            else:
                HomeSlide.objects.create(page=home, image=images[32], sort_order=0,
                                         alt="Лесная тропа в глэмпинге Лучший сезон")
            if len(slides) < 3:
                for index, number in enumerate([30, 28][max(0, len(slides)-1):],
                                               start=max(1, len(slides))):
                    HomeSlide.objects.create(page=home, image=images[number],
                                             sort_order=index, alt="Лес в Лучший сезон")
            home.gallery_images.all().delete()
            for order, (number, alt) in enumerate(HOME_GALLERY):
                HomeGalleryImage.objects.create(page=home, image=images[number],
                                                alt=alt, sort_order=order)
            home.save_revision().publish()

            for title, number in TERRITORY_PHOTOS.items():
                TerritoryItem.objects.filter(title=title).update(image=images[number])
            for title, number in NEARBY_PHOTOS.items():
                NearbyPlace.objects.filter(title=title).update(image=images[number])
            for slug, number in PROMOTION_PHOTOS.items():
                Promotion.objects.filter(slug=slug).update(image=images[number])

            for title, numbers in HOUSE_PHOTOS.items():
                house = HousePage.objects.filter(title=title).first()
                if house is None:
                    continue
                house.hero_image = images[numbers[0]]
                house.save()
                house.gallery_images.all().delete()
                for order, number in enumerate(numbers[1:]):
                    HouseGalleryImage.objects.create(page=house, image=images[number],
                                                     caption=f"{title}: фото {order + 2}",
                                                     sort_order=order)
                house.save_revision().publish()

                for order, (number, author, text) in enumerate(HOUSE_REVIEWS[title], start=1):
                    review, _ = Review.objects.get_or_create(
                        house=house, author_name=author, source=ReviewSource.OTHER,
                        sort_order=order * 10,
                        defaults={"text": text, "image": review_images[number],
                                  "is_published": True},
                    )
                    if (review.text != text or review.image_id != review_images[number].pk
                            or not review.is_published):
                        review.text = text
                        review.image = review_images[number]
                        review.is_published = True
                        review.save(update_fields=["text", "image", "is_published"])

            for slug, number in SERVICE_PHOTOS.items():
                Service.objects.filter(slug=slug).update(image=images[number])

        self.stdout.write(self.style.SUCCESS(
            f"Применён макет Desktop.svg: {len(images) + len(review_images)} фото, "
            f"{len(HOUSE_PHOTOS)} домика, {sum(map(len, HOUSE_REVIEWS.values()))} отзывов, "
            f"{len(HOME_GALLERY)} кадров главной"
        ))
