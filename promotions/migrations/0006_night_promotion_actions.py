from django.db import migrations


SEED = [
    ('den-rozhdeniya', 'Тариф "День рождения"', 'Дарим скидку в день рождения - 15%', 10),
    ('pyatnica-50', 'Тариф "Пятница со скидкой 50%"', 'При бронировании 3-х дней: пятницы, субботы и воскресения, на пятницу действует скидка 50%', 20),
    ('may-sentyabr', 'Тариф "С мая по сентябрь"', 'От 3-х суток скидка 10%\nОт 5 суток - 15%\nОт 7 суток - 20%', 30),
    ('vygodnaya-banya', 'Тариф "Выгодная баня"', 'При бронировании русской бани от 3-х часов - баня рассчитывается по тарифу 1 500Р/час', 40),
    ('gostepriimstvo', 'Тариф "Гостеприимство"', 'При бронировании напрямую комплимент от хозяев: набор фермерских продуктов или дополнительный час в бане', 50),
    ('pravilnaya-udalenka', 'Тариф "Правильная удаленка"', '4 дня по цене 3 в будние дни', 60),
    ('oktyabr-aprel', 'Тариф "С октября по апрель"', 'От 3-х суток скидка 10%\nОт 5 суток - 20%\nОт 7 суток - 25%', 70),
]


def apply_actions(apps, schema_editor):
    Promotion = apps.get_model('promotions', 'Promotion')
    records = Promotion.objects.using(schema_editor.connection.alias)
    for slug, title, text, order in SEED:
        promo = records.filter(slug=slug).first()
        if promo is None or not (
            promo.title == title and promo.short_description == text
            and not promo.description and promo.sort_order == order
            and promo.date_from is None and promo.date_to is None
            and promo.is_published and promo.is_visible
            and promo.cta_type == 'booking' and not promo.cta_label
        ):
            continue
        updates = {}
        if slug in {'den-rozhdeniya', 'vygodnaya-banya', 'gostepriimstvo', 'pravilnaya-udalenka'}:
            updates['cta_type'] = 'request'
        elif slug == 'may-sentyabr':
            updates['is_visible'] = False
        elif slug == 'oktyabr-aprel':
            updates['sort_order'] = 30
        if updates:
            records.filter(pk=promo.pk).update(**updates)
    records.get_or_create(slug='podarochnyy-sertifikat', defaults={
        'title': 'Подарочный сертификат',
        'short_description': 'демо: Текст и условия подарочного сертификата ожидаются от владельца.',
        'sort_order': 80, 'cta_type': 'request', 'cta_label': 'Заказать сертификат',
        'is_visible': True, 'is_published': True,
    })


class Migration(migrations.Migration):
    dependencies = [('promotions', '0005_promotion_cta_label_promotion_cta_type_and_more')]
    operations = [migrations.RunPython(apply_actions, migrations.RunPython.noop)]
