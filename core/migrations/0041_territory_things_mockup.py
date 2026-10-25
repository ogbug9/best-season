"""25.10: «Территория» и «Чем заняться» по макетам Насти.

У страниц появился макет — снимаем пометку «Раздел дополняется» (0038 её ставила).
Четыре вопроса блока «Ответы на вопросы» со страницы «Территория» заводятся
в общий справочник FAQ, не на главную; уже существующий вопрос не трогается.
"""
from django.db import migrations

FAQ = [
    ("Работает ли интернет, есть ли связь?", "houses",
     "<p>Да, у нас хорошо ловят связь такие провайдеры, как Билайн и Т2.<br/>"
     "А безлимитный беспроводной интернет есть в каждом домике.</p>"),
    ("Есть ли еда на территории?", "houses",
     "<p>К сожалению, пока что на территории глэмпинга нет кафе или ресторана.<br/>"
     "Но каждое утро наша ферма радует нас свежими и натуральными продуктами, а в каждом домике оснащённая "
     "кухня и своя мангальная зона. Ближайший магазин находится в д. Страхово (3 мин. на машине), а ближайшее "
     "кафе в 7 минутах от нас.<br/>В каждом домике лежат брошюры с меню и информацией о наших партнёрах, "
     "у которых можно заказать блюда с доставкой прямо на глэмпинг.</p>"),
    ("Можно ли выходить к животным?", "pets",
     "<p>Да, в любое время. Ферма рабочая, животные живут своим распорядком, но подойти, познакомиться "
     "и фотографироваться можно. Две небольшие просьбы — не заходить внутрь загонов и не кормить "
     "без согласования с нами.</p>"),
    ("Где на территории ресепшен?", "checkin",
     "<p>У нас нет ресепшена или стойки администратора, всех гостей мы встречаем лично, знакомим "
     "с территорией и провожаем до домика. Просто за 30 минут до прибытия позвоните нам, и мы вас будем ждать.</p>"),
]


def forward(apps, schema_editor):
    alias = schema_editor.connection.alias
    FaqItem = apps.get_model("core", "FaqItem")
    for order, (question, topic, answer) in enumerate(FAQ):
        if not FaqItem.objects.using(alias).filter(question=question).exists():
            FaqItem.objects.using(alias).create(question=question, topic=topic, answer=answer,
                                                show_on_home=False, is_published=True, sort_order=300 + order)

    Revision = apps.get_model("wagtailcore", "Revision")
    querysets = [apps.get_model("core", "TerritoryPage").objects.using(alias).all(),
                 apps.get_model("core", "ContentPage").objects.using(alias).filter(slug="chem-zanyatsya")]
    for queryset in querysets:
        for page in queryset:
            type(page).objects.using(alias).filter(pk=page.pk).update(in_progress=False)
            revision = Revision.objects.using(alias).filter(pk=page.latest_revision_id).first()
            if revision and isinstance(revision.content, dict):
                Revision.objects.using(alias).filter(pk=revision.pk).update(content={**revision.content, "in_progress": False})


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0040_contact_settings_proxy"),
        ("wagtailcore", "0097_baselogentry_uuid_action_timestamp_indexes"),
    ]
    operations = [migrations.RunPython(forward, migrations.RunPython.noop)]
