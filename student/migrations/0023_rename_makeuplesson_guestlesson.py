# Generated by Django 4.2.13 on 2024-11-06 03:29

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('teacher', '0011_delete_makeuplesson'),
        ('student', '0022_makeuplesson'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='MakeUpLesson',
            new_name='GuestLesson',
        ),
    ]
