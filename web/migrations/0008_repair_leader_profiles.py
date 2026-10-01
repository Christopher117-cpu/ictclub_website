from django.db import migrations


LEADERS = (
	('Mpoza Christopher', 'Club President', 'President of the BSK ICT Club.', 'one.jpeg', 1),
	('Nasuuna Alamrebecca', 'Speaker', '', '', 2),
	('Kasozi Allan', 'Treasurer', '', '', 3),
	('Najuuko Esther', 'Secretary', '', '', 4),
	('Kanyike Innocent', 'Projects Manager', '', '', 5),
	('Ewaku Chelsea Doreen', 'Mobiliser / Coordinator', '', '', 6),
)


def create_missing_leaders(apps, schema_editor):
	Leader = apps.get_model('web', 'Leader')
	Member = apps.get_model('web', 'Member')
	AuditLog = apps.get_model('web', 'AuditLog')
	for name, role, bio, photo, display_order in LEADERS:
		Leader.objects.get_or_create(
			name=name,
			role=role,
			defaults={
				'bio': bio,
				'photo': photo,
				'display_order': display_order,
				'is_visible': True,
			},
		)
		member, created = Member.objects.get_or_create(
			name=name,
			defaults={
				'class_name': 'Senior 1',
				'membership_fee_due': 0,
				'membership_fee_paid': 0,
				'is_leader': True,
			},
		)
		member.class_name = member.class_name or 'Senior 1'
		member.membership_fee_due = 0
		member.membership_fee_paid = 0
		member.is_leader = True
		member.save(update_fields=[
			'class_name', 'membership_fee_due', 'membership_fee_paid', 'is_leader',
		])
		if created:
			AuditLog.objects.create(
				action='added',
				details=f'Leader profile {name} was automatically added as a club member.',
				model_name='Member',
				object_name=name,
			)


class Migration(migrations.Migration):
	dependencies = [
		('web', '0007_alter_auditlog_action_clubincome'),
	]

	operations = [
		migrations.RunPython(create_missing_leaders, migrations.RunPython.noop),
	]
