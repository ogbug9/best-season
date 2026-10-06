"""06.10: seasonal tariffs replace each other every year on the same place.

«С мая по сентябрь» is shown 30.04–29.09, «С октября по апрель» 30.09–29.04
(decision of Nastya/Sofia). Only records whose season is still empty and whose
title is the seeded one are touched; editors can change the dates in the admin.
"""
from django.db import migrations

SEASONS = {
    'may-sentyabr': ('Тариф "С мая по сентябрь"', '30.04', '29.09'),
    'oktyabr-aprel': ('Тариф "С октября по апрель"', '30.09', '29.04'),
}


def apply_seasons(apps, schema_editor):
    Promotion = apps.get_model('promotions', 'Promotion')
    records = Promotion.objects.using(schema_editor.connection.alias)
    slot = records.filter(slug='oktyabr-aprel').values_list('sort_order', flat=True).first()
    for slug, (title, start, end) in SEASONS.items():
        promo = records.filter(slug=slug, title=title, season_start='', season_end='').first()
        if promo is None:
            print('Seasons 06.10: skipped (edited or missing):', slug)
            continue
        updates = {'season_start': start, 'season_end': end, 'is_visible': True}
        if slot is not None:
            updates['sort_order'] = slot
        records.filter(pk=promo.pk).update(**updates)


class Migration(migrations.Migration):
    dependencies = [('promotions', '0007_promotion_season')]
    operations = [migrations.RunPython(apply_seasons, migrations.RunPython.noop)]
