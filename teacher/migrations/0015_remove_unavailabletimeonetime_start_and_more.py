# Generated by Django 4.2.13 on 2024-11-25 10:58

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('teacher', '0014_alter_unavailabletimeonetime_start_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='unavailabletimeonetime',
            name='start',
        ),
        migrations.RemoveField(
            model_name='unavailabletimeonetime',
            name='stop',
        ),
    ]
