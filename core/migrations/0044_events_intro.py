from django.db import migrations


OLD_INTRO = "Праздники, съёмки, корпоративные заезды."
NEW_INTRO = "Поводы, ради которых точно стоит приехать."


def update_events_intro(apps, schema_editor):
    alias = schema_editor.connection.alias
    content_page = apps.get_model("core", "ContentPage")
    revision = apps.get_model("wagtailcore", "Revision")
    pages = content_page.objects.using(alias).filter(slug="meropriyatiya", intro=OLD_INTRO)
    for page in pages:
        pages.filter(pk=page.pk).update(intro=NEW_INTRO)
        revisions = revision.objects.using(alias).filter(pk=page.latest_revision_id)
        latest = revisions.first()
        if latest and latest.content.get("intro") == OLD_INTRO:
            revisions.update(content={**latest.content, "intro": NEW_INTRO})


class Migration(migrations.Migration):
    dependencies = [("core", "0043_legal_domain")]
    operations = [migrations.RunPython(update_events_intro, migrations.RunPython.noop)]
