from django.db import migrations


def set_whatsapp_contact(apps, schema_editor):
    apps.get_model("core", "SiteSettings").objects.using(schema_editor.connection.alias).update(
        whatsapp_url="https://wa.me/79652862406"
    )


class Migration(migrations.Migration):
    dependencies = [("core", "0022_faq_reference_05_10")]
    operations = [migrations.RunPython(set_whatsapp_contact, migrations.RunPython.noop)]
