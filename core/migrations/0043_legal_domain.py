"""Fill only the explicitly blank domains in the published legal text."""
import json

from django.db import migrations


def fill(apps, schema_editor):
    # This migration freezes the exact known placeholders and never replaces
    # an editor-supplied domain.
    replacements = {
        'oferta': (
            ('в области доменных имён https://.', 'в области доменных имён https://best-season.online.'),
            ('в области доменных имён https://,', 'в области доменных имён https://best-season.online,'),
            ('через сайт https://,', 'через сайт https://best-season.online,'),
            ('на сайте https:// с использованием', 'на сайте https://best-season.online с использованием'),
            ('по адресу https://..', 'по адресу https://best-season.online..'),
            ('на сайте https://.', 'на сайте https://best-season.online.'),
        ),
        'politika-konfidencialnosti': (
            ('сайта Оператора адрес сайта (далее', 'сайта Оператора https://best-season.online (далее'),
            ('по адресу: https:// Пользователь', 'по адресу: https://best-season.online Пользователь'),
        ),
    }

    def update_stream(slug, stream):
        data = json.loads(stream) if isinstance(stream, str) else stream
        if not isinstance(data, list):
            return stream, False
        changed = False
        for block in data:
            value = block.get('value') if isinstance(block, dict) else None
            if not isinstance(value, str):
                continue
            updated = value
            for old, new in replacements[slug]:
                updated = updated.replace(old, new)
            if slug == 'oferta' and updated.endswith('на сайте https://'):
                updated += 'best-season.online'
            if updated != value:
                block['value'] = updated
                changed = True
        return (json.dumps(data, ensure_ascii=False) if isinstance(stream, str) else data), changed

    ContentPage = apps.get_model('core', 'ContentPage')
    Revision = apps.get_model('wagtailcore', 'Revision')
    alias = schema_editor.connection.alias
    field = ContentPage._meta.get_field('legal_body')
    for page in ContentPage.objects.using(alias).filter(slug__in=replacements).iterator():
        raw = json.loads(json.dumps(list(page.legal_body.raw_data), default=str))
        updated, changed = update_stream(page.slug, raw)
        if changed:
            ContentPage.objects.using(alias).filter(pk=page.pk).update(legal_body=field.to_python(json.dumps(updated)))
        revision = Revision.objects.using(alias).filter(pk=page.latest_revision_id).first()
        if revision and isinstance(revision.content, dict) and revision.content.get('legal_body'):
            content = dict(revision.content)
            content['legal_body'], changed = update_stream(page.slug, content['legal_body'])
            if changed:
                Revision.objects.using(alias).filter(pk=revision.pk).update(content=content)


class Migration(migrations.Migration):
    dependencies = [('core', '0042_pet_fees_per_stay')]
    operations = [migrations.RunPython(fill, migrations.RunPython.noop)]
