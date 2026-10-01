import json
import re
from unittest.mock import patch

from django.core import mail
from django.http import HttpResponse
from django.test import TestCase
from django.test import RequestFactory, override_settings
from django.contrib.auth.models import Group, User
from django.urls import reverse
from django.utils import timezone

from .models import (
	Announcement, Attendance, AuditLog, ClubIncome, ClubPeriod, ClubProject, Leader,
	ContactMessage, Member, ProjectExpense, ProjectFee,
)


class HomePageTests(TestCase):
	def test_public_pages_load(self):
		for page in ('/', '/about/', '/projects/', '/team/', '/contact/'):
			with self.subTest(page=page):
				response = self.client.get(page)

				self.assertEqual(response.status_code, 200)
				self.assertContains(response, 'ICT Club')
		for removed_page in ('/activities/', '/resources/'):
			with self.subTest(removed_page=removed_page):
				self.assertEqual(self.client.get(removed_page).status_code, 404)

	def test_home_uses_shared_template(self):
		response = self.client.get('/')

		self.assertTemplateUsed(response, 'web/home.html')
		self.assertContains(response, 'Building Skills.')
		self.assertContains(response, 'Creating Technology.')
		self.assertContains(response, 'Levereging ICT to spur Innovations')
		self.assertContains(response, '/static/web/assets/logo.webp')
		self.assertContains(response, 'Project titles, images and descriptions will appear here')
		self.assertContains(response, 'Our motto')

	def test_events_page_is_removed_and_footer_credit_is_updated(self):
		self.assertEqual(self.client.get('/events/').status_code, 404)
		self.assertContains(self.client.get('/'), 'Built by Mpoza Christopher for the BSK ICT Club')

	def test_contact_page_displays_club_email_and_competition_photo(self):
		contact_response = self.client.get('/contact/')
		self.assertContains(contact_response, 'mailto:ictclubbsk@gmail.com')
		self.assertContains(contact_response, 'ictclubbsk@gmail.com')

	def test_public_metadata_robots_and_sitemap_use_canonical_public_pages(self):
		response = self.client.get('/')
		self.assertContains(response, '<link rel="canonical" href="http://testserver/">', html=False)
		self.assertContains(response, 'property="og:title"')
		self.assertContains(response, 'application/ld+json')
		schema_match = re.search(
			r'<script type="application/ld\+json">(.*?)</script>',
			response.content.decode(),
		)
		self.assertIsNotNone(schema_match)
		self.assertEqual(json.loads(schema_match.group(1))['@context'], 'https://schema.org')

		sitemap_response = self.client.get(reverse('sitemap'))
		self.assertEqual(sitemap_response.status_code, 200)
		self.assertContains(sitemap_response, 'http://testserver/about/')
		self.assertNotContains(sitemap_response, '/records/')
		robots_response = self.client.get(reverse('robots_txt'))
		self.assertContains(robots_response, 'Sitemap: http://testserver/sitemap.xml')
		self.assertContains(robots_response, 'Disallow: /records/')
		self.assertContains(robots_response, 'Disallow: /admin/')

	@override_settings(PUBLIC_BASE_URL='https://club.example.test')
	def test_configured_canonical_host_is_used_for_metadata_robots_and_sitemap(self):
		response = self.client.get('/about/')
		self.assertContains(response, '<link rel="canonical" href="https://club.example.test/about/">', html=False)
		self.assertContains(
			self.client.get(reverse('sitemap')),
			'https://club.example.test/about/',
		)
		self.assertContains(
			self.client.get(reverse('robots_txt')),
			'Sitemap: https://club.example.test/sitemap.xml',
		)

	@override_settings(DEBUG=False)
	def test_custom_public_error_page_is_rendered_without_debug_details(self):
		response = self.client.get('/this-page-does-not-exist/')
		self.assertEqual(response.status_code, 404)
		self.assertContains(response, 'That page could not be found.', status_code=404)
		self.assertNotIn('Page not found at', response.content.decode())

	def test_database_health_endpoint_returns_minimal_status(self):
		response = self.client.get(reverse('health_check'))
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.content, b'ok\n')

	@override_settings(
		PUBLIC_BASE_URL='https://canonical.example.test',
		ALLOWED_HOSTS=['canonical.example.test', 'alias.example.test'],
	)
	def test_canonical_host_middleware_redirects_gets_with_path_and_query(self):
		from .middleware import CanonicalHostMiddleware

		request = RequestFactory().get(
			'/projects/?source=alias',
			HTTP_HOST='alias.example.test',
		)
		response = CanonicalHostMiddleware(lambda _request: HttpResponse('ok'))(request)
		self.assertEqual(response.status_code, 301)
		self.assertEqual(
			response['Location'],
			'https://canonical.example.test/projects/?source=alias',
		)

	def test_about_page_includes_the_club_history_and_aims(self):
		response = self.client.get('/about/')
		self.assertContains(response, 'started in 2022 by Tumwine Kelly')
		self.assertContains(response, 'artificial intelligence, robotics, cloud computing, embedded systems')
		self.assertContains(response, 'Levereging ICT to spur Innovations')

	def test_projects_are_added_by_leaders_and_rendered_from_project_records(self):
		speaker_group, _ = Group.objects.get_or_create(name='Speaker')
		speaker = User.objects.create_user(username='speaker-projects', password='club-test-password')
		speaker.groups.add(speaker_group)
		self.client.force_login(speaker)
		response = self.client.post(reverse('add_project'), {
			'name': 'Student-built weather station',
			'description': 'An outdoor station for local weather measurements.',
			'image': 'web/assets/four.jpg',
		})
		self.assertEqual(response.status_code, 302)
		project = ClubProject.objects.get(name='Student-built weather station')
		self.assertEqual(project.added_by, speaker)
		self.assertContains(self.client.get('/'), 'Student-built weather station')
		projects_page = self.client.get('/projects/')
		self.assertContains(projects_page, 'An outdoor station for local weather measurements.')
		self.assertContains(projects_page, 'four-1280.webp')
		self.assertContains(projects_page, 'four-640.webp')

	def test_contact_form_sends_email_to_club_address(self):
		response = self.client.post('/contact/', {
			'name': 'Student Visitor',
			'email': 'student@example.com',
			'message': 'I would like to know more about club membership.',
		})
		self.assertEqual(response.status_code, 302)
		self.assertEqual(response.url, '/contact/')
		self.assertEqual(len(mail.outbox), 1)
		self.assertIn('ictclubbsk@gmail.com', mail.outbox[0].recipients())
		contact_message = ContactMessage.objects.get()
		self.assertEqual(contact_message.name, 'Student Visitor')
		self.assertEqual(contact_message.message, 'I would like to know more about club membership.')
		self.assertTrue(AuditLog.objects.filter(
			model_name='ContactMessage',
			details__contains='New website contact message from Student Visitor',
		).exists())

	@patch('web.views.EmailMessage.send', side_effect=OSError('test connection failure'))
	def test_contact_message_remains_in_leader_inbox_when_email_delivery_fails(self, send_email):
		with self.assertLogs('web.views', level='ERROR') as captured_logs:
			response = self.client.post('/contact/', {
				'name': 'Offline Visitor',
				'email': 'offline@example.com',
				'message': 'Please have a leader reply.',
			}, follow=True)
		self.assertEqual(response.status_code, 200)
		self.assertIn('Email notification failed for contact message id', captured_logs.output[0])
		send_email.assert_called_once_with(fail_silently=False)
		self.assertTrue(ContactMessage.objects.filter(name='Offline Visitor').exists())
		self.assertContains(
			response,
			'Your message was saved for the club leaders, but the email notification could not be sent.',
		)

	def test_contact_form_rejects_oversized_message(self):
		response = self.client.post('/contact/', {
			'name': 'Student Visitor',
			'email': 'student@example.com',
			'message': 'x' * 5001,
		})
		self.assertEqual(response.status_code, 200)
		self.assertFalse(ContactMessage.objects.exists())
		self.assertFalse(mail.outbox)

	def test_team_page_displays_leader_records(self):
		response = self.client.get('/team/')

		leaders = (
			('Mpoza Christopher', 'Club President'),
			('Nasuuna Alamrebecca', 'Speaker'),
			('Kasozi Allan', 'Treasurer'),
			('Najuuko Esther', 'Secretary'),
			('Kanyike Innocent', 'Projects Manager'),
			('Ewaku Chelsea Doreen', 'Mobiliser / Coordinator'),
			('Patron', 'Patron'),
		)
		self.assertEqual(Leader.objects.count(), 7)
		for name, role in leaders:
			with self.subTest(name=name):
				self.assertContains(response, name)
				self.assertContains(response, role)
			if name != 'Mpoza Christopher':
				self.assertEqual(Leader.objects.get(name=name).photo, '')

		self.assertContains(response, '/static/web/assets/one.webp')

	def test_public_team_member_list_is_paginated(self):
		Member.objects.bulk_create([
			Member(name=f'Public Member {number:03d}', class_name='Senior 3')
			for number in range(65)
		])
		first_page = self.client.get(reverse('team'))
		expected_count = Member.objects.filter(is_removed=False).count()
		self.assertEqual(first_page.context['member_page'].paginator.count, expected_count)
		self.assertEqual(len(first_page.context['member_page']), 60)
		second_page = self.client.get(reverse('team'), {'members_page': 2})
		self.assertEqual(len(second_page.context['member_page']), expected_count - 60)
		self.assertContains(second_page, 'Public Member 064')


class ClubRecordsTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(username='president', password='club-test-password')
		president_group, _ = Group.objects.get_or_create(name='President')
		self.user.groups.add(president_group)

	def test_records_dashboard_requires_login_and_leadership_role(self):
		response = self.client.get(reverse('records_dashboard'))
		self.assertEqual(response.status_code, 302)
		self.assertIn(reverse('records_login'), response.url)

		self.client.force_login(User.objects.create_user(username='member', password='club-test-password'))
		self.assertEqual(self.client.get(reverse('records_dashboard')).status_code, 403)

	def test_leaders_receive_and_individually_read_contact_messages(self):
		contact_message = ContactMessage.objects.create(
			name='Visitor Name',
			email='visitor@example.com',
			message='Please tell me about joining the club.',
		)
		self.client.force_login(self.user)

		dashboard = self.client.get(reverse('records_dashboard'))
		self.assertContains(dashboard, 'Contact inbox')
		self.assertContains(dashboard, '1 unread')
		self.assertContains(dashboard, 'Please tell me about joining the club.')
		self.assertContains(dashboard, 'visitor@example.com')

		read_response = self.client.post(
			reverse('mark_contact_message_read', args=[contact_message.pk]),
		)
		self.assertRedirects(read_response, reverse('records_dashboard'))
		dashboard = self.client.get(reverse('records_dashboard'))
		self.assertContains(dashboard, '0 unread')
		self.assertContains(dashboard, 'Read by you')

		treasurer_group, _ = Group.objects.get_or_create(name='Treasurer')
		treasurer = User.objects.create_user(username='treasurer-inbox', password='club-test-password')
		treasurer.groups.add(treasurer_group)
		self.client.force_login(treasurer)
		treasurer_dashboard = self.client.get(reverse('records_dashboard'))
		self.assertContains(treasurer_dashboard, '1 unread')
		self.assertContains(treasurer_dashboard, 'Please tell me about joining the club.')

	@override_settings(LEADER_INITIAL_PASSWORDS={
		'codestar': 'test-only-codestar-password',
		'patron': 'test-only-patron-password',
		'secretary': 'test-only-secretary-password',
		'speaker': 'test-only-speaker-password',
		'treasurer': 'test-only-treasurer-password',
		'projectsmanager': 'test-only-projectsmanager-password',
		'mobiliser': 'test-only-mobiliser-password',
	})
	def test_leader_accounts_use_configured_initial_passwords_without_resetting_existing(self):
		self.client.get(reverse('records_login'))
		accounts = {
			username: f'test-only-{username}-password'
			for username in (
				'codestar', 'patron', 'secretary', 'speaker',
				'treasurer', 'projectsmanager', 'mobiliser',
			)
		}
		for username, password in accounts.items():
			with self.subTest(username=username):
				self.assertTrue(User.objects.get(username=username).check_password(password))
		patron = User.objects.get(username='patron')
		patron.set_password('custom-test-password')
		patron.save(update_fields=['password'])
		self.client.get(reverse('records_login'))
		patron.refresh_from_db()
		self.assertTrue(patron.check_password('custom-test-password'))

	def test_membership_fee_status_uses_searchable_paginated_member_rows(self):
		Member.objects.bulk_create([
			Member(
				name=f'Fee Member {number:04d}',
				class_name='Senior 4',
				membership_fee_due=100,
				membership_fee_paid=100 if number < 25 else 50 if number < 75 else 0,
			)
			for number in range(101)
		])
		self.client.force_login(self.user)
		first_page = self.client.get(reverse('records_dashboard'))
		self.assertEqual(first_page.context['fee_page'].paginator.count, 108)
		self.assertEqual(len(first_page.context['fee_page']), 50)
		self.assertContains(first_page, 'Fee paid')
		self.assertContains(first_page, 'Fee due')
		self.assertContains(first_page, 'Balance')
		self.assertContains(first_page, 'Payment status')
		self.assertContains(first_page, 'Fee Member 0000')
		self.assertNotIn(
			'Fee Member 0050',
			[member.name for member in first_page.context['fee_page']],
		)
		second_page = self.client.get(reverse('records_dashboard'), {'fee_page': 2})
		self.assertEqual(len(second_page.context['fee_page']), 50)
		filtered_page = self.client.get(reverse('records_dashboard'), {
			'fee_status': 'partial',
			'fee_search': 'Fee Member 00',
		})
		self.assertEqual(filtered_page.context['fee_page'].paginator.count, 50)
		self.assertTrue(all(member.fee_status == 'Partial' for member in filtered_page.context['fee_page']))

	def test_leader_can_add_members_record_attendance_and_update_project_fees(self):
		self.client.force_login(self.user)
		self.client.post(reverse('add_member'), {
			'name': 'Amina Student',
			'class_name': 'Senior 4',
			'email': '',
			'membership_fee_due': '20.00',
			'membership_fee_paid': '5.00',
		})
		self.client.post(reverse('add_member'), {
			'name': 'Brian Student',
			'class_name': 'Senior 3',
			'email': '',
			'membership_fee_due': '20.00',
			'membership_fee_paid': '0.00',
		})
		amina = Member.objects.get(name='Amina Student')
		brian = Member.objects.get(name='Brian Student')

		self.client.post(reverse('record_attendance'), {
			'date': '2026-09-27',
			'present_members': [str(amina.pk)],
		})
		self.assertTrue(Attendance.objects.get(member=amina).is_present)
		self.assertFalse(Attendance.objects.get(member=brian).is_present)
		attendance_page = self.client.get(reverse('records_dashboard'), {'date': '2026-09-27'})
		self.assertRegex(
			attendance_page.content.decode(),
			rf'name="present_members" value="{amina.pk}"[^>]*checked',
		)

		self.client.post(reverse('add_project'), {
			'name': 'Robotics showcase',
			'description': 'Build a small educational robot.',
			'image': 'web/assets/three.jpg',
		})
		project = ClubProject.objects.get(name='Robotics showcase')
		fee_data = {
			'project': str(project.pk),
			'member': str(amina.pk),
			'amount_due': '50.00',
			'amount_paid': '15.00',
		}
		response = self.client.post(reverse('save_project_fee'), fee_data)
		self.assertEqual(response.status_code, 302)
		fee_data['amount_paid'] = '25.00'
		self.client.post(reverse('save_project_fee'), fee_data)
		fee = ProjectFee.objects.get(member=amina, project=project)
		self.assertEqual(ProjectFee.objects.count(), 1)
		self.assertEqual(str(fee.amount_paid), '25.00')

		self.client.post(reverse('remove_member', args=[amina.pk]), {'reason': 'Repeatedly absent.'})
		amina.refresh_from_db()
		self.assertTrue(amina.is_removed)
		self.assertTrue(ProjectFee.objects.filter(member=amina).exists())

	def test_four_missed_meetings_remove_a_member_and_preserve_history(self):
		member = Member.objects.create(name='Meeting Dodger', class_name='Senior 2')
		self.client.force_login(self.user)
		for date in ('2026-09-01', '2026-09-08', '2026-09-15', '2026-09-22'):
			self.client.post(reverse('record_attendance'), {'date': date})
		member.refresh_from_db()
		self.assertTrue(member.is_removed)
		self.assertIn('four', member.removal_reason)
		self.assertTrue(AuditLog.objects.filter(action='removed', object_name=member.name).exists())

	def test_only_president_or_patron_can_restore_and_removed_members_are_retained(self):
		member = Member.objects.create(name='Returned Student', class_name='Senior 2')
		member.is_removed = True
		member.removed_at = timezone.now()
		member.removal_reason = 'Repeated absences'
		member.removed_by = self.user
		member.save()
		self.client.force_login(self.user)
		response = self.client.post(reverse('restore_member', args=[member.pk]))
		self.assertEqual(response.status_code, 302)
		member.refresh_from_db()
		self.assertFalse(member.is_removed)
		self.assertEqual(member.restored_by, self.user)
		self.assertTrue(AuditLog.objects.filter(action='restored', object_name=member.name).exists())

	def test_starting_new_year_promotes_members_and_is_audited(self):
		member = Member.objects.create(name='Promoted Student', class_name='Senior 2')
		self.client.force_login(self.user)
		response = self.client.post(reverse('start_new_period'), {'period_type': 'year'})
		self.assertEqual(response.status_code, 302)
		member.refresh_from_db()
		self.assertEqual(member.class_name, 'Senior 3')
		period = ClubPeriod.objects.get(pk=1)
		self.assertEqual((period.academic_year, period.term), (2027, 1))
		self.assertTrue(AuditLog.objects.filter(action='period').exists())

	def test_treasurer_can_record_spending_and_fee_updates_are_audited(self):
		treasurer_group, _ = Group.objects.get_or_create(name='Treasurer')
		treasurer = User.objects.create_user(username='treasurer-test', password='club-test-password')
		treasurer.groups.add(treasurer_group)
		member = Member.objects.create(name='Finance Student', class_name='Senior 1')
		project = ClubProject.objects.create(name='Community lab')
		self.client.force_login(treasurer)
		response = self.client.post(reverse('save_membership_fee'), {
			'member': member.pk, 'amount_due': '25.00', 'amount_paid': '10.00',
		})
		self.assertEqual(response.status_code, 302)
		self.assertTrue(AuditLog.objects.filter(action='fee', object_name=member.name).exists())
		membership_income = ClubIncome.objects.get(activity='Membership fees', description__contains=member.name)
		self.assertEqual((membership_income.academic_year, membership_income.term), (2026, 1))
		self.client.post(reverse('add_project_expense'), {
			'project': project.pk, 'activity': '', 'description': 'Sensor components', 'amount': '12.50',
		})
		expense = ProjectExpense.objects.get(project=project)
		self.assertEqual(expense.recorded_by, treasurer)
		self.client.post(reverse('add_club_income'), {
			'project': project.pk, 'activity': '', 'description': 'Prototype sponsorship', 'amount': '40.00',
		})
		income = ClubIncome.objects.get(project=project)
		self.assertEqual(income.recorded_by, treasurer)
		self.assertEqual((income.academic_year, income.term), (2026, 1))
		self.assertTrue(AuditLog.objects.filter(action='income').exists())
		dashboard = self.client.get(reverse('records_dashboard'))
		self.assertContains(dashboard, 'Income &amp; expenditure by term')
		self.assertContains(dashboard, '12.50')
		self.assertContains(dashboard, '40.00')
		self.assertContains(dashboard, 'Income &amp; expenditure by term')

	def test_finance_chart_compares_recorded_income_and_expenses_by_academic_term(self):
		self.client.force_login(self.user)
		ClubIncome.objects.create(
			activity='Annual fundraiser',
			description='Term two fundraiser',
			amount='800.00',
			academic_year=2025,
			term=2,
		)
		ProjectExpense.objects.create(
			activity='Annual fundraiser',
			description='Term two venue',
			amount='225.00',
			academic_year=2025,
			term=2,
		)
		response = self.client.get(reverse('records_dashboard'))
		period_row = next(row for row in response.context['finance_rows'] if row['academic_year'] == 2025 and row['term'] == 2)
		self.assertEqual(period_row['income'], 800)
		self.assertEqual(period_row['spent'], 225)
		self.assertContains(response, '2025 · Term 2')

	def test_audit_history_expires_after_five_hours(self):
		self.client.force_login(self.user)
		expired = AuditLog.objects.create(
			actor=self.user, action='updated', details='Old change',
			model_name='Member', object_name='Old record',
			created_at=timezone.now() - timezone.timedelta(hours=6),
		)
		recent = AuditLog.objects.create(
			actor=self.user, action='updated', details='Recent change',
			model_name='Member', object_name='Recent record',
			created_at=timezone.now() - timezone.timedelta(hours=1),
		)
		response = self.client.get(reverse('records_dashboard'))
		self.assertFalse(AuditLog.objects.filter(pk=expired.pk).exists())
		self.assertTrue(AuditLog.objects.filter(pk=recent.pk).exists())
		self.assertNotContains(response, 'Old change')
		self.assertContains(response, 'Recent change')
		self.assertContains(response, 'data-audit-created=')

	def test_speaker_can_record_attendance_and_removed_sections_are_not_routed(self):
		speaker_group, _ = Group.objects.get_or_create(name='Speaker')
		speaker = User.objects.create_user(username='speaker-test', password='club-test-password')
		speaker.groups.add(speaker_group)
		self.client.force_login(speaker)
		response = self.client.post(reverse('record_attendance'), {'date': '2026-09-29'})
		self.assertEqual(response.status_code, 302)
		self.assertTrue(AuditLog.objects.filter(action='attendance').exists())
		self.assertEqual(self.client.get('/resources/').status_code, 404)
		self.assertEqual(self.client.get('/activities/').status_code, 404)

	def test_private_announcements_stay_out_of_public_pages(self):
		Announcement.objects.create(title='Leaders only', message='Internal details', is_public=False)
		Announcement.objects.create(title='Open meeting', message='Welcome everyone', is_public=True)
		public_page = self.client.get(reverse('home'))
		self.assertContains(public_page, 'Open meeting')
		self.assertNotContains(public_page, 'Leaders only')

	@override_settings(LEADER_INITIAL_PASSWORDS={
		'codestar': 'test-only-codestar-password',
		'patron': 'test-only-patron-password',
		'secretary': 'test-only-secretary-password',
		'speaker': 'test-only-speaker-password',
		'treasurer': 'test-only-treasurer-password',
		'projectsmanager': 'test-only-projectsmanager-password',
		'mobiliser': 'test-only-mobiliser-password',
	})
	def test_each_leader_receives_changes_since_their_previous_login(self):
		self.client.get(reverse('records_login'))
		login_data = {'username': 'speaker', 'password': 'test-only-speaker-password'}
		self.assertEqual(self.client.post(reverse('records_login'), login_data).status_code, 302)
		self.assertEqual(self.client.get(reverse('records_dashboard')).status_code, 200)
		self.client.post(reverse('records_logout'))
		AuditLog.objects.create(
			actor=self.user,
			action='removed',
			details='A member was removed after repeated absence.',
			model_name='Member',
			object_name='Notification Student',
		)
		self.assertEqual(self.client.post(reverse('records_login'), login_data).status_code, 302)
		next_login = self.client.get(reverse('records_dashboard'))
		self.assertContains(next_login, 'Notification Student')
		self.assertContains(next_login, 'repeated absence')


class AdminAppearanceTests(TestCase):
	def test_admin_uses_club_branding_and_custom_stylesheet(self):
		staff_user = User.objects.create_user(
			username='admin-style-test', password='club-test-password', is_staff=True,
		)
		self.client.force_login(staff_user)
		response = self.client.get(reverse('admin:index'))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'BSK ICT CLUB')
		self.assertContains(response, 'Club records management')
		self.assertContains(response, 'web/css/admin.css')
