"""«Дневник Сезона» (20.10): перевод временных ContentPage в DiaryIndexPage/DiaryEntryPage.

Запускается из seed_pages (run.py). Сохраняет адреса и редакторские записи.
"""
from django.utils import timezone
from django.utils.html import format_html

from core.diary_edition import ARTICLES
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

    index = DiaryIndexPage.objects.first()
    if index is not None:
        _fill_covers(log)
        return _ensure_edition(index)
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
    created += _ensure_edition(index)
    log(f"  дневник: {'перенесён' if old else 'создан'} ({created} стр.)")
    return created


def _ensure_edition(index):
    from core.models import DiaryEntryPage

    children = index.get_children()
    duck = DiaryEntryPage.objects.child_of(index).filter(slug="zheltoe-chudo").first()
    if (duck and duck.live and not duck.has_unpublished_changes
            and duck.title == "История о маленьком жёлтом японском чуде"):
        duck.title = "История о маленьком жёлтом июньском чуде"
        duck.save_revision().publish()

    existing = set(children.values_list("slug", flat=True))
    for slug, (title, lead, paragraphs) in ARTICLES.items():
        if slug in existing:
            continue
        page = DiaryEntryPage(
            title=title, slug=slug, show_in_menus=False, date=timezone.localdate(),
            lead=lead, body=[("paragraph", format_html("<p>{}</p>", text)) for text in paragraphs],
        )
        index.add_child(instance=page)
        page.save_revision().publish()
    return len(ARTICLES.keys() - existing)


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
