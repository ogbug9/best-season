# -*- coding: utf-8 -*-
"""«Уютный домик-лофт» → «Уютный домик-лофт №1» на странице «Первый домик».

Правим и саму страницу, и JSON её ревизий: публикация сохранённого
черновика подставила бы описание из ревизии и откатила замену.
"""
import json

from django.db import migrations

TITLE = "Первый домик"
OLD = "Уютный домик-лофт с собственной сауной"
NEW = "Уютный домик-лофт №1 с собственной сауной"


def _replace(apps, old, new):
    ContentType = apps.get_model("contenttypes", "ContentType")
    HousePage = apps.get_model("houses", "HousePage")
    Revision = apps.get_model("wagtailcore", "Revision")

    pages = list(HousePage.objects.filter(title=TITLE))
    if not pages:
        return
    for page in pages:
        if old in (page.description or ""):
            page.description = page.description.replace(old, new)
            page.save(update_fields=["description"])

    content_type = ContentType.objects.filter(
        app_label="houses", model="housepage"
    ).first()
    if content_type is None:
        return
    revisions = Revision.objects.filter(
        content_type=content_type,
        object_id__in=[str(page.pk) for page in pages],
    )
    for revision in revisions:
        content = revision.content
        # На всякий случай: в старых базах content мог остаться строкой
        if isinstance(content, str):
            try:
                content = json.loads(content)
            except ValueError:
                continue
        if not isinstance(content, dict):
            continue
        description = content.get("description")
        if not isinstance(description, str) or old not in description:
            continue
        content["description"] = description.replace(old, new)
        revision.content = content
        revision.save(update_fields=["content"])


def forwards(apps, schema_editor):
    _replace(apps, OLD, NEW)


def backwards(apps, schema_editor):
    _replace(apps, NEW, OLD)


class Migration(migrations.Migration):

    dependencies = [
        ("houses", "0006_alter_housesleepingplace_icon"),
        ("wagtailcore", "0089_log_entry_data_json_null_to_object"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
