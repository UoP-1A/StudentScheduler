# Generated by Django 5.2 on 2025-04-02 13:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('calendarapp', '0002_event_duration'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='type',
            field=models.CharField(choices=[('event', 'Event'), ('study', 'Study')], default='event', max_length=10),
        ),
    ]
