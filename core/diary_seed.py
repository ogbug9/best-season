"""«Дневник Сезона» (20.10): перевод временных ContentPage в DiaryIndexPage/DiaryEntryPage.

Адреса не меняются: /o-nas/dnevnik/ и три записи (novyj-god, ayka, zheltoe-chudo).
Запускается из seed_pages (run.py) и ничего не делает, если дневник уже нового типа —
правки редактора не перезаписываются.
"""
from django.utils import timezone

from core.temp_pages import DIARY, DIARY_INDEX

TITLE = "Дневник Сезона"
# Текст из макета News (совпадает с блоком «Дневник» на «О нас»).
INTRO = ("Что у нас происходит: новые постройки, сезонные затеи, наши рубрики "
         "и места по соседству, куда стоит съездить.")
OLD_INTRO = "Что у нас происходит: новые постройки, сезонные акции, наши рубрики и места по соседству."


def _body(entry):
    blocks = [("paragraph", f"<p>{text}</p>") for text in entry["paras"]]
    if entry.get("quote"):
        blocks.insert(1, ("quote", entry["quote"]))
    return blocks


def ensure_diary(log=print):
    """Создаёт дневник нового типа; возвращает число созданных страниц."""
    from wagtail.models import Page

    from core.models import DiaryEntryPage, DiaryIndexPage, image_titled

    if DiaryIndexPage.objects.exists():
        _fill_covers(log)
        return 0
    old = Page.objects.filter(slug=DIARY_INDEX).first()
    parent = old.get_parent() if old else Page.objects.filter(slug="o-nas").first()
    if parent is None:
        log("Нет раздела «О нас» — дневник не создан")
        return 0

    kept = {}
    old_intro = ""
    if old:
        for page in [old, *old.get_children()]:
            kept[page.slug] = (page.seo_title, page.search_description, page.first_published_at)
        old_intro = getattr(old.specific, "intro", "")
        old.delete()  # временные страницы: их наполнение живёт в core/temp_pages.py

    seo_title, description, _ = kept.get(DIARY_INDEX, ("", "", None))
    intro = old_intro if old_intro and old_intro != OLD_INTRO else INTRO
    index = DiaryIndexPage(title=TITLE, slug=DIARY_INDEX, intro=intro, show_in_menus=False,
                           seo_title=seo_title, search_description=description or INTRO)
    parent.add_child(instance=index)
    index.save_revision().publish()
    created = 1
    for entry in DIARY:
        seo_title, description, published = kept.get(entry["slug"], ("", "", None))
        page = DiaryEntryPage(
            title=entry["title"], slug=entry["slug"], show_in_menus=False,
            date=timezone.localdate(published) if published else timezone.localdate(),
            cover=image_titled(entry["image"]), lead=entry["lead"], body=_body(entry),
            seo_title=seo_title, search_description=description or entry["lead"],
        )
        if page.cover is None:
            log(f"  дневник: нет фото «{entry['image']}» для /{entry['slug']}/ — обложку добавить в админке")
        index.add_child(instance=page)
        page.save_revision().publish()
        created += 1
    log(f"  дневник: {'перенесён' if old else 'создан'} ({created} стр.)")
    return created


def _fill_covers(log):
    """Обложка записи из сида, если картинка появилась в базе позже; правку редактора не трогает."""
    from core.models import DiaryEntryPage, image_titled

    for entry in DIARY:
        page = DiaryEntryPage.objects.filter(slug=entry["slug"], cover__isnull=True).first()
        if page is None or page.revisions.count() > 1:  # редактор уже правил запись
            continue
        image = image_titled(entry["image"])
        if image:
            page.cover = image
            page.save_revision().publish()
            log(f"  дневник: обложка «{page.title}»")
