"""05.10: remove the superseded adjective only from approved homepage copy."""
import importlib
import re
from django.db import migrations

OLD = importlib.import_module('home.migrations.0007_approved_home_about_copy').NEW
NEW = OLD.replace('богатый и душистый питомник.', 'душистый питомник.')


def replace_copy(value):
    return re.sub(r'(<p\b[^>]*>)(.*?)</p>',
                  lambda match: match[1] + NEW + '</p>' if match[2] == OLD else match[0],
                  value or '', flags=re.S)


def update_copy(apps, schema_editor):
    HomePage = apps.get_model('home', 'HomePage')
    Revision = apps.get_model('wagtailcore', 'Revision')
    alias = schema_editor.connection.alias
    for page in HomePage.objects.using(alias).filter(slug='home').iterator():
        updated = replace_copy(page.about_text)
        if updated != page.about_text:
            HomePage.objects.using(alias).filter(pk=page.pk, about_text=page.about_text).update(about_text=updated)
        else:
            print('About 05.10: unchanged/editor copy preserved, page id=', page.pk)
        revision = Revision.objects.using(alias).filter(pk=page.latest_revision_id).first()
        if revision:
            content = dict(revision.content)
            draft = content.get('about_text', '')
            updated_draft = replace_copy(draft)
            if draft != updated_draft:
                content['about_text'] = updated_draft
                Revision.objects.using(alias).filter(pk=revision.pk).update(content=content)


class Migration(migrations.Migration):
    dependencies = [('home', '0007_approved_home_about_copy')]
    operations = [migrations.RunPython(update_copy, migrations.RunPython.noop)]
