import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('web', '0004_clubproject_member_attendance_projectfee'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='clubproject',
            name='added_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='added_projects', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='clubproject',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='clubproject',
            name='description',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='clubproject',
            name='image',
            field=models.CharField(blank=True, help_text='Path to a static image or uploaded file relative to the project assets.', max_length=255),
        ),
        migrations.AddField(
            model_name='clubproject',
            name='updated_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='clubproject',
            name='updated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_projects', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='member',
            name='is_leader',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='member',
            name='is_removed',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='member',
            name='removal_reason',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='member',
            name='removed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='member',
            name='removed_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='removed_members', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='attendance',
            name='recorded_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='attendance_records', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='projectfee',
            name='recorded_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='project_fee_records', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='projectfee',
            name='updated_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.CreateModel(
            name='Announcement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('message', models.TextField()),
                ('is_public', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='announcements_created', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='AuditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(choices=[('added', 'Added'), ('updated', 'Updated'), ('deleted', 'Deleted'), ('removed', 'Removed'), ('attendance', 'Attendance'), ('fee', 'Fee'), ('announcement', 'Announcement'), ('resource', 'Resource')], max_length=30)),
                ('details', models.TextField()),
                ('model_name', models.CharField(blank=True, max_length=80)),
                ('object_name', models.CharField(blank=True, max_length=200)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('actor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='audit_logs', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='ResourceCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120, unique=True)),
                ('description', models.TextField(blank=True)),
                ('image', models.CharField(blank=True, max_length=255)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={'ordering': ['name']},
        ),
        migrations.CreateModel(
            name='ResourceItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('resource_type', models.CharField(choices=[('image', 'Image'), ('video', 'Video'), ('document', 'Document'), ('file', 'File')], default='file', max_length=20)),
                ('media_url', models.URLField(blank=True)),
                ('file_name', models.CharField(blank=True, max_length=200)),
                ('image', models.CharField(blank=True, help_text='Optional local static image path such as web/assets/one.jpeg.', max_length=255)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('is_active', models.BooleanField(default=True)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='resources', to='web.resourcecategory')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_resources', to=settings.AUTH_USER_MODEL)),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_resources', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['title']},
        ),
    ]
