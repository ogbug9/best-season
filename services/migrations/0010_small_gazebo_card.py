from django.db import migrations


def add_card(apps, schema_editor):
    # Фото #69 и тариф не переданы. Существующие редакторские данные сохраняем.
    apps.get_model("services", "Service").objects.get_or_create(
        slug="malaya-besedka",
        defaults={"name": "Маленькая беседка", "short_description": "Для небольшой компании.",
                  "is_hourly": True, "price": None, "sort_order": 25},
    )


class Migration(migrations.Migration):
    dependencies = [("services", "0009_besedka_short_text")]
    operations = [migrations.RunPython(add_card, migrations.RunPython.noop)]
