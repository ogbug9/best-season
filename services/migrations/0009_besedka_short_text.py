"""26.10: «Что добавить» — вариант 3 карточки (Настя, одобрено Софьей 21.10).

У «Большой беседки» короткое описание сокращено, чтобы текст и кнопки стояли
на тех же уровнях, что у соседней карточки. Меняется только прежний текст —
правка редактора в админке не затирается.
"""
from django.db import migrations

OLD = "Идеальное решение для проведения мероприятий и ужинов в большой компании."
NEW = "Идеальное решение для большой компании."


def forward(apps, schema_editor):
    Service = apps.get_model("services", "Service")
    Service.objects.using(schema_editor.connection.alias).filter(
        slug="bolshaya-besedka", short_description=OLD
    ).update(short_description=NEW)


def backward(apps, schema_editor):
    Service = apps.get_model("services", "Service")
    Service.objects.using(schema_editor.connection.alias).filter(
        slug="bolshaya-besedka", short_description=NEW
    ).update(short_description=OLD)


class Migration(migrations.Migration):
    dependencies = [("services", "0008_service_includes")]
    operations = [migrations.RunPython(forward, backward)]
