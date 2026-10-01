"""Добавить согласованные фотографии из архивного набора, сохранив текущие кадры."""
from pathlib import Path

from django.conf import settings
from django.core.files.images import ImageFile
from django.core.management.base import BaseCommand
from django.db import transaction
from wagtail.images import get_image_model

from core.models import GalleryPage
from houses.models import HousePage
from promotions.models import Promotion
from services.models import Service


class Command(BaseCommand):
    help = 'Добавить фото домов/галереи и мобильные кадры акций из согласованного архива.'

    def add_arguments(self, parser):
        parser.add_argument('--if-not-applied', action='store_true')

    @transaction.atomic
    def handle(self, *args, **options):
        base = Path(settings.BASE_DIR) / 'config/static/img/content-gallery'
        if not base.is_dir():
            self.stdout.write('Архивный набор не найден; наполнение сохранено.')
            return
        Image = get_image_model()
        paths = sorted(base.glob('*/*.webp'))
        if not paths:
            return
        last = paths[-1]
        marker = f'BS archive {last.parent.name}/{last.stem}'
        if options['if_not_applied'] and Image.objects.filter(title=marker).exists():
            self.stdout.write('Архивные фото уже добавлены; последующие правки CMS сохранены.')
            return
        added = 0
        for folder in sorted(path for path in base.iterdir() if path.is_dir()):
            if folder.name.startswith('house-'):
                page = HousePage.objects.filter(slug=f'domik-{folder.name[-1]}').first()
                relation = page.gallery_images if page else None
            elif folder.name == 'gallery':
                page = GalleryPage.objects.first()
                relation = page.photos if page else None
            else:
                page, relation = None, None
            changed = False
            for path in sorted(folder.glob('*.webp')):
                title = f'BS archive {folder.name}/{path.stem}'
                image = Image.objects.filter(title=title).first()
                if image is None:
                    with path.open('rb') as source:
                        image = Image.objects.create(title=title, file=ImageFile(source, name=path.name))
                if relation is not None and not relation.filter(image=image).exists():
                    last = relation.order_by('-sort_order').first()
                    relation.create(image=image, sort_order=(last.sort_order or 0) + 1 if last else 0)
                    added += 1
                    changed = True
                if folder.name.startswith('promo-'):
                    # Заполняется только отдельное мобильное фото, десктопное не меняется.
                    Promotion.objects.filter(slug=folder.name[6:], mobile_image=None).update(mobile_image=image)
                if folder.name.startswith('service-'):
                    service = Service.objects.filter(slug=folder.name[8:]).first()
                    if service:
                        service.gallery_images.add(image)
            if changed:
                page.save_revision().publish()
        self.stdout.write(self.style.SUCCESS(f'Добавлены фотографии: {added}.'))
