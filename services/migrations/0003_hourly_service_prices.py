# -*- coding: utf-8 -*-
"""Цены почасовых объектов: баня 1 500 ₽/час, беседка 4 000 ₽/час.

Прежние 8 000 и 6 000 были сняты с флажков макета, где стоит подпись
«за ночь», — для почасового объекта она неверна. Правим только там, где
цена так и осталась засеянной: свою цену редактора не трогаем.
"""
from django.db import migrations

# slug: (старая засеянная цена, новая цена)
PRICES = {
    "russkaya-banya": (8000, 1500),
    "bolshaya-besedka": (6000, 4000),
}


def forwards(apps, schema_editor):
    Service = apps.get_model("services", "Service")
    for slug, (seeded, actual) in PRICES.items():
        service = Service.objects.filter(slug=slug, price=seeded).first()
        if service is None:
            continue
        service.price = actual
        service.price_unit = "hour"
        service.save(update_fields=["price", "price_unit"])


def backwards(apps, schema_editor):
    Service = apps.get_model("services", "Service")
    for slug, (seeded, actual) in PRICES.items():
        service = Service.objects.filter(slug=slug, price=actual).first()
        if service is None:
            continue
        service.price = seeded
        service.save(update_fields=["price"])


class Migration(migrations.Migration):

    dependencies = [
        ("services", "0002_servicespage"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
