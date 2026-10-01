"""
URL configuration for ICT_CLUB project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from django.urls import path

from web import views
from web.sitemaps import PublicPagesSitemap

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('projects/', views.projects, name='projects'),
    path('team/', views.team, name='team'),
    path('contact/', views.contact, name='contact'),
    path('robots.txt', views.robots_txt, name='robots_txt'),
    path('sitemap.xml', sitemap, {'sitemaps': {'public': PublicPagesSitemap()}}, name='sitemap'),
    path('health/', views.health_check, name='health_check'),
    path('records/login/', views.records_login, name='records_login'),
    path('records/logout/', views.records_logout, name='records_logout'),
    path('records/', views.records_dashboard, name='records_dashboard'),
    path('records/contact-messages/<int:message_id>/read/', views.mark_contact_message_read, name='mark_contact_message_read'),
    path('records/members/add/', views.add_member, name='add_member'),
    path('records/members/<int:member_id>/remove/', views.remove_member, name='remove_member'),
    path('records/members/<int:member_id>/restore/', views.restore_member, name='restore_member'),
    path('records/attendance/', views.record_attendance, name='record_attendance'),
    path('records/projects/add/', views.add_project, name='add_project'),
    path('records/projects/<int:project_id>/update/', views.update_project, name='update_project'),
    path('records/project-fees/', views.save_project_fee, name='save_project_fee'),
    path('records/membership-fees/', views.save_membership_fee, name='save_membership_fee'),
    path('records/project-expenses/', views.add_project_expense, name='add_project_expense'),
    path('records/income/', views.add_club_income, name='add_club_income'),
    path('records/announcements/add/', views.add_announcement, name='add_announcement'),
    path('records/announcements/<int:announcement_id>/delete/', views.delete_announcement, name='delete_announcement'),
    path('records/period/start/', views.start_new_period, name='start_new_period'),
    path('admin/', admin.site.urls),
]

handler400 = 'web.views.bad_request'
handler403 = 'web.views.permission_denied'
handler404 = 'web.views.page_not_found'
handler500 = 'web.views.server_error'

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
