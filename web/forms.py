from django import forms
from django.contrib.staticfiles.finders import find
from django.utils import timezone
from pathlib import PurePosixPath

from .models import Announcement, ClubIncome, ClubProject, Member, ProjectExpense, ProjectFee


class MemberForm(forms.ModelForm):
	class Meta:
		model = Member
		fields = (
			'name', 'class_name', 'email', 'membership_fee_due', 'membership_fee_paid',
		)
		widgets = {
			'name': forms.TextInput(attrs={'autocomplete': 'name'}),
			'class_name': forms.Select(),
			'email': forms.EmailInput(attrs={'autocomplete': 'email'}),
		}

	def clean(self):
		cleaned_data = super().clean()
		due = cleaned_data.get('membership_fee_due')
		paid = cleaned_data.get('membership_fee_paid')
		if due is not None and paid is not None and paid > due:
			self.add_error('membership_fee_paid', 'Paid amount cannot exceed the fee due.')
		return cleaned_data


class AttendanceForm(forms.Form):
	date = forms.DateField(
		initial=timezone.localdate,
		widget=forms.DateInput(attrs={'type': 'date'}),
	)
	present_members = forms.ModelMultipleChoiceField(
		queryset=Member.objects.none(),
		required=False,
		widget=forms.CheckboxSelectMultiple,
	)

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.fields['present_members'].queryset = Member.objects.filter(is_removed=False)


class ProjectForm(forms.ModelForm):
	description = forms.CharField(
		widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'Brief project description'}),
	)

	class Meta:
		model = ClubProject
		fields = ('name', 'description', 'image', 'image_file', 'active')
		widgets = {
			'name': forms.TextInput(attrs={'placeholder': 'Project name'}),
			'description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Brief project description'}),
			'image': forms.TextInput(attrs={'placeholder': 'Example: web/assets/three.jpg'}),
		}

	def clean(self):
		cleaned_data = super().clean()
		has_existing_image = bool(self.instance and (self.instance.image_file or self.instance.image))
		if not cleaned_data.get('image_file') and not cleaned_data.get('image') and not has_existing_image:
			self.add_error('image_file', 'Upload an image or provide an existing image path.')
		image_path = cleaned_data.get('image', '').strip().replace('\\', '/')
		if image_path:
			parsed_path = PurePosixPath(image_path)
			if (
				parsed_path.is_absolute()
				or parsed_path.parts[:2] != ('web', 'assets')
				or '..' in parsed_path.parts
				or parsed_path.suffix.lower() not in {'.jpg', '.jpeg', '.png', '.webp'}
				or not find(str(parsed_path))
			):
				self.add_error('image', 'Choose an existing image from the club static assets.')
		uploaded_image = cleaned_data.get('image_file')
		if uploaded_image and uploaded_image.size > 10 * 1024 * 1024:
			self.add_error('image_file', 'Uploaded images must be 10 MB or smaller.')
		return cleaned_data


class MembershipFeeForm(forms.Form):
	member = forms.ModelChoiceField(queryset=Member.objects.filter(is_removed=False, is_leader=False))
	amount_due = forms.DecimalField(min_value=0, max_digits=10, decimal_places=2)
	amount_paid = forms.DecimalField(min_value=0, max_digits=10, decimal_places=2)

	def clean(self):
		cleaned_data = super().clean()
		due = cleaned_data.get('amount_due')
		paid = cleaned_data.get('amount_paid')
		if due is not None and paid is not None and paid > due:
			self.add_error('amount_paid', 'Paid amount cannot exceed the fee due.')
		return cleaned_data


class ProjectExpenseForm(forms.ModelForm):
	class Meta:
		model = ProjectExpense
		fields = ('project', 'activity', 'description', 'amount')
		widgets = {
			'activity': forms.TextInput(attrs={'placeholder': 'Activity or project name'}),
			'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'What was this money spent on?'}),
		}

	def clean(self):
		cleaned_data = super().clean()
		if not cleaned_data.get('project') and not cleaned_data.get('activity'):
			self.add_error('activity', 'Enter an activity or select a project.')
		return cleaned_data


class ClubIncomeForm(forms.ModelForm):
	amount = forms.DecimalField(min_value=0, max_digits=10, decimal_places=2)

	class Meta:
		model = ClubIncome
		fields = ('project', 'activity', 'description', 'amount')
		widgets = {
			'activity': forms.TextInput(attrs={'placeholder': 'Fundraiser, event, or other activity'}),
			'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Describe where this income came from.'}),
		}

	def clean(self):
		cleaned_data = super().clean()
		if not cleaned_data.get('project') and not cleaned_data.get('activity'):
			self.add_error('activity', 'Enter an activity or select a project.')
		return cleaned_data


class ProjectFeeForm(forms.Form):
	project = forms.ModelChoiceField(queryset=ClubProject.objects.filter(active=True))
	member = forms.ModelChoiceField(queryset=Member.objects.filter(is_removed=False))
	amount_due = forms.DecimalField(min_value=0, max_digits=10, decimal_places=2)
	amount_paid = forms.DecimalField(min_value=0, max_digits=10, decimal_places=2)

	def clean(self):
		cleaned_data = super().clean()
		due = cleaned_data.get('amount_due')
		paid = cleaned_data.get('amount_paid')
		if due is not None and paid is not None and paid > due:
			self.add_error('amount_paid', 'Paid amount cannot exceed the fee due.')
		return cleaned_data

	def save(self, user=None):
		if not self.is_valid():
			raise ValueError('Cannot save an invalid project fee form.')
		fee, _ = ProjectFee.objects.update_or_create(
			project=self.cleaned_data['project'],
			member=self.cleaned_data['member'],
			defaults={
				'amount_due': self.cleaned_data['amount_due'],
				'amount_paid': self.cleaned_data['amount_paid'],
				'recorded_by': user,
				'updated_at': timezone.now(),
			},
		)
		return fee


class ContactForm(forms.Form):
	name = forms.CharField(max_length=120, widget=forms.TextInput(attrs={'placeholder': 'Your full name'}))
	email = forms.EmailField(widget=forms.EmailInput(attrs={'placeholder': 'you@example.com'}))
	message = forms.CharField(
		max_length=5000,
		widget=forms.Textarea(attrs={'rows': 5, 'placeholder': 'How can we help?'}),
	)


class ClubPeriodForm(forms.Form):
	period_type = forms.ChoiceField(choices=(('term', 'Start a new term'), ('year', 'Start a new academic year')))


class AnnouncementForm(forms.ModelForm):
	class Meta:
		model = Announcement
		fields = ('title', 'message', 'is_public')
		widgets = {
			'title': forms.TextInput(attrs={'placeholder': 'Announcement title'}),
			'message': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Write the announcement here...'}),
		}
