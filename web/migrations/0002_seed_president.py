from django.db import migrations


def create_president(apps, schema_editor):
    Leader = apps.get_model('web', 'Leader')
    Leader.objects.create(
        name='Mpoza Christopher',
        role='Club President',
        bio='President of the BSK ICT Club.',
        photo='one.jpeg',
        display_order=1,
    )


def remove_president(apps, schema_editor):
    Leader = apps.get_model('web', 'Leader')
    Leader.objects.filter(name='Mpoza Christopher', role='Club President').delete()


class Migration(migrations.Migration):
    dependencies = [
        ('web', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_president, remove_president),
    ]
