from functools import wraps
from datetime import timedelta
import logging
from pathlib import PurePosixPath
import smtplib

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.core.mail import EmailMessage
from django.core.paginator import Paginator
from django.db import connection
from django.db.models import Count, F, Q, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.templatetags.static import static
from django.contrib.staticfiles.finders import find
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_GET, require_POST

from .forms import (
    AnnouncementForm,
    AttendanceForm,
    ClubIncomeForm,
    ContactForm,
    ClubPeriodForm,
    MemberForm,
    MembershipFeeForm,
    ProjectExpenseForm,
    ProjectFeeForm,
    ProjectForm,
)

from .models import (
    Announcement,
    Attendance,
    AuditLog,
    ClubIncome,
    ClubPeriod,
    ClubProject,
    ContactMessage,
    LeaderNotificationState,
    Leader,
    Member,
    ProjectFee,
    ProjectExpense,
)


# ============================================================
# ICT CLUB LEADERSHIP GROUPS
# ============================================================

LEADERSHIP_GROUPS = (
    "President",
    "Patron",
    "Secretary",
    "Speaker",
    "Treasurer",
    "Projects Manager",
    "Mobiliser / Coordinator",
)


logger = logging.getLogger(__name__)


# ============================================================
# DEFAULT INITIAL PASSWORD
# ============================================================
#
# ALL ICT CLUB LEADERSHIP ACCOUNTS USE THIS PASSWORD.
#
# ============================================================

DEFAULT_LEADER_PASSWORD = "adminictclub@2026"


# ============================================================
# ENSURE ICT CLUB LEADER ACCOUNTS EXIST
# ============================================================

def ensure_club_users():
    """
    Create the ICT Club leadership accounts automatically.

    All leadership accounts use the same password:

        adminictclub@2026

    Existing accounts are also updated to use this password.
    """

    user_model = get_user_model()

    leader_accounts = [
        ("codestar", ["President"]),
        ("patron", ["Patron"]),
        ("secretary", ["Secretary"]),
        ("speaker", ["Speaker"]),
        ("treasurer", ["Treasurer"]),
        ("projectsmanager", ["Projects Manager"]),
        ("mobiliser", ["Mobiliser / Coordinator"]),
    ]

    usernames = [
        username
        for username, _ in leader_accounts
    ]

    existing_usernames = set(
        user_model.objects.filter(
            username__in=usernames
        ).values_list(
            "username",
            flat=True,
        )
    )

    for username, group_names in leader_accounts:

        # ----------------------------------------------------
        # Create groups
        # ----------------------------------------------------

        group_objs = []

        for group_name in group_names:

            group, _ = Group.objects.get_or_create(
                name=group_name
            )

            group_objs.append(group)

        # ----------------------------------------------------
        # Create or retrieve user
        # ----------------------------------------------------

        user, created = user_model.objects.get_or_create(
            username=username,
            defaults={
                "is_staff": username in {
                    "codestar",
                    "patron",
                },
            },
        )

        # ----------------------------------------------------
        # Set password
        # ----------------------------------------------------
        #
        # The password is deliberately applied to both new
        # and existing accounts so that all leadership users
        # can log in with the same credentials.
        #
        # Password:
        #
        # adminictclub@2026
        #
        # ----------------------------------------------------

        user.set_password(
            DEFAULT_LEADER_PASSWORD
        )

        # ----------------------------------------------------
        # President and Patron are staff users.
        # ----------------------------------------------------

        user.is_staff = username in {
            "codestar",
            "patron",
        }

        user.save(
            update_fields=[
                "password",
                "is_staff",
            ]
        )

        if created:

            logger.info(
                "Created ICT Club leader account: %s",
                username,
            )

        else:

            logger.info(
                "Updated ICT Club leader account password: %s",
                username,
            )

        # ----------------------------------------------------
        # Make sure the user has the correct leadership group.
        # ----------------------------------------------------

        user.groups.set(group_objs)


# ============================================================
# AUDIT LOG
# ============================================================

def create_audit_log(
    actor,
    action,
    details,
    model_name="",
    object_name="",
):
    AuditLog.objects.create(
        actor=actor,
        action=action,
        details=details,
        model_name=model_name,
        object_name=object_name,
    )


# ============================================================
# ENSURE LEADERS ARE CLUB MEMBERS
# ============================================================

def ensure_leader_membership():

    for leader in Leader.objects.filter(
        is_visible=True
    ):

        member, created = Member.objects.get_or_create(
            name=leader.name,
            defaults={
                "class_name": "Senior 1",
                "membership_fee_due": 0,
                "membership_fee_paid": 0,
                "is_leader": True,
            },
        )

        member.class_name = (
            member.class_name or "Senior 1"
        )

        member.membership_fee_due = 0
        member.membership_fee_paid = 0
        member.is_leader = True

        member.save(
            update_fields=[
                "class_name",
                "membership_fee_due",
                "membership_fee_paid",
                "is_leader",
            ]
        )

        if created:

            create_audit_log(
                None,
                "added",
                (
                    f"Leader profile {leader.name} "
                    "was automatically added as a club member."
                ),
                "Member",
                leader.name,
            )


