from django.db import migrations


def rename_small_gazebo(apps, schema_editor):
    service = apps.get_model("services", "Service")
    service.objects.using(schema_editor.connection.alias).filter(
        slug="malaya-besedka",
        name__iexact="Маленькая беседка",
    ).update(name="Малая беседка")


class Migration(migrations.Migration):
    dependencies = [("services", "0010_small_gazebo_card")]
    operations = [migrations.RunPython(rename_small_gazebo, migrations.RunPython.noop)]
