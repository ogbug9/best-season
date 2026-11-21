from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("reviews", "0005_dev_strip")]

    operations = [
        migrations.AddField(
            model_name="reviewspage",
            name="sutochno_url",
            field=models.URLField("Страница отзывов на Суточно", blank=True),
        ),
        migrations.AddField(
            model_name="reviewspage",
            name="two_gis_review_url",
            field=models.URLField("Ссылка для отзыва в 2ГИС", blank=True),
        ),
    ]