# ============================================================
# LEADERSHIP ACCESS DECORATOR
# ============================================================

def leadership_required(view_func):

    @login_required(
        login_url="records_login"
    )
    @wraps(view_func)
    def wrapped(
        request,
        *args,
        **kwargs,
    ):

        if (
            not request.user.is_superuser
            and not request.user.groups.filter(
                name__in=LEADERSHIP_GROUPS
            ).exists()
        ):
            raise PermissionDenied

        return view_func(
            request,
            *args,
            **kwargs,
        )

    return wrapped


# ============================================================
# ROLE CHECK
# ============================================================

def _has_role(user, *roles):

    return (
        user.is_superuser
        or user.groups.filter(
            name__in=roles
        ).exists()
    )


# ============================================================
# CLUB LOGIN
# ============================================================

class ClubLoginView(LoginView):

    def form_valid(self, form):

        user = form.get_user()

        previous_login = user.last_login

        response = super().form_valid(form)

        requested_state = (
            LeaderNotificationState.objects
            .filter(user=user)
            .select_related("last_seen_log")
            .first()
        )

        self.request.session[
            "club_audit_cursor"
        ] = (
            requested_state.last_seen_log_id
            if requested_state
            else 0
        )

        self.request.session[
            "club_previous_login"
        ] = (
            previous_login.isoformat()
            if previous_login
            else ""
        )

        return response


# ============================================================
# RECORDS DASHBOARD CONTEXT
# ============================================================

