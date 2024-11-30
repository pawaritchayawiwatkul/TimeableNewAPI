# Generated by Django 4.2.13 on 2024-11-25 10:59

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('teacher', '0017_remove_unavailabletimeonetime_start_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='unavailabletimeonetime',
            name='start',
            field=models.DateTimeField(default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='unavailabletimeonetime',
            name='stop',
            field=models.DateTimeField(default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]
