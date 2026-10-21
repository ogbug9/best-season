"""07.10: пометка «Страница в разработке» на всех страницах без макета.

Строка над заголовком (includes/in_progress_note.html). Снимается галочкой
«Раздел дополняется» на вкладке «Настройки» страницы.
"""
from django.db import migrations

CONTENT_SLUGS = ("chem-zanyatsya", "razvlecheniya", "meropriyatiya", "vyezdy-kompaniy", "partneram",
                 "pravila-bronirovaniya", "rassylka")
MODELS = [("core", "TerritoryPage"), ("core", "NearbyPage"), ("core", "DirectionsPage"), ("core", "GalleryPage"),
          ("core", "FaqPage"), ("core", "ContactsPage"), ("services", "ServicesPage"), ("reviews", "ReviewsPage")]


def turn_on(apps, schema_editor):
    alias = schema_editor.connection.alias
    Revision = apps.get_model("wagtailcore", "Revision")
    querysets = [apps.get_model("core", "ContentPage").objects.using(alias).filter(slug__in=CONTENT_SLUGS)]
    querysets += [apps.get_model(app, name).objects.using(alias).all() for app, name in MODELS]
    for queryset in querysets:
        for page in queryset:
            type(page).objects.using(alias).filter(pk=page.pk).update(in_progress=True)
            revision = Revision.objects.using(alias).filter(pk=page.latest_revision_id).first()
            if revision and isinstance(revision.content, dict):
                Revision.objects.using(alias).filter(pk=revision.pk).update(content={**revision.content, "in_progress": True})


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0037_dev_strip"),
        ("services", "0008_service_includes"),
        ("reviews", "0005_dev_strip"),
        ("wagtailcore", "0097_baselogentry_uuid_action_timestamp_indexes"),
    ]
    operations = [migrations.RunPython(turn_on, migrations.RunPython.noop)]