def _records_context(
    request,
    selected_date=None,
    **form_overrides,
):

    ensure_leader_membership()

    selected_date = (
        selected_date
        or timezone.localdate()
    )

    current_period, _ = (
        ClubPeriod.objects.get_or_create(
            pk=1
        )
    )

    present_ids = list(
        Attendance.objects.filter(
            date=selected_date,
            is_present=True,
        ).values_list(
            "member_id",
            flat=True,
        )
    )

    forms = {
        "member_form": MemberForm(),

        "attendance_form": AttendanceForm(
            initial={
                "date": selected_date,
                "present_members": present_ids,
            }
        ),

        "project_form": ProjectForm(),

        "project_fee_form": ProjectFeeForm(),

        "membership_fee_form": MembershipFeeForm(),

        "expense_form": ProjectExpenseForm(),

        "income_form": ClubIncomeForm(),

        "announcement_form": AnnouncementForm(),

        "period_form": ClubPeriodForm(),
    }

    forms.update(form_overrides)

    members = (
        Member.objects
        .filter(is_removed=False)
        .annotate(
            present_count=Count(
                "attendance",
                filter=Q(
                    attendance__is_present=True
                ),
            )
        )
        .prefetch_related(
            "project_fees__project"
        )
    )

    fee_status = request.GET.get(
        "fee_status",
        "",
    )

    fee_search = request.GET.get(
        "fee_search",
        "",
    ).strip()

    fee_members = Member.objects.filter(
        is_removed=False
    )

    if fee_status == "complete":

        fee_members = fee_members.filter(
            Q(membership_fee_due__lte=0)
            |
            Q(
                membership_fee_paid__gte=F(
                    "membership_fee_due"
                )
            )
        )

    elif fee_status == "partial":

        fee_members = fee_members.filter(
            membership_fee_due__gt=0,
            membership_fee_paid__gt=0,
            membership_fee_paid__lt=F(
                "membership_fee_due"
            ),
        )

    elif fee_status == "outstanding":

        fee_members = fee_members.filter(
            membership_fee_due__gt=0,
            membership_fee_paid__lte=0,
        )

    if fee_search:

        fee_members = fee_members.filter(
            Q(
                name__icontains=fee_search
            )
            |
            Q(
                class_name__icontains=fee_search
            )
        )

    fee_page = Paginator(
        fee_members.order_by("name"),
        50,
    ).get_page(
        request.GET.get("fee_page")
    )

    period_income = {
        (
            entry["academic_year"],
            entry["term"],
        ): entry["total"] or 0

        for entry in (
            ClubIncome.objects
            .values(
                "academic_year",
                "term",
            )
            .annotate(
                total=Sum("amount")
            )
        )
    }

    period_expenses = {
        (
            entry["academic_year"],
            entry["term"],
        ): entry["total"] or 0

        for entry in (
            ProjectExpense.objects
            .values(
                "academic_year",
                "term",
            )
            .annotate(
                total=Sum("amount")
            )
        )
    }

    period_income.setdefault(
        (
            current_period.academic_year,
            current_period.term,
        ),
        0,
    )

    finance_rows = [
        {
            "academic_year": year,
            "term": term,
            "income": period_income.get(
                (year, term),
                0,
            ),
            "spent": period_expenses.get(
                (year, term),
                0,
            ),
        }

        for year, term in sorted(
            period_income.keys()
            |
            period_expenses.keys()
        )
    ]

    max_amount = max(
        (
            max(
                max(row["income"], 0),
                row["spent"],
            )

            for row in finance_rows
        ),
        default=0,
    )

    for row in finance_rows:

        row["income_width"] = (
            float(
                max(row["income"], 0)
                * 100
                / max_amount
            )
            if max_amount
            else 0
        )

        row["spent_width"] = (
            float(
                row["spent"]
                * 100
                / max_amount
            )
            if max_amount
            else 0
        )

    cursor_id = (
        request.session.pop(
            "club_audit_cursor",
            None,
        )
        if hasattr(request, "session")
        else None
    )

    notifications = AuditLog.objects.none()

    if cursor_id is not None:

        notifications = (
            AuditLog.objects
            .filter(
                pk__gt=cursor_id,
                created_at__gte=(
                    timezone.now()
                    - timedelta(hours=5)
                ),
            )
            .select_related("actor")
            .order_by("created_at")
        )

        latest_log_id = (
            AuditLog.objects
            .order_by("-pk")
            .values_list(
                "pk",
                flat=True,
            )
            .first()
        )

        state, _ = (
            LeaderNotificationState.objects
            .get_or_create(
                user=request.user
            )
        )

        if latest_log_id:

            state.last_seen_log_id = (
                latest_log_id
            )

            state.save(
                update_fields=[
                    "last_seen_log"
                ]
            )

    contact_message_paginator = Paginator(
        ContactMessage.objects.prefetch_related(
            "read_by"
        ),
        25,
    )

    contact_message_page = (
        contact_message_paginator.get_page(
            request.GET.get(
                "contact_page"
            )
        )
    )

    unread_contact_count = (
        ContactMessage.objects
        .exclude(
            read_by=request.user
        )
        .count()
    )

    return {
        **forms,

        "members": members,

        "member_count": members.count(),

        "fee_page": fee_page,

        "fee_page_range": (
            fee_page.paginator
            .get_elided_page_range(
                fee_page.number
            )
        ),

        "fee_status": fee_status,

        "fee_search": fee_search,

        "projects": (
            ClubProject.objects
            .filter(active=True)
            .select_related(
                "added_by",
                "updated_by",
            )
        ),

        "project_fees": (
            ProjectFee.objects
            .select_related(
                "member",
                "project",
            )
        ),

        "removed_members": (
            Member.objects
            .filter(
                removed_at__isnull=False
            )
            .select_related(
                "removed_by",
                "restored_by",
            )
            .order_by("-removed_at")
        ),

        "audit_logs": (
            AuditLog.objects
            .filter(
                created_at__gte=(
                    timezone.now()
                    - timedelta(hours=5)
                )
            )
            .select_related("actor")
            .order_by("-created_at")[:20]
        ),

        "announcements": (
            Announcement.objects
            .select_related("created_by")
            .order_by("-created_at")[:10]
        ),

        "contact_message_page": (
            contact_message_page
        ),

        "contact_message_page_range": (
            contact_message_paginator
            .get_elided_page_range(
                contact_message_page.number
            )
        ),

        "unread_contact_count": (
            unread_contact_count
        ),

        "expenses": (
            ProjectExpense.objects
            .select_related(
                "project",
                "recorded_by",
            )[:20]
        ),

        "incomes": (
            ClubIncome.objects
            .select_related(
                "project",
                "recorded_by",
            )[:20]
        ),

        "finance_rows": finance_rows,

        "current_period": current_period,

        "notifications": notifications,

        "can_manage_finance": _has_role(
            request.user,
            "President",
            "Patron",
            "Treasurer",
            "Projects Manager",
        ),

        "can_manage_projects": _has_role(
            request.user,
            *LEADERSHIP_GROUPS,
        ),

        "can_manage_announcements": _has_role(
            request.user,
            "President",
            "Patron",
            "Mobiliser / Coordinator",
            "Treasurer",
            "Projects Manager",
        ),

        "can_manage_period": _has_role(
            request.user,
            "President",
            "Patron",
            "Secretary",
            "Speaker",
        ),

        "can_remove_leaders": _has_role(
            request.user,
            "President",
            "Patron",
        ),

        "selected_date": selected_date,
    }


# ============================================================
# AUTOMATIC MEMBER REMOVAL
# ============================================================

