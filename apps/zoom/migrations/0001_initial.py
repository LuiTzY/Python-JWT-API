# Generated by Django 5.0.6 on 2024-06-08 17:35

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('clients', '0003_alter_client_email'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserZoomEmail',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('mentor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='clients.mentor')),
            ],
        ),
        migrations.CreateModel(
            name='Zoom',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('access_token', models.TextField()),
                ('refresh_token', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('mentor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='clients.mentor')),
            ],
        ),
    ]