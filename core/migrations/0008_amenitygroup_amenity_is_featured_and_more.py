"""Группа удобств из TextChoices превращается в справочник.

Прежние пять значений («В доме», «Кухня», «Ванная», «На улице»,
«Условия») переносятся записями, связи удобств сохраняются. Обратная
миграция кладёт коды назад в текстовое поле — группы, заведённые
редактором после перехода, кода не имеют и получают «inside».
"""

from django.db import migrations, models
import django.db.models.deletion

# Порядок — как в прежнем TextChoices, он же порядок вывода на странице
LEGACY_GROUPS = [
    ("inside", "В доме"),
    ("kitchen", "Кухня"),
    ("bathroom", "Ванная"),
    ("outside", "На улице"),
    ("rules", "Условия"),
]


def to_snippets(apps, schema_editor):
    AmenityGroup = apps.get_model("core", "AmenityGroup")
    Amenity = apps.get_model("core", "Amenity")

    used = set(Amenity.objects.values_list("legacy_group", flat=True))
    by_code = {}
    for order, (code, title) in enumerate(LEGACY_GROUPS, start=1):
        # Пустые группы не заводим: справочник и так придётся наполнять
        # под макет, лишние строки редактору только мешают.
        if code not in used:
            continue
        by_code[code] = AmenityGroup.objects.create(name=title, sort_order=order * 10)

    for amenity in Amenity.objects.all():
        group = by_code.get(amenity.legacy_group)
        if group is None:
            continue
        amenity.group = group
        amenity.save(update_fields=["group"])


def to_codes(apps, schema_editor):
    Amenity = apps.get_model("core", "Amenity")

    by_title = {title: code for code, title in LEGACY_GROUPS}
    for amenity in Amenity.objects.select_related("group"):
        title = amenity.group.name if amenity.group_id else ""
        amenity.legacy_group = by_title.get(title, "inside")
        amenity.save(update_fields=["legacy_group"])


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0007_territoryitem_spacer_before_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="AmenityGroup",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        max_length=80, unique=True, verbose_name="Название"
                    ),
                ),
                (
                    "sort_order",
                    models.PositiveSmallIntegerField(
                        default=100, verbose_name="Порядок"
                    ),
                ),
            ],
            options={
                "verbose_name": "Группа удобств",
                "verbose_name_plural": "Группы удобств",
                "ordering": ["sort_order", "name"],
            },
        ),
        migrations.AlterModelOptions(
            name="amenity",
            options={
                "ordering": ["group__sort_order", "group__name", "sort_order", "name"],
                "verbose_name": "Удобство",
                "verbose_name_plural": "Удобства",
            },
        ),
        migrations.RenameField(
            model_name="amenity", old_name="group", new_name="legacy_group"
        ),
        migrations.AddField(
            model_name="amenity",
            name="group",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="amenities",
                to="core.amenitygroup",
                verbose_name="Группа",
            ),
        ),
        migrations.AddField(
            model_name="amenity",
            name="is_featured",
            field=models.BooleanField(
                default=False,
                help_text="Снятая галочка — удобство видно только в развёрнутом описании.",
                verbose_name="Показывать плиткой в «Удобствах»",
            ),
        ),
        migrations.RunPython(to_snippets, to_codes),
        migrations.RemoveField(model_name="amenity", name="legacy_group"),
        migrations.AlterField(
            model_name="amenity",
            name="icon",
            field=models.CharField(
                blank=True,
                choices=[
                    ("wifi", "Wi-Fi"),
                    ("parking", "Парковка"),
                    ("kitchen", "Кухня"),
                    ("fridge", "Холодильник"),
                    ("stove", "Плита"),
                    ("microwave", "Микроволновка"),
                    ("kettle", "Чайник"),
                    ("dishes", "Посуда"),
                    ("shower", "Душ"),
                    ("towels", "Полотенца"),
                    ("hairdryer", "Фен"),
                    ("bed", "Спальное место"),
                    ("linen", "Постельное бельё"),
                    ("tv", "Телевизор"),
                    ("heating", "Отопление"),
                    ("conditioner", "Кондиционер"),
                    ("fireplace", "Камин"),
                    ("terrace", "Терраса"),
                    ("bbq", "Мангал"),
                    ("gazebo", "Беседка"),
                    ("sauna", "Баня"),
                    ("pool", "Купель"),
                    ("pets", "Можно с животными"),
                    ("kids", "Можно с детьми"),
                    ("capacity", "Вместимость"),
                    ("guest", "Гость"),
                    ("area", "Площадь"),
                    ("layout", "Планировка"),
                    ("sofa_bed", "Диван-кровать"),
                    ("bunk_bed", "Двухэтажная кровать"),
                    ("moon", "Ночи"),
                ],
                max_length=32,
                verbose_name="Иконка",
            ),
        ),
    ]