def _remove_member_if_dodging(
    request,
    member,
    reason,
    actor=None,
):

    if member.is_removed:
        return False

    missed_count = (
        Attendance.objects
        .filter(
            member=member,
            is_present=False,
        )
        .count()
    )

    if (
        missed_count >= 4
        and not member.is_leader
    ):

        member.is_removed = True

        member.removed_at = timezone.now()

        member.removal_reason = reason

        member.removed_by = actor

        period = (
            ClubPeriod.objects
            .filter(pk=1)
            .first()
        )

        member.removed_academic_year = (
            period.academic_year
            if period
            else timezone.localdate().year
        )

        member.removed_term = (
            period.term
            if period
            else 1
        )

        member.save(
            update_fields=[
                "is_removed",
                "removed_at",
                "removal_reason",
                "removed_by",
                "removed_academic_year",
                "removed_term",
            ]
        )

        create_audit_log(
            actor,
            "removed",
            reason,
            "Member",
            member.name,
        )

        if request is not None:

            messages.warning(
                request,
                (
                    f"{member.name} was automatically "
                    "removed because they missed four meetings."
                ),
            )

        return True

    return False


# ============================================================
# PUBLIC PAGES
# ============================================================

def home(request):

    projects_list = (
        ClubProject.objects
        .filter(active=True)
        .only(
            "id",
            "name",
            "description",
            "image",
            "image_file",
        )
        .order_by("name")
    )

    projects_list = _prepare_project_images(
        projects_list
    )

    return render(
        request,
        "web/home.html",
        {
            "project_entries": projects_list
        },
    )


def about(request):

    return render(
        request,
        "web/about.html"
    )


def projects(request):

    projects_list = (
        ClubProject.objects
        .filter(active=True)
        .only(
            "id",
            "name",
            "description",
            "image",
            "image_file",
            "added_by",
            "updated_by",
            "created_at",
            "updated_at",
        )
        .select_related(
            "added_by",
            "updated_by",
        )
        .order_by("name")
    )

    projects_list = _prepare_project_images(
        projects_list
    )

    return render(
        request,
        "web/projects.html",
        {
            "project_entries": projects_list
        },
    )


def team(request):

    leaders = Leader.objects.filter(
        is_visible=True
    )

    for leader in leaders:

        if leader.photo:

            photo_path = (
                PurePosixPath("web/assets")
                / leader.photo
            )

            optimized_photo = str(
                photo_path.with_suffix(".webp")
            )

            leader.photo_source = static(
                optimized_photo
                if find(optimized_photo)
                else str(photo_path)
            )

    member_page = Paginator(
        Member.objects
        .filter(is_removed=False)
        .order_by("name"),
        60,
    ).get_page(
        request.GET.get("members_page")
    )

    return render(
        request,
        "web/team.html",
        {
            "leaders": leaders,
            "public_members": member_page,
            "member_page": member_page,
            "member_page_range": (
                member_page.paginator
                .get_elided_page_range(
                    member_page.number
                )
            ),
        },
    )


# ============================================================
# PROJECT IMAGES
# ============================================================

def _prepare_project_images(
    projects_list
):

    for project in projects_list:

        project.image_srcset = ""

        if project.image_file:

            project.image_source = (
                project.image_file.url
            )

        elif project.image:

            original_path = PurePosixPath(
                project.image
            )

            optimized_path = str(
                original_path.with_suffix(".webp")
            )

            responsive_variants = [
                (
                    width,
                    str(
                        original_path.with_name(
                            f"{original_path.stem}-{width}.webp"
                        )
                    ),
                )

                for width in (
                    640,
                    1280,
                )

                if find(
                    str(
                        original_path.with_name(
                            f"{original_path.stem}-{width}.webp"
                        )
                    )
                )
            ]

            if responsive_variants:

                project.image_source = static(
                    responsive_variants[-1][1]
                )

                project.image_srcset = ", ".join(
                    f"{static(variant_path)} {width}w"
                    for width, variant_path
                    in responsive_variants
                )

            elif find(optimized_path):

                project.image_source = static(
                    optimized_path
                )

            elif find(
                str(original_path)
            ):

                project.image_source = static(
                    str(original_path)
                )

            else:

                project.image_source = static(
                    "web/assets/logo.webp"
                )

        else:

            project.image_source = static(
                "web/assets/logo.webp"
            )

    return projects_list


# ============================================================
# CONTACT
# ============================================================

