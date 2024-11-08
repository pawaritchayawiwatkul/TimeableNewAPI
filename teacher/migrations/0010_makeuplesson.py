# Generated by Django 4.2.13 on 2024-11-05 08:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('teacher', '0009_alter_unavailabletimeonetime_code_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='MakeUpLesson',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('notes', models.CharField(blank=True, max_length=300)),
                ('name', models.CharField(blank=True, max_length=300)),
                ('booked_datetime', models.DateTimeField()),
                ('duration', models.IntegerField()),
                ('code', models.CharField(max_length=12, unique=True)),
                ('status', models.CharField(choices=[('PEN', 'Pending'), ('CON', 'Confirmed'), ('COM', 'Completed'), ('CAN', 'Canceled'), ('MIS', 'Missed')], default='PEN', max_length=3)),
                ('online', models.BooleanField(default=False)),
            ],
        ),
    ]
