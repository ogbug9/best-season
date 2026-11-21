import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("core", "0046_event_archive_and_banner"), ("houses", "0008_alter_housepage_pet_fee")]

    operations = [
        migrations.AddField(
            model_name="galleryphoto",
            name="house",
            field=models.ForeignKey(
                "houses.housepage", verbose_name="Дом", null=True, blank=True,
                on_delete=django.db.models.deletion.SET_NULL, related_name="+",
            ),
        ),
        migrations.AlterField(
            model_name="galleryphoto",
            name="category",
            field=models.CharField(
                "Что на фото", max_length=12, blank=True,
                choices=[
                    ("houses", "Домики"), ("territory", "Территория"), ("animals", "Животные"),
                    ("around", "Окрестности"), ("terrace", "Терраса"), ("banya", "Баня"),
                    ("gazebo", "Беседка"), ("farm", "Ферма"), ("river", "Река"), ("clearing", "Поляна"),
                ],
            ),
        ),
    ]