def contact(request):

    form = ContactForm(
        request.POST or None
    )

    if (
        request.method == "POST"
        and form.is_valid()
    ):

        cleaned = form.cleaned_data

        contact_message = (
            ContactMessage.objects.create(
                name=cleaned["name"],
                email=cleaned["email"],
                message=cleaned["message"],
            )
        )

        create_audit_log(
            None,
            "added",
            (
                f"New website contact message "
                f"from {contact_message.name}."
            ),
            "ContactMessage",
            str(contact_message.pk),
        )

        try:

            EmailMessage(
                subject=(
                    f'New message from {cleaned["name"]}'
                ),

                body=(
                    f'Name: {cleaned["name"]}\n'
                    f'Email: {cleaned["email"]}\n\n'
                    f'{cleaned["message"]}'
                ),

                to=[
                    "ictclubbsk@gmail.com"
                ],

                reply_to=[
                    cleaned["email"]
                ],
            ).send(
                fail_silently=False
            )

        except (
            OSError,
            smtplib.SMTPException,
        ):

            logger.exception(
                "Email notification failed for "
                "contact message id %s.",
                contact_message.pk,
            )

            messages.warning(
                request,
                (
                    "Your message was saved for the club "
                    "leaders, but the email notification "
                    "could not be sent."
                ),
            )

        else:

            messages.success(
                request,
                (
                    "Your message has been sent to "
                    "the ICT Club email address."
                ),
            )

        return redirect("contact")

    return render(
        request,
        "web/contact.html",
        {
            "form": form
        },
    )


# ============================================================
# RECORDS LOGIN
# ============================================================

def records_login(
    request,
    *args,
    **kwargs,
):

    # Automatically creates all required leadership accounts.
    ensure_club_users()

    return ClubLoginView.as_view(
        template_name="web/records_login.html",
        redirect_authenticated_user=True,
        next_page="records_dashboard",
    )(
        request,
        *args,
        **kwargs,
    )


# ============================================================
# LOGOUT
# ============================================================

records_logout = LogoutView.as_view(
    next_page="home"
)


# ============================================================
# RECORDS DASHBOARD
# ============================================================

@leadership_required
def records_dashboard(request):

    AuditLog.objects.filter(
        created_at__lt=(
            timezone.now()
            - timedelta(hours=5)
        )
    ).delete()

    selected_date = (
        parse_date(
            request.GET.get(
                "date",
                "",
            )
        )
        or timezone.localdate()
    )

    context = _records_context(
        request,
        selected_date,
    )

    return render(
        request,
        "web/records.html",
        context,
    )


# ============================================================
# ROBOTS.TXT
# ============================================================

@require_GET
def robots_txt(request):

    public_base_url = (
        settings.PUBLIC_BASE_URL
        or request.build_absolute_uri(
            "/"
        ).rstrip("/")
    )

    return HttpResponse(
        "User-agent: *\n"
        "Allow: /\n"
        "Disallow: /records/\n"
        "Allow: /records/login/\n"
        "Disallow: /records/logout/\n"
        "Disallow: /admin/\n"
        "Disallow: /health/\n"
        f"Sitemap: {public_base_url}/sitemap.xml\n",
        content_type=(
            "text/plain; charset=utf-8"
        ),
    )


# ============================================================
# HEALTH CHECK
# ============================================================

@require_GET
def health_check(request):

    with connection.cursor() as cursor:

        cursor.execute(
            "SELECT 1"
        )

        cursor.fetchone()

    return HttpResponse(
        "ok\n",
        content_type=(
            "text/plain; charset=utf-8"
        ),
    )


# ============================================================
# ERROR HANDLERS
# ============================================================

def bad_request(
    request,
    exception,
):

    return HttpResponse(
        render_to_string(
            "400.html"
        ),
        status=400,
    )


def permission_denied(
    request,
    exception,
):

    return HttpResponse(
        render_to_string(
            "403.html"
        ),
        status=403,
    )


def page_not_found(
    request,
    exception,
):

    return HttpResponse(
        render_to_string(
            "404.html"
        ),
        status=404,
    )


def server_error(request):

    return HttpResponse(
        render_to_string(
            "500.html"
        ),
        status=500,
    )


# ============================================================
# CONTACT MESSAGE
# ============================================================

@leadership_required
@require_POST
def mark_contact_message_read(
    request,
    message_id,
):

    contact_message = get_object_or_404(
        ContactMessage,
        pk=message_id,
    )

    contact_message.read_by.add(
        request.user
    )

    return redirect(
        "records_dashboard"
    )


# ============================================================
# MEMBERS
# ============================================================

@leadership_required
@require_POST
def add_member(request):

    form = MemberForm(
        request.POST
    )

    if form.is_valid():

        member = form.save()

        create_audit_log(
            request.user,
            "added",
            "Member was added to the club register.",
            "Member",
            member.name,
        )

        messages.success(
            request,
            "Member added.",
        )

    else:

        messages.error(
            request,
            form.errors.as_text(),
        )

    return redirect(
        "records_dashboard"
    )


