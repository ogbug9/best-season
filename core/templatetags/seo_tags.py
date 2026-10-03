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
