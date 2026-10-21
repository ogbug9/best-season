"""04.10.2026: Sofia's approved paragraph; preserve other/editor-authored copy."""
import re
from html import unescape

from django.db import migrations

OLD = (
    'Территория глэмпинга поистине уникальна — с трёх сторон нас '
    'окружает лес и небольшая местная речка Скнижка, а рядом раскинулся '
    'богатый и душистый питомник «Долина роз». Также наш район является '
    'самым озонированным в Тульской области, воздух здесь чище и плотнее, '
    'так что здесь отлично можно выспаться. А ещё у нас есть собственная '
    'контактная ферма, которая порадует свежими и натуральными продуктами '
    'к вашему завтраку.'
)
NEW = (
    'Территория глэмпинга уникальна — с трех сторон нас '
    'окружает лес и небольшая местная речка Скнижка, а рядом раскинулся '
    'богатый и душистый питомник. Также наш район является '
    'самым озонированным в Тульской области, воздух здесь чище и плотнее, '
    'так что здесь отлично можно выспаться. А ещё у нас есть собственная '
    'контактная ферма, которая порадует свежими и натуральными продуктами '
    'к вашему завтраку.'
)


def normalize(text):
    text = unescape(re.sub(r'<br\s*/?>', ' ', text, flags=re.I))
    text = re.sub(r'<[^>]*>', '', text)
    return ' '.join(text.split()).replace('ё', 'е')


def replace_approved_paragraph(value):
    def replace(match):
        if normalize(match[2]) == normalize(OLD):
            return match[1] + NEW + '</p>'
        return match[0]
    return re.sub(r'(<p\b[^>]*>)(.*?)</p>', replace, value or '', flags=re.S)


def update_copy(apps, schema_editor):
    HomePage = apps.get_model('home', 'HomePage')
    Revision = apps.get_model('wagtailcore', 'Revision')
    alias = schema_editor.connection.alias
    for page in HomePage.objects.using(alias).all().iterator():
        updated = replace_approved_paragraph(page.about_text)
        if updated != page.about_text:
            HomePage.objects.using(alias).filter(pk=page.pk).update(about_text=updated)
        # Keep the latest draft's unrelated edits. Older revision history stays.
        revision = Revision.objects.using(alias).filter(pk=page.latest_revision_id).first()
        if revision:
            content = dict(revision.content)
            draft_text = content.get('about_text', '')
            updated_draft = replace_approved_paragraph(draft_text)
            if updated_draft != draft_text:
                content['about_text'] = updated_draft
                Revision.objects.using(alias).filter(pk=revision.pk).update(content=content)


class Migration(migrations.Migration):
    dependencies = [
        ('home', '0006_homepage_about_mobile_image_and_more'),
        ('wagtailcore', '0097_baselogentry_uuid_action_timestamp_indexes'),
    ]
    operations = [migrations.RunPython(update_copy, migrations.RunPython.noop)]