@leadership_required
@require_POST
def remove_member(
    request,
    member_id,
):

    member = get_object_or_404(
        Member,
        pk=member_id,
    )

    if (
        member.is_leader
        and not _has_role(
            request.user,
            "President",
            "Patron",
        )
    ):

        raise PermissionDenied

    reason = request.POST.get(
        "reason",
        "",
    ).strip()

    if not reason:

        messages.error(
            request,
            "Enter a reason before removing a member.",
        )

        return redirect(
            "records_dashboard"
        )

    member.is_removed = True

    member.removed_at = timezone.now()

    member.removal_reason = reason

    member.removed_by = request.user

    period = (
        ClubPeriod.objects
        .filter(pk=1)
        .first()
    )

    member.removed_academic_year = (
        period.academic_year
        if period
        else timezone.localdate().year
    )

    member.removed_term = (
        period.term
        if period
        else 1
    )

    member.restored_at = None

    member.restored_by = None

    member.save(
        update_fields=[
            "is_removed",
            "removed_at",
            "removal_reason",
            "removed_by",
            "removed_academic_year",
            "removed_term",
            "restored_at",
            "restored_by",
        ]
    )

    create_audit_log(
        request.user,
        "removed",
        reason,
        "Member",
        member.name,
    )

    messages.success(
        request,
        (
            f"{member.name} removed from the club. "
            f"Reason: {reason}"
        ),
    )

    return redirect(
        "records_dashboard"
    )


@leadership_required
@require_POST
def restore_member(
    request,
    member_id,
):

    if not _has_role(
        request.user,
        "President",
        "Patron",
    ):

        raise PermissionDenied

    member = get_object_or_404(
        Member,
        pk=member_id,
        is_removed=True,
    )

    member.is_removed = False

    member.restored_at = timezone.now()

    member.restored_by = request.user

    member.save(
        update_fields=[
            "is_removed",
            "restored_at",
            "restored_by",
        ]
    )

    create_audit_log(
        request.user,
        "restored",
        "Member restored to the active club register.",
        "Member",
        member.name,
    )

    messages.success(
        request,
        f"{member.name} was restored to the club.",
    )

    return redirect(
        "records_dashboard"
    )


# ============================================================
# ATTENDANCE
# ============================================================

@leadership_required
@require_POST
def record_attendance(request):

    form = AttendanceForm(
        request.POST
    )

    if form.is_valid():

        present_ids = set(
            form.cleaned_data[
                "present_members"
            ].values_list(
                "pk",
                flat=True,
            )
        )

        attendance_date = (
            form.cleaned_data["date"]
        )

        active_members = list(
            Member.objects.filter(
                is_removed=False
            )
        )

        for member in active_members:

            is_present = (
                member.pk in present_ids
            )

            Attendance.objects.update_or_create(
                member=member,
                date=attendance_date,
                defaults={
                    "is_present": is_present,
                    "recorded_by": request.user,
                },
            )

            if not is_present:

                _remove_member_if_dodging(
                    request,
                    member,
                    (
                        "Automatic removal after "
                        "missing four club meetings."
                    ),
                    request.user,
                )

        create_audit_log(
            request.user,
            "attendance",
            (
                f"Attendance recorded for "
                f"{attendance_date:%d %b %Y}: "
                f"{len(present_ids)} present of "
                f"{len(active_members)} active members."
            ),
            "Attendance",
            attendance_date.isoformat(),
        )

        messages.success(
            request,
            (
                f"Attendance saved for "
                f"{attendance_date:%d %b %Y}."
            ),
        )

    else:

        messages.error(
            request,
            form.errors.as_text(),
        )

    return redirect(
        "records_dashboard"
    )


# ============================================================
# PROJECTS
# ============================================================

@leadership_required
@require_POST
def add_project(request):

    if not _has_role(
        request.user,
        *LEADERSHIP_GROUPS,
    ):

        raise PermissionDenied

    project_data = request.POST.copy()

    project_data.setdefault(
        "active",
        "on",
    )

    form = ProjectForm(
        project_data,
        request.FILES,
    )

    if form.is_valid():

        project = form.save(
            commit=False
        )

        project.added_by = request.user

        project.save()

        create_audit_log(
            request.user,
            "added",
            "Project was added to the club list.",
            "ClubProject",
            project.name,
        )

        messages.success(
            request,
            "Project added.",
        )

    else:

        messages.error(
            request,
            form.errors.as_text(),
        )

    return redirect(
        "records_dashboard"
    )


@leadership_required
@require_POST
def update_project(
    request,
    project_id,
):

    if not _has_role(
        request.user,
        *LEADERSHIP_GROUPS,
    ):

        raise PermissionDenied

    project = get_object_or_404(
        ClubProject,
        pk=project_id,
    )

    form = ProjectForm(
        request.POST,
        request.FILES,
        instance=project,
    )

    if form.is_valid():

        project = form.save(
            commit=False
        )

        project.updated_by = request.user

        project.updated_at = timezone.now()

        project.save()

        create_audit_log(
            request.user,
            "updated",
            "Project details or image updated.",
            "ClubProject",
            project.name,
        )

        messages.success(
            request,
            "Project updated.",
        )

    else:

        messages.error(
            request,
            form.errors.as_text(),
        )

    return redirect(
        "records_dashboard"
    )


