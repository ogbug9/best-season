"""Backfill new fields once. Never overwrite editable bodies, drafts or images."""
import json
from hashlib import sha256
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from wagtail.images import get_image_model

from core.models import ContentPage, InterfaceText
from core.about_content import PILLARS, VALUES, PETS, DIARY
from core.templatetags.legal_docs import LEGAL_PDFS


class Command(BaseCommand):
    help = 'Однократно заполнить новые CMS-поля из текущих текстов и исходных PDF.'

    @transaction.atomic
    def handle(self, *args, **options):
        folder = Path(settings.BASE_DIR) / 'core/data'
        from home.models import HomePage
        for home in HomePage.objects.select_for_update().filter(mobile_photos_initialized=False):
            fields = ['mobile_photos_initialized']
            for field, filename in (('about_mobile_image', 'home-about-mobile.webp'), ('quote_mobile_image', 'home-quote-mobile.webp')):
                if not getattr(home, field):
                    image = self.static_image(f'BS {filename}', Path(settings.BASE_DIR)/'config/static/img'/filename)
                    setattr(home, field, image)
                    fields.append(field)
            home.mobile_photos_initialized = True
            home.save(update_fields=fields)
            self.extend_revisions(home, fields)
        for key, item in json.loads((folder / 'interface_text.json').read_text(encoding='utf-8')).items():
            InterfaceText.objects.get_or_create(key=key, defaults=item)
        for page in ContentPage.objects.select_for_update():
            fields = []
            if page.slug == 'o-nas' and not page.about_initialized:
                if not page.about_content:
                    data = json.loads((folder / 'about.json').read_text(encoding='utf-8'))
                    data['history_photos'] = [self.photo(key, alt) for key, alt in (
                        ('aerial', 'Вид глэмпинга сверху'), ('story-moss', 'Рука на мягком лесном мху'),
                        ('story-terrace', 'Терраса домика и зелёная территория'), ('story-season', 'Прогулка на природе'))]
                    for name, items in (('pillars', PILLARS), ('values', VALUES), ('pets', PETS), ('diary', DIARY)):
                        data[name] = []
                        for item in items:
                            card = {k: v for k, v in item.items() if k not in ('image', 'journey')}
                            card.update(self.photo(item['image'], '' if name == 'values' else item.get('title', item.get('name', ''))))
                            data[name].append(card)
                    page.about_content = [{'type': 'content', 'value': data}]
                    fields.append('about_content')
                page.about_initialized = True
                fields.append('about_initialized')
            pdf_path = LEGAL_PDFS.get(page.slug)
            if pdf_path and not page.legal_source_sha256:
                source = Path(settings.BASE_DIR) / 'config/static' / pdf_path
                data = json.loads((folder / 'legal' / (source.stem + '.json')).read_text(encoding='utf-8'))
                if sha256(source.read_bytes()).hexdigest() != data['sha256']:
                    raise CommandError(f'Исходный PDF изменился: {source.name}; требуется повторная сверка текста.')
                if not page.legal_body:
                    page.legal_body = data['blocks']
                    fields.append('legal_body')
                page.legal_source_sha256 = data['sha256']
                fields.append('legal_source_sha256')
            if fields:
                page.save(update_fields=fields)
                # Existing drafts predate these fields. Extend only missing/empty
                # new keys so publishing an old draft cannot erase the backfill.
                self.extend_revisions(page, fields)
                self.stdout.write(f'Новые поля заполнены: {page.slug}')
        # Deliberately do not change consent_version or any original body field.

    def photo(self, key, alt):
        path = Path(settings.BASE_DIR) / 'config/static/img/about' / f'{key}.webp'
        image = self.static_image(f'BS About {key}', path)
        return {'image': image.pk, 'crop': key, 'alt': alt}

    def static_image(self, title, path):
        image_model = get_image_model()
        image = image_model.objects.filter(title=title).first()
        if image is None:
            image = image_model(title=title)
            with path.open('rb') as source:
                image.file.save(path.name, File(source), save=False)
            image.save()
        return image

    def extend_revisions(self, page, fields):
        serialized = page.serializable_data()
        for revision in page.revisions.all():
            changed = False
            for field in fields:
                if not revision.content.get(field):
                    revision.content[field] = serialized[field]
                    changed = True
            if changed:
                revision.save(update_fields=['content'])
