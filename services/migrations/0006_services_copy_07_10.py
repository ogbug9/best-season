"""07.10: убрать служебное с «Доп. услуг».

- Подзаголовок обещал завтраки, которых нет (FAQ «Есть ли завтраки?»).
- У бани и беседки вместо описания стояло «Описание»: берём их тексты
  с карточек территории на сайте.
Меняется только сидовый текст; правка редактора сохраняется.
"""
from django.db import migrations

OLD_INTRO = 'Баня, беседка, завтраки и другие услуги.'
NEW_INTRO = 'Баня, беседка, сапы и всё, что сделает поездку вашей.'
TEXTS = {
    'russkaya-banya': 'Баня на дровах в лучших традициях парного искусства.',
    'bolshaya-besedka': 'Идеальное решение для проведения мероприятий и ужинов в большой компании.',
}


def update_copy(apps, schema_editor):
    alias = schema_editor.connection.alias
    ServicesPage = apps.get_model('services', 'ServicesPage')
    Revision = apps.get_model('wagtailcore', 'Revision')
    Service = apps.get_model('services', 'Service')
    for page in ServicesPage.objects.using(alias).filter(intro=OLD_INTRO):
        ServicesPage.objects.using(alias).filter(pk=page.pk).update(intro=NEW_INTRO)
        revision = Revision.objects.using(alias).filter(pk=page.latest_revision_id).first()
        if revision and isinstance(revision.content, dict) and revision.content.get('intro') == OLD_INTRO:
            Revision.objects.using(alias).filter(pk=revision.pk).update(content={**revision.content, 'intro': NEW_INTRO})
    for slug, text in TEXTS.items():
        Service.objects.using(alias).filter(slug=slug, short_description__in=('', 'Описание')).update(short_description=text)


class Migration(migrations.Migration):
    dependencies = [('services', '0005_card_template_texts'), ('wagtailcore', '0097_baselogentry_uuid_action_timestamp_indexes')]
    operations = [migrations.RunPython(update_copy, migrations.RunPython.noop)]
