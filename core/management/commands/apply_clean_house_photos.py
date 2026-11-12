"""Relink only checksum-verified imported photos to their clean originals."""
import json
from hashlib import sha256
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models.signals import post_save
from wagtail.images import get_image_model

from houses.models import HousePage


def load_records(root):
    return json.loads((root / 'core/house_clean_manifest.json').read_text(encoding='utf-8'))


class Command(BaseCommand):
    help = 'Use exact clean house originals; preserve old files and editor changes.'

    @transaction.atomic
    def handle(self, *args, **options):
        root = Path(settings.BASE_DIR)
        records = load_records(root)
        Image = get_image_model()
        for page in HousePage.objects.select_for_update():
            if page.has_unpublished_changes:
                self.stdout.write(f'{page.slug}: preserved unpublished changes')
                continue
            mapping = {r['old_title']: r for r in records if r['house'] == page.slug}
            changed = 0
            for row in page.gallery_images.select_related('image'):
                record = mapping.get(row.image.title)
                if record is None:
                    continue
                with row.image.file.open('rb') as original:
                    if sha256(original.read()).hexdigest() != record['old_sha256']:
                        continue
                title = f"BS clean 20261112 {page.slug} {record['source']}"
                clean = Image.objects.filter(title=title).first()
                if clean is None:
                    path = root / 'config/static/img/house-clean-20261112' / record['file']
                    clean = Image(title=title)
                    with path.open('rb') as source:
                        clean.file.save(path.name, File(source), save=False)
                    # Startup already warms images in the background. Avoid
                    # holding publication for all editor-upload renditions.
                    from core.image_signals import prepare_editor_image
                    post_save.disconnect(sender=Image, dispatch_uid='bs_prepare_editor_image')
                    try:
                        clean.save()
                    finally:
                        post_save.connect(prepare_editor_image, sender=Image,
                                          dispatch_uid='bs_prepare_editor_image')
                row.image = clean
                row.save(update_fields=['image'])
                changed += 1
            if changed:
                page.save_revision().publish()
            self.stdout.write(f'{page.slug}: {changed} verified replacements')
