from django.conf import settings
from django.core.files.base import ContentFile
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from pathlib import PurePosixPath
from io import BytesIO

from PIL import Image, ImageOps


class Leader(models.Model):
	name = models.CharField(max_length=120)
	role = models.CharField(max_length=120)
	bio = models.TextField(blank=True)
	photo = models.CharField(
		max_length=120,
		blank=True,
		help_text='Filename inside web/static/web/assets/, for example one.jpeg.',
	)
	display_order = models.PositiveIntegerField(default=0)
	is_visible = models.BooleanField(default=True)

	class Meta:
		ordering = ['display_order', 'name']

	def __str__(self):
		return f'{self.name} - {self.role}'


class Member(models.Model):
	CLASS_CHOICES = tuple((f'Senior {number}', f'Senior {number}') for number in range(1, 7))

	name = models.CharField(max_length=120)
	class_name = models.CharField(max_length=80, choices=CLASS_CHOICES, default='Senior 1')
	email = models.EmailField(blank=True)
	joined_on = models.DateField(default=timezone.localdate)
	membership_fee_due = models.DecimalField(
		max_digits=10, decimal_places=2, default=0,
		validators=[MinValueValidator(0)],
	)
	membership_fee_paid = models.DecimalField(
		max_digits=10, decimal_places=2, default=0,
		validators=[MinValueValidator(0)],
	)
	is_removed = models.BooleanField(default=False)
	removed_at = models.DateTimeField(null=True, blank=True)
	removal_reason = models.TextField(blank=True)
	removed_by = models.ForeignKey(
		settings.AUTH_USER_MODEL, null=True, blank=True,
		on_delete=models.SET_NULL, related_name='removed_members',
	)
	removed_academic_year = models.PositiveIntegerField(null=True, blank=True)
	removed_term = models.PositiveSmallIntegerField(null=True, blank=True)
	restored_at = models.DateTimeField(null=True, blank=True)
	restored_by = models.ForeignKey(
		settings.AUTH_USER_MODEL, null=True, blank=True,
		on_delete=models.SET_NULL, related_name='restored_members',
	)
	is_leader = models.BooleanField(default=False)

	class Meta:
		ordering = ['name']

	@property
	def fee_status(self):
		if self.membership_fee_due <= 0 or self.membership_fee_paid >= self.membership_fee_due:
			return 'Complete'
		if self.membership_fee_paid > 0:
			return 'Partial'
		return 'Outstanding'

	@property
	def membership_fee_balance(self):
		return max(self.membership_fee_due - self.membership_fee_paid, 0)

	def __str__(self):
		return self.name


class Attendance(models.Model):
	member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='attendance')
	date = models.DateField(default=timezone.localdate)
	is_present = models.BooleanField(default=True)
	recorded_by = models.ForeignKey(
		settings.AUTH_USER_MODEL, null=True, blank=True,
		on_delete=models.SET_NULL, related_name='attendance_records',
	)

	class Meta:
		ordering = ['-date', 'member__name']
		constraints = [
			models.UniqueConstraint(fields=['member', 'date'], name='unique_member_attendance_date'),
		]

	def __str__(self):
		return f'{self.member} - {self.date}'


class ClubProject(models.Model):
	name = models.CharField(max_length=120, unique=True)
	description = models.TextField(blank=True)
	image = models.CharField(max_length=255, blank=True, help_text='Path to a static image or uploaded file relative to the project assets.')
	image_file = models.ImageField(upload_to='projects/', blank=True)
	image_640 = models.ImageField(upload_to='projects/responsive/', blank=True, editable=False)
	image_1280 = models.ImageField(upload_to='projects/responsive/', blank=True, editable=False)
	active = models.BooleanField(default=True)
	created_at = models.DateTimeField(default=timezone.now)
	updated_at = models.DateTimeField(default=timezone.now)
	added_by = models.ForeignKey(
		settings.AUTH_USER_MODEL, null=True, blank=True,
		on_delete=models.SET_NULL, related_name='added_projects',
	)
	updated_by = models.ForeignKey(
		settings.AUTH_USER_MODEL, null=True, blank=True,
		on_delete=models.SET_NULL, related_name='updated_projects',
	)

	class Meta:
		ordering = ['name']

	def __str__(self):
		return self.name

	def save(self, *args, **kwargs):
		previous_image = None
		if self.pk:
			previous_image = type(self).objects.filter(pk=self.pk).values(
				'image_file', 'image_640', 'image_1280',
			).first()
		current_image_name = self.image_file.name or ''
		image_changed = previous_image is None or previous_image['image_file'] != current_image_name
		old_variants = (
			(previous_image['image_640'], previous_image['image_1280'])
			if previous_image else ('', '')
		)
		if image_changed:
			self.image_640 = ''
			self.image_1280 = ''

		super().save(*args, **kwargs)
		if not image_changed:
			return

		try:
			if self.image_file:
				with self.image_file.open('rb') as uploaded_image:
					with Image.open(uploaded_image) as opened_image:
						image = ImageOps.exif_transpose(opened_image)
						image = image.convert('RGBA' if 'A' in image.getbands() else 'RGB')
						for width, field_name in ((640, 'image_640'), (1280, 'image_1280')):
							if image.width <= width:
								continue
							height = round(image.height * width / image.width)
							variant = image.resize((width, height), Image.Resampling.LANCZOS)
							buffer = BytesIO()
							variant.save(buffer, format='WEBP', quality=80, method=4)
							field = getattr(self, field_name)
							filename = f'{PurePosixPath(self.image_file.name).stem}-{width}.webp'
							field.save(filename, ContentFile(buffer.getvalue()), save=False)
				super().save(update_fields=['image_640', 'image_1280'])
		finally:
			for field_name, old_name in zip(('image_640', 'image_1280'), old_variants):
				field = getattr(self, field_name)
				if old_name and old_name != field.name:
					field.storage.delete(old_name)


