# Generated by Django 4.2.13 on 2024-07-30 02:35

import core.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_user_profile_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='profile_image',
            field=models.FileField(blank=True, null=True, upload_to=core.models.file_generate_upload_path),
        ),
    ]
