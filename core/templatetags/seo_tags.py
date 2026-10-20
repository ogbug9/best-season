"""JSON-LD from data, with safe script escaping and configured Wagtail URLs."""
import json
from urllib.parse import urljoin

from django import template
from django.utils.safestring import mark_safe

register = template.Library()


def script(data):
    value = json.dumps(data, ensure_ascii=False).replace('<', '\\u003C').replace('>', '\\u003E').replace('&', '\\u0026')
    return mark_safe(f'<script type="application/ld+json">{value}</script>')


@register.simple_tag(takes_context=True)
def canonical_url(context):
    request, page = context['request'], context.get('page')
    return page.get_full_url(request) if page else request.build_absolute_uri(request.path)


@register.simple_tag(takes_context=True)
def absolute_media_url(context, url):
    return urljoin(context['request'].build_absolute_uri('/'), url)


@register.simple_tag(takes_context=True)
def breadcrumbs_schema(context):
    page, request = context.get('page'), context['request']
    if not page:
        return ''
    ancestors = list(page.get_ancestors().live().filter(depth__gte=2)) + [page]
    if len(ancestors) < 2:
        return ''
    items = [{'@type': 'ListItem', 'position': i + 1, 'name': node.title, 'item': node.get_full_url(request)}
             for i, node in enumerate(ancestors)]
    return script({'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': items})


@register.simple_tag(takes_context=True)
def organization_schema(context):
    from core.models import SiteSettings
    request, site = context['request'], context.get('current_site')
    config = SiteSettings.for_request(request)
    data = {'@context': 'https://schema.org', '@type': 'LodgingBusiness',
            'name': site.site_name if site else '', 'url': site.root_url if site else request.build_absolute_uri('/')}
    if config.phone:
        data['telephone'] = config.phone
    if config.address:
        data['address'] = {'@type': 'PostalAddress', 'streetAddress': config.address}
    return script(data)


@register.simple_tag(takes_context=True)
def accommodation_schema(context):
    page = context['page']
    data = {'@context': 'https://schema.org', '@type': 'Accommodation', 'name': page.title,
            'url': canonical_url(context), 'occupancy': {'@type': 'QuantitativeValue', 'maxValue': page.capacity}}
    if page.area:
        data['floorSize'] = {'@type': 'QuantitativeValue', 'value': float(page.area), 'unitCode': 'MTK'}
    data['amenityFeature'] = [{'@type': 'LocationFeatureSpecification', 'name': item.name, 'value': True}
                            for item in page.amenities.all()]
    return script(data)


# Превью для соцсетей: JPEG 1200×630 (20.10, «Дневник Сезона»).
OG_SPEC = 'fill-1200x630|format-jpeg|jpegquality-85'


@register.simple_tag
def og_rendition(image):
    """Готовый вариант 1200×630; в проде создаётся prepare_site_images, а не запросом гостя."""
    from django.conf import settings
    from core.templatetags.media_tags import rendition_plan

    if not image:
        return None
    plan = rendition_plan.get()
    if plan is not None:
        plan.add((image.pk, OG_SPEC))
        return None
    rendition = image.renditions.filter(filter_spec=OG_SPEC).first()
    if rendition is None and getattr(settings, 'GENERATE_IMAGE_RENDITIONS_ON_REQUEST', False):
        try:
            rendition = image.get_rendition(OG_SPEC)
        except Exception:
            return None
    return rendition


@register.simple_tag(takes_context=True)
def article_schema(context, image_url=''):
    page, site = context['page'], context.get('current_site')
    publisher = {'@type': 'Organization', 'name': site.site_name if site else 'Лучший Сезон'}
    data = {'@context': 'https://schema.org', '@type': 'Article', 'headline': page.title,
            'description': page.search_description or page.lead,
            'datePublished': page.date.isoformat(), 'author': publisher, 'publisher': publisher,
            'mainEntityOfPage': canonical_url(context)}
    if page.last_published_at:
        data['dateModified'] = page.last_published_at.isoformat()
    if image_url:
        data['image'] = [image_url]
    return script(data)
