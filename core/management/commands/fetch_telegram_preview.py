"""Превью последних постов канала для «Рассылки» (docs/dop-stranicy/20).

Берёт публичную страницу https://t.me/s/<канал> из ссылки Telegram в
настройках сайта, сохраняет до шести последних постов с текстом. Сеть
недоступна или разметка изменилась — команда пишет предупреждение и
ничего не удаляет: страница остаётся с прежними превью или без них.
"""
import html
import re
from datetime import datetime
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from django.core.management.base import BaseCommand

LIMIT = 6
BLOCK = re.compile(r'<div class="tgme_widget_message_wrap')
POST = re.compile(r'data-post="([^"/]+/\d+)"')
DATE = re.compile(r'<time[^>]+datetime="([^"]+)"')
TEXT = re.compile(r'tgme_widget_message_text[^>]*>(.*?)</div>', re.S)
PHOTO = re.compile(r"tgme_widget_message_photo_wrap[^>]+background-image:url\('([^']+)'\)")


def parse(page):
    """Список постов: url, дата, текст, фото. Посты без текста пропускаются."""
    posts = []
    for block in BLOCK.split(page)[1:]:
        post, date = POST.search(block), DATE.search(block)
        text = TEXT.search(block)
        if not (post and date and text):
            continue
        body = re.sub(r"<br\s*/?>", "\n", text.group(1))
        body = html.unescape(re.sub(r"<[^>]+>", "", body)).strip()
        if not body:
            continue
        photo = PHOTO.search(block)
        posts.append({
            "url": f"https://t.me/{post.group(1)}",
            "published_at": datetime.fromisoformat(date.group(1)),
            "text": body,
            "image_url": photo.group(1) if photo else "",
        })
    return posts


def channel_name(url):
    parts = urlsplit(url or "")
    if (parts.hostname or "").removeprefix("www.") not in {"t.me", "telegram.me"}:
        return ""
    return parts.path.strip("/").split("/")[-1]


class Command(BaseCommand):
    help = "Обновить превью последних постов Telegram-канала для страницы «Рассылка»."

    def handle(self, *args, **options):
        from wagtail.models import Site

        from core.models import ChannelPost, SiteSettings

        site = Site.objects.filter(is_default_site=True).first()
        name = channel_name(SiteSettings.for_site(site).telegram_url) if site else ""
        if not name:
            self.stdout.write("Ссылка на Telegram-канал не заполнена — превью не обновляются.")
            return
        try:
            request = Request(f"https://t.me/s/{name}", headers={"User-Agent": "Mozilla/5.0"})
            page = urlopen(request, timeout=15).read().decode("utf-8", "replace")
        except Exception as error:  # сеть, TLS, HTTP: старт сайта не должен падать
            self.stderr.write(f"Канал недоступен ({error}); превью оставлены как были.")
            return
        posts = parse(page)
        if not posts:
            self.stderr.write("Посты не найдены — разметка t.me могла измениться; превью оставлены как были.")
            return
        for post in sorted(posts, key=lambda item: item["published_at"], reverse=True)[:LIMIT]:
            ChannelPost.objects.update_or_create(url=post["url"], defaults=post)
        stale = ChannelPost.objects.order_by("-published_at").values_list("pk", flat=True)[LIMIT:]
        ChannelPost.objects.filter(pk__in=list(stale)).delete()
        self.stdout.write(f"Превью канала обновлены: {min(len(posts), LIMIT)}.")
