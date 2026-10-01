"""Импорт согласованных исходников с защитой редакторских замен и удалений."""
import json
from hashlib import sha256
from pathlib import Path

from django.conf import settings
from django.core.files.images import ImageFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from wagtail.images import get_image_model

from core.models import ArchivePhotoImport, GalleryPage
from core.photo_import import file_digest, perceptual_hash
from houses.models import HousePage
from promotions.models import Promotion
from services.models import Service


class Command(BaseCommand):
    help = 'Добавить все согласованные фото, обновить неизменённые импорты по sha256.'

    def add_arguments(self, parser):
        parser.add_argument('--if-not-applied', action='store_true')

    def import_image(self, path, key, title, legacy=None):
        Image = get_image_model()
        with path.open('rb') as source:
            digest = file_digest(source)
        record = ArchivePhotoImport.objects.filter(source_key=key).first()
        if record and record.image_id is None:
            return None, False, False
        image = record.image if record else Image.objects.filter(title=title).first()
        if image is None and legacy:
            image = Image.objects.filter(title=legacy['title']).first()
        created = image is None
        if created:
            with path.open('rb') as source:
                image = Image.objects.create(title=title, file=ImageFile(source, name=path.name))
        else:
            try:
                with image.file.open('rb') as current:
                    current_digest = file_digest(current)
            except OSError:
                self.stdout.write(f'Нет файла Image #{image.pk}; нужна ручная проверка: {key}')
                return image, False, False
            baseline = record.sha256 if record else (legacy or {}).get('sha256', digest)
            if current_digest != digest and current_digest != baseline:
                self.stdout.write(f'Сохранена редакторская замена Image #{image.pk}: {key}')
                if record is None:
                    ArchivePhotoImport.objects.create(source_key=key, sha256=baseline, image=image)
                return image, False, False
            if current_digest != digest:
                with path.open('rb') as source:
                    image.file.save(path.name, ImageFile(source), save=False)
                from PIL import Image as PILImage
                with image.file.open('rb') as current, PILImage.open(current) as decoded:
                    image.width, image.height = decoded.size
                image.save()
                image.renditions.all().delete()
                self.stdout.write(f'Обновлён файл Image #{image.pk}: {key}')
        first_import = record is None
        ArchivePhotoImport.objects.update_or_create(source_key=key, defaults={'sha256': digest, 'image': image})
        return image, first_import, True

    @transaction.atomic
    def handle(self, *args, **options):
        base = Path(settings.BASE_DIR) / 'config/static/img/content-gallery'
        if not base.is_dir():
            self.stdout.write('Архивный набор не найден; наполнение сохранено.')
            return
        manifest_path = base / 'originals.json'
        originals = json.loads(manifest_path.read_text(encoding='utf-8')) if manifest_path.exists() else []
        aliases = {item['legacy']['title'] for item in originals if item.get('legacy')}
        old_paths = sorted(base.glob('*/*.webp'))
        batch = sha256(manifest_path.read_bytes() if manifest_path.exists() else b'')
        for path in old_paths:
            with path.open('rb') as source:
                batch.update(file_digest(source).encode('ascii'))
        for item in originals:
            path = (base / item['path']).resolve()
            if not path.is_relative_to(base.resolve()) or not path.is_file():
                raise CommandError(f'Не найден согласованный исходник: {item["path"]}')
            with path.open('rb') as source:
                batch.update(file_digest(source).encode('ascii'))
        batch_key = f'@batch/{batch.hexdigest()}'
        if options['if_not_applied'] and ArchivePhotoImport.objects.filter(source_key=batch_key).exists():
            self.stdout.write('Эта версия архива уже применена; правки редактора сохранены.')
            return
        old_marker = f'BS archive {old_paths[-1].parent.name}/{old_paths[-1].stem}' if old_paths else ''
        old_applied = bool(old_marker and get_image_model().objects.filter(title=old_marker).exists())
        added = 0
        for folder in sorted(path for path in base.iterdir() if path.is_dir()):
            if folder.name.startswith('house-'):
                page = HousePage.objects.filter(slug=f'domik-{folder.name[6:]}').first()
                relation = page.gallery_images if page else None
            elif folder.name == 'gallery':
                page = GalleryPage.objects.first()
                relation = page.photos if page else None
            else:
                page, relation = None, None
            changed = False
            for path in sorted(folder.glob('*.webp')):
                title = f'BS archive {folder.name}/{path.stem}'
                if title in aliases:
                    continue
                previously_known = get_image_model().objects.filter(title=title).exists()
                image, fresh, managed = self.import_image(path, f'{folder.name}/{path.stem}', title)
                if image is None:
                    continue
                may_link = not options['if_not_applied'] or (fresh and (not old_applied or not previously_known))
                if relation is not None and managed and may_link and not relation.filter(image=image).exists():
                    last = relation.order_by('-sort_order').first()
                    relation.create(image=image, sort_order=(last.sort_order or 0)+1 if last else 0)
                    added += 1
                    changed = True
                if folder.name.startswith('promo-'):
                    Promotion.objects.filter(slug=folder.name[6:], mobile_image=None).update(mobile_image=image)
                if folder.name.startswith('service-') and fresh:
                    service = Service.objects.filter(slug=folder.name[8:]).first()
                    if service:
                        service.gallery_images.add(image)
            if changed:
                page.save_revision().publish()

        for number in range(1,5):
            page = HousePage.objects.filter(slug=f'domik-{number}').first()
            if page is None:
                continue
            changed = False
            seen = []
            for order, item in enumerate(row for row in originals if row['house'] == number):
                path = (base / item['path']).resolve()
                if not path.is_relative_to(base.resolve()) or not path.is_file():
                    raise CommandError(f'Не найден согласованный исходник: {item["path"]}')
                with path.open('rb') as source:
                    digest = file_digest(source)
                fingerprint = perceptual_hash(path)
                if any(digest == old_digest or (fingerprint is not None and old_phash is not None and (fingerprint ^ old_phash).bit_count() <= 4) for old_digest,old_phash in seen):
                    continue
                seen.append((digest,fingerprint))
                image, fresh, managed = self.import_image(path, item['path'], f'BS original {item["path"]}', item.get('legacy'))
                if image is None or not managed:
                    continue
                link = page.gallery_images.filter(image=image).first()
                if link is None and (fresh or not options['if_not_applied']):
                    if item.get('legacy') and image.title == item['legacy']['title']:
                        continue
                    page.gallery_images.create(image=image, sort_order=order)
                    added += 1
                    changed = True
                elif link and link.sort_order != order and fresh:
                    link.sort_order = order
                    link.save(update_fields=['sort_order'])
                    changed = True
            if changed:
                page.save_revision().publish()
        self.stdout.write(self.style.SUCCESS(f'Добавлены фотографии: {added}.'))
        ArchivePhotoImport.objects.get_or_create(source_key=batch_key, defaults={'sha256': batch.hexdigest()})
