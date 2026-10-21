"""06.10: remove the nursery name from «О нас» (decision of Sofia/Nastya).

Only the exact approved phrase is changed — in the live page and in its latest
revision — so an editor's own wording is never overwritten.
"""
import json
from django.db import migrations

OLD = 'рядом питомник «Долина роз»'
NEW = 'рядом питомник'


def clean(data):
    """Replace the phrase inside the intro paragraphs of a raw stream; return (data, changed)."""
    changed = False
    for block in data or []:
        value = block.get('value') if isinstance(block, dict) else None
        if not isinstance(value, dict):
            continue
        intro = value.get('intro')
        if isinstance(intro, list):
            for i, item in enumerate(intro):
                text = item.get('value') if isinstance(item, dict) else item
                if isinstance(text, str) and OLD in text:
                    text = text.replace(OLD, NEW)
                    if isinstance(item, dict):
                        item['value'] = text
                    else:
                        intro[i] = text
                    changed = True
    return data, changed


def update_copy(apps, schema_editor):
    ContentPage = apps.get_model('core', 'ContentPage')
    Revision = apps.get_model('wagtailcore', 'Revision')
    alias = schema_editor.connection.alias
    field = ContentPage._meta.get_field('about_content')
    for page in ContentPage.objects.using(alias).filter(slug='o-nas').iterator():
        raw, changed = clean(json.loads(json.dumps(list(page.about_content.raw_data), default=str)))
        if changed:
            ContentPage.objects.using(alias).filter(pk=page.pk).update(about_content=field.to_python(json.dumps(raw)))
        else:
            print('About 06.10: nursery phrase not found, editor copy preserved, page id=', page.pk)
        revision = Revision.objects.using(alias).filter(pk=page.latest_revision_id).first()
        if revision and isinstance(revision.content, dict) and revision.content.get('about_content'):
            content = dict(revision.content)
            stream = content['about_content']
            data = json.loads(stream) if isinstance(stream, str) else stream
            data, changed = clean(data)
            if changed:
                content['about_content'] = json.dumps(data, ensure_ascii=False) if isinstance(stream, str) else data
                Revision.objects.using(alias).filter(pk=revision.pk).update(content=content)


class Migration(migrations.Migration):
    dependencies = [('core', '0023_whatsapp_contact')]
    operations = [migrations.RunPython(update_copy, migrations.RunPython.noop)]
