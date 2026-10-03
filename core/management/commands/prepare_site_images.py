"""Discover actual template usage and warm it outside HTTP requests."""
from collections import defaultdict
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.http.request import validate_host
from django.test import RequestFactory
from wagtail.images import get_image_model
from wagtail.models import Page, Site
from core.templatetags.media_tags import rendition_plan


def page_plan(pages):
    plan = set()
    token = rendition_plan.set(plan)
    try:
        site = Site.objects.filter(is_default_site=True).first()
        host = site.hostname if site else 'localhost'
        # The configured canonical domain may not be enabled yet. Render on a
        # permitted host without changing the Site, DNS or public validation.
        if not validate_host(host, settings.ALLOWED_HOSTS):
            hosts = [item for item in settings.ALLOWED_HOSTS if item and item != '*']
            host = next((item for item in hosts if not item.startswith('.')), None)
            if host is None and hosts:
                host = 'preview' + hosts[0]
            if host is None:
                raise CommandError('Для подготовки фото нужен разрешённый хост в ALLOWED_HOSTS.')
        for page in pages:
            request = RequestFactory().get(page.url or '/', HTTP_HOST=host)
            request.session = {}
            request.bs_utm = {}
            request.is_preview = False
            response = page.specific.serve(request)
            if hasattr(response, 'render'):
                response.render()
    finally:
        rendition_plan.reset(token)
    return plan


def prepare(plan):
    grouped = defaultdict(set)
    for image_id, spec in plan:
        grouped[image_id].add(spec)
    failures = 0
    for image in get_image_model().objects.filter(pk__in=grouped).iterator():
        for spec in sorted(grouped[image.pk]):
            try:
                rendition = image.get_rendition(spec)
                # Repair DB rows pointing to missing files (e.g. after transfer).
                if not rendition.file.storage.exists(rendition.file.name):
                    rendition.delete()
                    image.get_rendition(spec)
            except Exception:
                failures += 1
    return failures


class Command(BaseCommand):
    help = 'Заранее подготовить только используемые страницами WebP/JPEG и мобильные варианты.'

    def add_arguments(self, parser):
        parser.add_argument('--page', type=int, help='Подготовить одну страницу после публикации.')
        parser.add_argument('--plan-only', action='store_true')
        parser.add_argument('--strict', action='store_true', help='Завершиться с ошибкой при недоступном исходнике.')

    def handle(self, *args, **options):
        pages = Page.objects.filter(pk=options['page']) if options['page'] else Page.objects.live().filter(depth__gte=2)
        plan = page_plan(pages)
        self.stdout.write(f'Фото: {len({p[0] for p in plan})}; используемых вариантов: {len(plan)}.')
        if not options['plan_only']:
            failures = prepare(plan)
            if failures:
                message = f'Не подготовлено вариантов: {failures}. Проверьте наличие файлов media.'
                if options['strict']:
                    raise CommandError(message)
                self.stderr.write(self.style.WARNING(message))
                return
            self.stdout.write(self.style.SUCCESS('Используемые варианты готовы.'))
