"""06.10: card texts from «Шаблоны карточек» for the four catalogue tiles.

Only empty descriptions or the seed placeholder «Описание» are filled; editor copy is kept.
"""
from django.db import migrations

TEXTS = {'arenda-sapov': 'Берег отсюда выглядит совсем иначе. Если не шуметь, то можно увидеть гнездо аистов, диких уток или бобровую хатку.', 'master-klassy': 'В летний сезон и по праздникам у нас проходят различные мастер-классы по живописи, флористике, йога-практики и другие активности.', 'fotosessii': 'Уникальность нашей локации оценила и съёмочная команда Алины Загитовой, организуем фотосессию и вам.', 'arenda-velosipedov': 'Взять велосипед и посмотреть, что вокруг: лесные дороги, окрестности, соседние деревни. Часа хватит на короткую вылазку.'}


def fill(apps, schema_editor):
    Service = apps.get_model('services', 'Service')
    records = Service.objects.using(schema_editor.connection.alias)
    for slug, text in TEXTS.items():
        updated = records.filter(slug=slug, short_description__in=('', 'Описание')).update(short_description=text)
        if not updated:
            print('Service texts 06.10: kept existing copy for', slug)


class Migration(migrations.Migration):
    dependencies = [('services', '0004_service_gallery_images')]
    operations = [migrations.RunPython(fill, migrations.RunPython.noop)]
