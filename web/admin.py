from django.contrib import admin

from .models import (
	Announcement, Attendance, AuditLog, ClubIncome, ClubPeriod, ClubProject, Leader,
	ContactMessage, LeaderNotificationState, Member, ProjectExpense, ProjectFee,
)

admin.site.site_header = 'BSK ICT Club administration'
admin.site.site_title = 'BSK ICT Club'
admin.site.index_title = 'Club records workspace'


@admin.register(Leader)
class LeaderAdmin(admin.ModelAdmin):
	list_display = ('name', 'role', 'is_visible', 'display_order')
	list_filter = ('is_visible', 'role')
	list_editable = ('is_visible', 'display_order')
	search_fields = ('name', 'role', 'bio')
	ordering = ('display_order', 'name')


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
	list_display = ('name', 'class_name', 'membership_fee_paid', 'membership_fee_due', 'joined_on', 'is_removed')
	list_filter = ('is_removed', 'is_leader')
	search_fields = ('name', 'class_name', 'email')


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
	list_display = ('member', 'date', 'is_present', 'recorded_by')
	list_filter = ('date', 'is_present')
	search_fields = ('member__name',)


@admin.register(ClubProject)
class ClubProjectAdmin(admin.ModelAdmin):
	list_display = ('name', 'active', 'added_by', 'updated_by')
	list_filter = ('active',)
	search_fields = ('name',)


@admin.register(ProjectFee)
class ProjectFeeAdmin(admin.ModelAdmin):
	list_display = ('member', 'project', 'amount_paid', 'amount_due', 'recorded_by')
	list_filter = ('project',)
	search_fields = ('member__name', 'project__name')


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
	list_display = ('title', 'is_public', 'created_by', 'created_at')
	list_filter = ('is_public',)
	search_fields = ('title', 'message')


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
	list_display = ('name', 'email', 'created_at')
	search_fields = ('name', 'email', 'message')
	list_filter = ('created_at',)
	readonly_fields = ('name', 'email', 'message', 'created_at', 'read_by')

	def has_add_permission(self, request):
		return False

	def has_change_permission(self, request, obj=None):
		return False

	def has_delete_permission(self, request, obj=None):
		return False


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
	list_display = ('actor', 'action', 'object_name', 'created_at')
	list_filter = ('action',)
	search_fields = ('details', 'object_name')
	readonly_fields = ('actor', 'action', 'details', 'model_name', 'object_name', 'created_at')


@admin.register(ProjectExpense)
class ProjectExpenseAdmin(admin.ModelAdmin):
	list_display = ('project', 'activity', 'amount', 'recorded_by', 'created_at')
	list_filter = ('project', 'created_at')
	search_fields = ('activity', 'description', 'project__name')
	readonly_fields = ('recorded_by', 'created_at')


@admin.register(ClubIncome)
class ClubIncomeAdmin(admin.ModelAdmin):
	list_display = ('project', 'activity', 'amount', 'recorded_by', 'created_at')
	list_filter = ('project', 'created_at')
	search_fields = ('activity', 'description', 'project__name')
	readonly_fields = ('recorded_by', 'created_at')


@admin.register(ClubPeriod)
class ClubPeriodAdmin(admin.ModelAdmin):
	list_display = ('academic_year', 'term', 'updated_by', 'updated_at')
	readonly_fields = ('academic_year', 'term', 'updated_by', 'updated_at')


@admin.register(LeaderNotificationState)
class LeaderNotificationStateAdmin(admin.ModelAdmin):
	list_display = ('user', 'last_seen_log')
	readonly_fields = ('user', 'last_seen_log')
