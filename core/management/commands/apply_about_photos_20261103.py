"""Apply exact About photos from the supplied 02.11 SVG, preserving editor changes."""
import copy
import hashlib
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand
from django.db import transaction
from wagtail.images import get_image_model

from core.models import ContentPage


class Command(BaseCommand):
    help = 'Preview or apply guarded About photo replacements from the supplied SVG'

    def add_arguments(self, parser):
        parser.add_argument('--apply', action='store_true')

    @transaction.atomic
    def handle(self, *args, **options):
        Image = get_image_model()
        for page in ContentPage.objects.select_for_update().filter(slug='o-nas'):
            if page.has_unpublished_changes:
                self.stdout.write('Пропущено: есть неопубликованные изменения')
                continue
            data = copy.deepcopy(list(page.about_content.raw_data))
            changed = False
            for block in data:
                content = block.get('value', {})
                photos = content.get('history_photos', []) + content.get('pillars', [])
                for photo in photos:
                    key = photo.get('crop')
                    if key not in {'story-terrace', 'pillar-farm', 'pillar-slow', 'pillar-comfort'}:
                        continue
                    current = Image.objects.filter(pk=photo.get('image')).first()
                    title = f'BS About 20261103 {key}'
                    if current and current.title == title:
                        self.stdout.write(f'{key}: уже применено')
                        continue
                    original = Path(settings.BASE_DIR) / f'config/static/img/about/{key}.webp'
                    if not current or current.title != f'BS About {key}' or not original.exists():
                        self.stdout.write(f'{key}: пропущено — изменено редактором')
                        continue
                    with current.file.open('rb') as source:
                        same = hashlib.sha256(source.read()).digest() == hashlib.sha256(original.read_bytes()).digest()
                    if not same:
                        self.stdout.write(f'{key}: пропущено — файл изменён редактором')
                        continue
                    self.stdout.write(f'{key}: готово к замене')
                    if not options['apply']:
                        continue
                    image = Image.objects.filter(title=title).first()
                    if image is None:
                        path = Path(settings.BASE_DIR) / f'config/static/img/about-20261103/{key}.webp'
                        image = Image(title=title)
                        with path.open('rb') as source:
                            image.file.save(f'20261103-{key}.webp', File(source), save=False)
                        image.save()
                    photo['image'] = image.pk
                    if key == 'story-terrace':
                        photo['alt'] = 'Коза на нашей ферме'
                    changed = True
            if changed:
                page.about_content = data
                page.save_revision().publish()
                self.stdout.write('Фотографии обновлены, остальные поля сохранены')
