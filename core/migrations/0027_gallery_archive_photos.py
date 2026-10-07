"""07.10: пустая «Галерея» получает уже загруженные фото архива.

На проде фото «BS archive gallery/*» есть в библиотеке, но к странице не
привязаны: повторный импорт с --if-not-applied уже загруженные кадры не
связывает. Привязываем, только если в галерее нет ни одного фото, — выбор
редактора не трогаем. Ревизия обновляется тоже, иначе следующая публикация
из админки удалит привязку.
"""
from django.db import migrations

PREFIX = 'BS archive gallery/'


def link(apps, schema_editor):
    alias = schema_editor.connection.alias
    GalleryPage = apps.get_model('core', 'GalleryPage')
    GalleryPhoto = apps.get_model('core', 'GalleryPhoto')
    Image = apps.get_model('wagtailimages', 'Image')
    Revision = apps.get_model('wagtailcore', 'Revision')
    images = list(Image.objects.using(alias).filter(title__startswith=PREFIX).order_by('title'))
    if not images:
        return
    for page in GalleryPage.objects.using(alias).all():
        if GalleryPhoto.objects.using(alias).filter(page=page).exists():
            continue
        photos = [GalleryPhoto.objects.using(alias).create(page=page, image=image, sort_order=i)
                  for i, image in enumerate(images)]
        revision = Revision.objects.using(alias).filter(pk=page.latest_revision_id).first()
        if revision and isinstance(revision.content, dict) and not revision.content.get('photos'):
            content = dict(revision.content)
            content['photos'] = [{'pk': photo.pk, 'sort_order': photo.sort_order, 'page': page.pk,
                                  'image': photo.image_id, 'alt': '', 'is_large': False} for photo in photos]
            Revision.objects.using(alias).filter(pk=revision.pk).update(content=content)


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0026_in_progress'),
        ('wagtailimages', '0027_image_description'),
        ('wagtailcore', '0097_baselogentry_uuid_action_timestamp_indexes'),
    ]
    operations = [migrations.RunPython(link, migrations.RunPython.noop)]
