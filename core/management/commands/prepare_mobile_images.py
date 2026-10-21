"""Подготовить мобильные фото до запуска HTTP-сервера."""
from django.core.management.base import BaseCommand

from core.templatetags.media_tags import mobile_specs
from home.models import HomeSlide
from promotions.models import Promotion


class Command(BaseCommand):
    help = 'Подготовить готовые мобильные rendition первого экрана и акций.'

    def handle(self, *args, **options):
        seen = set()
        count = 0
        for model, preset in ((HomeSlide, 'hero_mobile'), (Promotion, 'promo_mobile')):
            for item in model.objects.exclude(image=None).select_related('image'):
                image = getattr(item, 'mobile_image', None) or item.image
                key = (image.pk, preset)
                if key in seen:
                    continue
                seen.add(key)
                for _, _, spec in mobile_specs(preset):
                    image.get_rendition(spec)
                    count += 1
        self.stdout.write(self.style.SUCCESS(f'Мобильные rendition готовы: {count}.'))