class ProjectFee(models.Model):
	member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='project_fees')
	project = models.ForeignKey(ClubProject, on_delete=models.CASCADE, related_name='fees')
	amount_due = models.DecimalField(
		max_digits=10, decimal_places=2, default=0,
		validators=[MinValueValidator(0)],
	)
	amount_paid = models.DecimalField(
		max_digits=10, decimal_places=2, default=0,
		validators=[MinValueValidator(0)],
	)
	recorded_by = models.ForeignKey(
		settings.AUTH_USER_MODEL, null=True, blank=True,
		on_delete=models.SET_NULL, related_name='project_fee_records',
	)
	updated_at = models.DateTimeField(default=timezone.now)

	class Meta:
		ordering = ['project__name', 'member__name']
		constraints = [
			models.UniqueConstraint(fields=['member', 'project'], name='unique_member_project_fee'),
		]

	def __str__(self):
		return f'{self.member} - {self.project}'


class Announcement(models.Model):
	title = models.CharField(max_length=200)
	message = models.TextField()
	is_public = models.BooleanField(default=True)
	created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='announcements_created')
	created_at = models.DateTimeField(default=timezone.now)
	updated_at = models.DateTimeField(default=timezone.now)

	class Meta:
		ordering = ['-created_at']

	def __str__(self):
		return self.title


class ContactMessage(models.Model):
	name = models.CharField(max_length=120)
	email = models.EmailField()
	message = models.TextField()
	created_at = models.DateTimeField(default=timezone.now, db_index=True)
	read_by = models.ManyToManyField(
		settings.AUTH_USER_MODEL, blank=True, related_name='read_contact_messages',
	)

	class Meta:
		ordering = ['-created_at']

	def __str__(self):
		return f'Message from {self.name} ({self.created_at:%Y-%m-%d %H:%M})'


class AuditLog(models.Model):
	ACTION_CHOICES = (
		('added', 'Added'),
		('updated', 'Updated'),
		('deleted', 'Deleted'),
		('removed', 'Removed'),
		('attendance', 'Attendance'),
		('fee', 'Fee'),
		('announcement', 'Announcement'),
		('restored', 'Restored'),
		('period', 'Period'),
		('expense', 'Expense'),
		('income', 'Income'),
	)

	actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='audit_logs')
	action = models.CharField(max_length=30, choices=ACTION_CHOICES)
	details = models.TextField()
	model_name = models.CharField(max_length=80, blank=True)
	object_name = models.CharField(max_length=200, blank=True)
	created_at = models.DateTimeField(default=timezone.now)

	class Meta:
		ordering = ['-created_at']

	def __str__(self):
		return f'{self.actor or "System"} - {self.action}'


class ClubPeriod(models.Model):
	academic_year = models.PositiveIntegerField(default=2026)
	term = models.PositiveSmallIntegerField(default=1)
	updated_at = models.DateTimeField(default=timezone.now)
	updated_by = models.ForeignKey(
		settings.AUTH_USER_MODEL, null=True, blank=True,
		on_delete=models.SET_NULL, related_name='club_period_updates',
	)

	class Meta:
		verbose_name = 'club academic period'

	def __str__(self):
		return f'{self.academic_year} / Term {self.term}'


class ProjectExpense(models.Model):
	project = models.ForeignKey(
		ClubProject, null=True, blank=True, on_delete=models.SET_NULL,
		related_name='expenses',
	)
	activity = models.CharField(max_length=160, blank=True)
	description = models.TextField()
	amount = models.DecimalField(
		max_digits=10, decimal_places=2, validators=[MinValueValidator(0)],
	)
	academic_year = models.PositiveIntegerField(default=2026)
	term = models.PositiveSmallIntegerField(default=1)
	recorded_by = models.ForeignKey(
		settings.AUTH_USER_MODEL, null=True, blank=True,
		on_delete=models.SET_NULL, related_name='project_expenses',
	)
	created_at = models.DateTimeField(default=timezone.now)

	class Meta:
		ordering = ['-created_at']

	def __str__(self):
		return f'{self.project or self.activity}: {self.amount}'


class ClubIncome(models.Model):
	project = models.ForeignKey(
		ClubProject, null=True, blank=True, on_delete=models.SET_NULL,
		related_name='income_records',
	)
	activity = models.CharField(max_length=160, blank=True)
	description = models.TextField()
	amount = models.DecimalField(
		max_digits=10, decimal_places=2,
	)
	academic_year = models.PositiveIntegerField(default=2026)
	term = models.PositiveSmallIntegerField(default=1)
	recorded_by = models.ForeignKey(
		settings.AUTH_USER_MODEL, null=True, blank=True,
		on_delete=models.SET_NULL, related_name='club_income_records',
	)
	created_at = models.DateTimeField(default=timezone.now)

	class Meta:
		ordering = ['-created_at']

	def __str__(self):
		return f'{self.project or self.activity}: {self.amount}'


class LeaderNotificationState(models.Model):
	user = models.OneToOneField(
		settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
		related_name='club_notification_state',
	)
	last_seen_log = models.ForeignKey(
		AuditLog, null=True, blank=True, on_delete=models.SET_NULL,
		related_name='seen_by_leader_states',
	)
