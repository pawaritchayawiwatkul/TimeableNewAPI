# Generated by Django 4.2.13 on 2024-11-25 10:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('teacher', '0013_unavailabletimeonetime_start_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='unavailabletimeonetime',
            name='start',
            field=models.TimeField(),
        ),
        migrations.AlterField(
            model_name='unavailabletimeonetime',
            name='stop',
            field=models.TimeField(),
        ),
        migrations.AlterField(
            model_name='unavailabletimeregular',
            name='start',
            field=models.TimeField(),
        ),
        migrations.AlterField(
            model_name='unavailabletimeregular',
            name='stop',
            field=models.TimeField(),
        ),
    ]
