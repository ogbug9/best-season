import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('promotions', '0003_alter_promotion_short_description'), ('wagtailimages', '0027_image_description')]
    operations = [
        migrations.AddField(
            model_name='promotion', name='mobile_image',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='wagtailimages.image', verbose_name='Фото для мобильного макета'),
        ),
    ]
