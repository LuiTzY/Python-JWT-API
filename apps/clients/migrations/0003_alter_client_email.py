# Generated by Django 5.0.6 on 2024-06-08 17:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0002_mentor'),
    ]

    operations = [
        migrations.AlterField(
            model_name='client',
            name='email',
            field=models.EmailField(max_length=254, unique=True),
        ),
    ]
