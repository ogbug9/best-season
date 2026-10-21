"""07.10: «Как добраться» — служебные «уточняется» и «Текст ожидается…» заменяются
фактами из ответа FAQ «Как добраться до глэмпинга?».

Меняется только поле, в котором ещё стоит пометка сида, — в странице и в её
последней ревизии. Правка редактора не перезаписывается.
"""
from django.db import migrations

MARKER = 'Текст ожидается от заказчика'
TRANSIT_ROUTE = (
    '<p>С Курского вокзала на электричке до станции Тарусская: от 400 ₽ '
    'и 1,2–2,5 часа в пути. Дальше такси или наш трансфер. '
    '<a href="https://www.tutu.ru/rasp.php?st1=20000&amp;st2=43806">Расписание электричек</a></p>'
)
CHANGES = {
    'car_distance': (lambda v: (v or '').strip() == 'уточняется', '100 км от Москвы'),
    'car_time': (lambda v: (v or '').strip() == 'уточняется', '≈ 1,5 часа'),
    'transfer_price': (lambda v: (v or '').strip() == 'уточняется', ''),
    'transit_route': (lambda v: MARKER in (v or ''), TRANSIT_ROUTE),
}


def updated(values):
    return {name: new for name, (is_seed, new) in CHANGES.items()
            if name in values and is_seed(values[name])}


def update_copy(apps, schema_editor):
    DirectionsPage = apps.get_model('core', 'DirectionsPage')
    Revision = apps.get_model('wagtailcore', 'Revision')
    alias = schema_editor.connection.alias
    for page in DirectionsPage.objects.using(alias).iterator():
        fields = updated({name: getattr(page, name) for name in CHANGES})
        if fields:
            DirectionsPage.objects.using(alias).filter(pk=page.pk).update(**fields)
        revision = Revision.objects.using(alias).filter(pk=page.latest_revision_id).first()
        if revision and isinstance(revision.content, dict):
            fields = updated(revision.content)
            if fields:
                Revision.objects.using(alias).filter(pk=revision.pk).update(content={**revision.content, **fields})


class Migration(migrations.Migration):
    dependencies = [('core', '0024_about_remove_nursery_name'), ('wagtailcore', '0097_baselogentry_uuid_action_timestamp_indexes')]
    operations = [migrations.RunPython(update_copy, migrations.RunPython.noop)]
