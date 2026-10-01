from django.db import migrations


LEADERS = (
	('Nasuuna Alamrebecca', 'Speaker', 2),
	('Kasozi Allan', 'Treasurer', 3),
	('Najuuko Esther', 'Secretary', 4),
	('Kanyike Innocent', 'Projects Manager', 5),
	('Ewaku Chelsea Doreen', 'Mobiliser / Coordinator', 6),
)


def create_leaders(apps, schema_editor):
	Leader = apps.get_model('web', 'Leader')
	for name, role, display_order in LEADERS:
		Leader.objects.get_or_create(
			name=name,
			role=role,
			defaults={
				'bio': '',
				'photo': '',
				'display_order': display_order,
			},
		)


def remove_leaders(apps, schema_editor):
	Leader = apps.get_model('web', 'Leader')
	for name, role, _ in LEADERS:
		Leader.objects.filter(name=name, role=role).delete()


class Migration(migrations.Migration):
	dependencies = [
		('web', '0002_seed_president'),
	]

	operations = [
		migrations.RunPython(create_leaders, remove_leaders),
	]