# ============================================================
# PROJECT FEES
# ============================================================

@leadership_required
@require_POST
def save_project_fee(request):

    if not _has_role(
        request.user,
        "President",
        "Patron",
        "Treasurer",
        "Projects Manager",
    ):

        raise PermissionDenied

    form = ProjectFeeForm(
        request.POST
    )

    if form.is_valid():

        project = form.cleaned_data[
            "project"
        ]

        member = form.cleaned_data[
            "member"
        ]

        existing_fee = (
            ProjectFee.objects
            .filter(
                project=project,
                member=member,
            )
            .first()
        )

        previous_paid = (
            existing_fee.amount_paid
            if existing_fee
            else 0
        )

        fee = form.save(
            user=request.user
        )

        payment_delta = (
            fee.amount_paid
            - previous_paid
        )

        if payment_delta:

            period, _ = (
                ClubPeriod.objects
                .get_or_create(pk=1)
            )

            ClubIncome.objects.create(
                project=fee.project,
                activity="Project fee",
                description=(
                    "Project fee payment adjustment "
                    f"for {fee.member.name}."
                ),
                amount=payment_delta,
                academic_year=(
                    period.academic_year
                ),
                term=period.term,
                recorded_by=request.user,
            )

        create_audit_log(
            request.user,
            "fee",
            (
                f"{fee.project.name} fee for "
                f"{fee.member.name}: "
                f"{fee.amount_paid} paid of "
                f"{fee.amount_due} due."
            ),
            "ProjectFee",
            fee.member.name,
        )

        messages.success(
            request,
            "Project fee balance saved.",
        )

    else:

        messages.error(
            request,
            form.errors.as_text(),
        )

    return redirect(
        "records_dashboard"
    )


# ============================================================
# MEMBERSHIP FEES
# ============================================================

@leadership_required
@require_POST
def save_membership_fee(request):

    if not _has_role(
        request.user,
        "President",
        "Patron",
        "Treasurer",
        "Projects Manager",
    ):

        raise PermissionDenied

    form = MembershipFeeForm(
        request.POST
    )

    if form.is_valid():

        member = form.cleaned_data[
            "member"
        ]

        previous_paid = (
            member.membership_fee_paid
        )

        member.membership_fee_due = (
            form.cleaned_data[
                "amount_due"
            ]
        )

        member.membership_fee_paid = (
            form.cleaned_data[
                "amount_paid"
            ]
        )

        member.save(
            update_fields=[
                "membership_fee_due",
                "membership_fee_paid",
            ]
        )

        payment_delta = (
            member.membership_fee_paid
            - previous_paid
        )

        if payment_delta:

            period, _ = (
                ClubPeriod.objects
                .get_or_create(pk=1)
            )

            ClubIncome.objects.create(
                activity="Membership fees",
                description=(
                    "Membership fee payment "
                    f"adjustment for {member.name}."
                ),
                amount=payment_delta,
                academic_year=(
                    period.academic_year
                ),
                term=period.term,
                recorded_by=request.user,
            )

        create_audit_log(
            request.user,
            "fee",
            (
                "Membership fee payment updated: "
                f"{member.membership_fee_paid} paid of "
                f"{member.membership_fee_due} due."
            ),
            "Member",
            member.name,
        )

        messages.success(
            request,
            (
                f"Membership fee record saved "
                f"for {member.name}."
            ),
        )

    else:

        messages.error(
            request,
            form.errors.as_text(),
        )

    return redirect(
        "records_dashboard"
    )


# ============================================================
# PROJECT EXPENSES
# ============================================================

@leadership_required
@require_POST
def add_project_expense(request):

    if not _has_role(
        request.user,
        "President",
        "Patron",
        "Treasurer",
        "Projects Manager",
    ):

        raise PermissionDenied

    form = ProjectExpenseForm(
        request.POST
    )

    if form.is_valid():

        expense = form.save(
            commit=False
        )

        expense.recorded_by = request.user

        period, _ = (
            ClubPeriod.objects
            .get_or_create(pk=1)
        )

        expense.academic_year = (
            period.academic_year
        )

        expense.term = period.term

        expense.save()

        create_audit_log(
            request.user,
            "expense",
            (
                "Project expenditure recorded: "
                f"{expense.amount} for "
                f"{expense.project or expense.activity}. "
                f"{expense.description}"
            ),
            "ProjectExpense",
            str(
                expense.project
                or expense.activity
            ),
        )

        messages.success(
            request,
            "Project expenditure recorded.",
        )

    else:

        messages.error(
            request,
            form.errors.as_text(),
        )

    return redirect(
        "records_dashboard"
    )


