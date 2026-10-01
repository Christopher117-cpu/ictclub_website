from django.db import migrations


def seed_patron_membership(apps, schema_editor):
	Leader = apps.get_model('web', 'Leader')
	Member = apps.get_model('web', 'Member')
	AuditLog = apps.get_model('web', 'AuditLog')
	patron_profile, _ = Leader.objects.get_or_create(
		role='Patron',
		defaults={
			'name': 'Patron',
			'bio': 'Club patron profile.',
			'display_order': 7,
			'is_visible': True,
		},
	)
	member, created = Member.objects.get_or_create(
		name=patron_profile.name,
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
			details='The club patron was automatically added as a member with membership fees complete.',
			model_name='Member',
			object_name=patron_profile.name,
		)


class Migration(migrations.Migration):
	dependencies = [
		('web', '0008_repair_leader_profiles'),
	]

	operations = [
		migrations.RunPython(seed_patron_membership, migrations.RunPython.noop),
	]
