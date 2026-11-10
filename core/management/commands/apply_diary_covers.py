"""Import the nine covers embedded in the approved News SVG."""

from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand
from django.db import transaction
from wagtail.images import get_image_model

from core.diary_edition import EDITION_ORDER
from core.models import DiaryEntryPage, DiaryIndexPage
from core.temp_pages import DIARY


class Command(BaseCommand):
    help = "Attach the approved Season Diary covers to the first edition"

    @transaction.atomic
    def handle(self, *args, **options):
        index = DiaryIndexPage.objects.live().filter(slug="dnevnik").first()
        if index is None:
            return
        image_model = get_image_model()
        legacy = {entry["slug"]: entry["image"] for entry in DIARY}
        directory = Path(settings.BASE_DIR) / "config/static/img/diary-edition"
        entries = DiaryEntryPage.objects.select_for_update().live().child_of(index).filter(slug__in=EDITION_ORDER)
        for entry in entries:
            if entry.has_unpublished_changes:
                continue
            if entry.cover_id and entry.cover.title != legacy.get(entry.slug):
                continue
            title = f"BS News {entry.slug}"
            image = image_model.objects.filter(title=title).first()
            if image is None:
                path = directory / f"{entry.slug}.webp"
                image = image_model(title=title)
                with path.open("rb") as source:
                    image.file.save(path.name, File(source), save=False)
                image.save()
            entry.cover = image
            entry.save_revision().publish()
            self.stdout.write(entry.slug)
