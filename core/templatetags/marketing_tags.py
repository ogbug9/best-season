from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
from django import template

register = template.Library()
PUBLIC_HOSTS = {'t.me', 'telegram.me', 'wa.me', 'api.whatsapp.com', 'vk.com', 'vk.ru',
                'instagram.com', 'tiktok.com', 'avito.ru', 'ostrovok.ru', 'booking.com',
                'travel.yandex.ru', 'yandex.ru', '2gis.ru'}


@register.simple_tag
def marketing_url(url, placement='site'):
    parts = urlsplit(str(url or ''))
    host = (parts.hostname or '').lower().removeprefix('www.')
    if parts.scheme not in ('http', 'https') or host not in PUBLIC_HOSTS:
        return url
    pairs = parse_qsl(parts.query, keep_blank_values=True)
    if any(segment in {'pay', 'payment', 'payments', 'checkout', 'sdk'} for segment in parts.path.lower().split('/')) or any(
        key.lower() in {'payment_id', 'payment', 'token', 'signature', 'order_id'} for key, _ in pairs
    ):
        return url
    # Maps/reviews links only. Do not annotate SDK or payment endpoints.
    if host == 'yandex.ru' and not parts.path.startswith('/maps'):
        return url
    query = [(k, v) for k, v in pairs if not k.startswith('utm_')]
    query += [('utm_source', 'best_season'), ('utm_medium', 'referral'),
              ('utm_campaign', 'outbound'), ('utm_content', str(placement))]
    return urlunsplit(parts._replace(query=urlencode(query)))
