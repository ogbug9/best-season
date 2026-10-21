from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('services', '0003_hourly_service_prices'),
        ('wagtailimages', '0027_image_description'),
    ]
    operations = [
        migrations.AddField(
            model_name='service', name='gallery_images',
            field=models.ManyToManyField(blank=True, related_name='+', to='wagtailimages.image', verbose_name='Дополнительные фото'),
        ),
    ]
