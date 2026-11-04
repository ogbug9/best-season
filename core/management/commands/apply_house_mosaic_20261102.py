"""Предпросмотр и осторожное обновление мозаик из макета от 02.11.

Запуск без --apply только показывает изменения. Существующие фото не удаляются.
"""
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from wagtail.images import get_image_model

from houses.models import HouseGalleryImage, HousePage


MOSAICS = {
    'Первый домик': ([55, 51, 57, 58, 59], [60, 61, 62, 63, 64]),
    'Второй домик': ([63, 64, 65, 66, 67], [68, 69, 70, 71, 72]),
    'Третий домик': ([72, 73, 74, 75, 76], [77, 78, 79, 80, 81]),
    'Четвёртый домик': ([80, 81, 82, 83, 84], [85, 86, 87, 88, 89]),
}
PHOTO_DIR = Path(settings.BASE_DIR) / 'config/static/img/house-mosaic-20261102'


class Command(BaseCommand):
    help = 'Просмотр или безопасное применение мозаик домиков из макета 02.11'

    def add_arguments(self, parser):
        parser.add_argument('--apply', action='store_true', help='Применить проверенные замены')

    def handle(self, *args, **options):
        files = [PHOTO_DIR / f'figma-{number}.webp' for _, new in MOSAICS.values() for number in new]
        if any(not path.is_file() for path in files):
            raise CommandError('Нет всех 20 фото мозаики.')
        with transaction.atomic():
            for title, (old, new) in MOSAICS.items():
                page = HousePage.objects.select_for_update().filter(title=title).first()
                if page is None:
                    self.stdout.write(f'{title}: страница не найдена')
                    continue
                photos = list(page.gallery_images.select_related('image').order_by('sort_order', 'pk'))
                expected = [f'BS Desktop reference #{number:02d}' for number in old]
                selected = [f'BS Figma 20261102 house {title} #{number}' for number in new]
                current = [photo.image.title for photo in photos[:5]]
                if current == selected:
                    self.stdout.write(f'{title}: уже применено')
                    continue
                house_number = page.slug.removeprefix('domik-')
                archive_prefixes = (
                    f'BS archive house-{house_number}/',
                    f'BS original house-{house_number}/',
                )
                managed_gallery = current == expected or (
                    any(name.startswith(archive_prefixes) for name in current)
                    and all(name in expected or name.startswith(archive_prefixes) for name in current)
                )
                if page.has_unpublished_changes or not managed_gallery or any(
                    photo.sort_order is None or photo.sort_order < 0 for photo in photos
                ):
                    self.stdout.write(f'{title}: пропущен — черновик или галерея изменены редактором')
                    continue
                if not options['apply']:
                    self.stdout.write(f'{title}: готово к обновлению; сохранится {len(photos)} фото')
                    continue
                for index, number in enumerate(new):
                    name = selected[index]
                    image = get_image_model().objects.filter(title=name).first()
                    if image is None:
                        path = PHOTO_DIR / f'figma-{number}.webp'
                        image = get_image_model()(title=name)
                        with path.open('rb') as source:
                            image.file.save(path.name, File(source), save=False)
                        image.save()
                    HouseGalleryImage.objects.create(page=page, image=image, caption=f'{title}: фото {index + 1}', sort_order=index - 5)
                page.save_revision().publish()
                self.stdout.write(self.style.SUCCESS(f'{title}: обновлён, остальные {len(photos)} фото сохранены'))
