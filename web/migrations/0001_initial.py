from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Leader',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120)),
                ('role', models.CharField(max_length=120)),
                ('bio', models.TextField(blank=True)),
                ('photo', models.CharField(blank=True, help_text='Filename inside web/static/web/assets/, for example one.jpeg.', max_length=120)),
                ('display_order', models.PositiveIntegerField(default=0)),
                ('is_visible', models.BooleanField(default=True)),
            ],
            options={
                'ordering': ['display_order', 'name'],
            },
        ),
    ]
