# Generated by Django 4.2.13 on 2024-11-18 08:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0027_alter_studentteacherrelation_student_color'),
    ]

    operations = [
        migrations.AddField(
            model_name='lesson',
            name='notified',
            field=models.BooleanField(default=False),
        ),
    ]