# ============================================================
# CLUB INCOME
# ============================================================

@leadership_required
@require_POST
def add_club_income(request):

    if not _has_role(
        request.user,
        "President",
        "Patron",
        "Treasurer",
        "Projects Manager",
    ):

        raise PermissionDenied

    form = ClubIncomeForm(
        request.POST
    )

    if form.is_valid():

        income = form.save(
            commit=False
        )

        income.recorded_by = request.user

        period, _ = (
            ClubPeriod.objects
            .get_or_create(pk=1)
        )

        income.academic_year = (
            period.academic_year
        )

        income.term = period.term

        income.save()

        create_audit_log(
            request.user,
            "income",
            (
                "Club income recorded: "
                f"{income.amount} from "
                f"{income.project or income.activity}. "
                f"{income.description}"
            ),
            "ClubIncome",
            str(
                income.project
                or income.activity
            ),
        )

        messages.success(
            request,
            "Club income recorded.",
        )

    else:

        messages.error(
            request,
            form.errors.as_text(),
        )

    return redirect(
        "records_dashboard"
    )


# ============================================================
# ANNOUNCEMENTS
# ============================================================

@leadership_required
@require_POST
def add_announcement(request):

    if not _has_role(
        request.user,
        "Mobiliser / Coordinator",
        "President",
        "Patron",
        "Treasurer",
        "Projects Manager",
    ):

        raise PermissionDenied

    form = AnnouncementForm(
        request.POST
    )

    if form.is_valid():

        announcement = form.save(
            commit=False
        )

        announcement.created_by = (
            request.user
        )

        announcement.save()

        create_audit_log(
            request.user,
            "announcement",
            (
                f"Announcement added: "
                f"{announcement.title}."
            ),
            "Announcement",
            announcement.title,
        )

        messages.success(
            request,
            "Announcement published.",
        )

    else:

        messages.error(
            request,
            form.errors.as_text(),
        )

    return redirect(
        "records_dashboard"
    )


@leadership_required
@require_POST
def delete_announcement(
    request,
    announcement_id,
):

    if not _has_role(
        request.user,
        "Mobiliser / Coordinator",
        "President",
        "Patron",
        "Treasurer",
        "Projects Manager",
    ):

        raise PermissionDenied

    announcement = get_object_or_404(
        Announcement,
        pk=announcement_id,
    )

    name = announcement.title

    announcement.delete()

    create_audit_log(
        request.user,
        "deleted",
        (
            f"Announcement deleted: {name}"
        ),
        "Announcement",
        name,
    )

    messages.success(
        request,
        f"Announcement deleted: {name}",
    )

    return redirect(
        "records_dashboard"
    )


# ============================================================
# CLUB PERIOD
# ============================================================

@leadership_required
@require_POST
def start_new_period(request):

    if not _has_role(
        request.user,
        "President",
        "Patron",
        "Secretary",
        "Speaker",
    ):

        raise PermissionDenied

    form = ClubPeriodForm(
        request.POST
    )

    if not form.is_valid():

        messages.error(
            request,
            form.errors.as_text(),
        )

        return redirect(
            "records_dashboard"
        )

    period, _ = (
        ClubPeriod.objects
        .get_or_create(pk=1)
    )

    period_type = form.cleaned_data[
        "period_type"
    ]

    if period_type == "term":

        if period.term >= 3:

            messages.error(
                request,
                (
                    "Term 3 is in progress. "
                    "Start a new academic year instead."
                ),
            )

            return redirect(
                "records_dashboard"
            )

        period.term += 1

        details = (
            f"Club term {period.term} of "
            f"academic year {period.academic_year} "
            "started."
        )

    else:

        period.academic_year += 1

        period.term = 1

        promotions = {
            "Senior 1": "Senior 2",
            "Senior 2": "Senior 3",
            "Senior 3": "Senior 4",
            "Senior 4": "Senior 5",
            "Senior 5": "Senior 6",
        }

        promoted = 0

        for member in Member.objects.filter(
            is_removed=False,
            is_leader=False,
        ):

            new_class = promotions.get(
                member.class_name
            )

            if new_class:

                member.class_name = (
                    new_class
                )

                member.save(
                    update_fields=[
                        "class_name"
                    ]
                )

                promoted += 1

        details = (
            f"Academic year "
            f"{period.academic_year} started; "
            f"{promoted} active members advanced "
            "one class."
        )

    period.updated_at = timezone.now()

    period.updated_by = request.user

    period.save()

    create_audit_log(
        request.user,
        "period",
        details,
        "ClubPeriod",
        str(period),
    )

    messages.success(
        request,
        details,
    )

    return redirect(
        "records_dashboard"
    )
