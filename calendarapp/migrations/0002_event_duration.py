# Generated by Django 5.1.6 on 2025-03-05 14:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('calendarapp', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='duration',
            field=models.DurationField(blank=True, null=True),
        ),
    ]
