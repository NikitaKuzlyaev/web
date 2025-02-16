# Generated by Django 5.1.2 on 2025-01-30 14:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0015_quizuser_user'),
    ]

    operations = [
        migrations.CreateModel(
            name='AppConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('allow_registration', models.BooleanField(default=True, verbose_name='Разрешить регистрацию пользователей')),
                ('enable_feature_x', models.BooleanField(default=False, verbose_name='Включить функцию X')),
            ],
        ),
        migrations.AlterField(
            model_name='quizfield',
            name='width',
            field=models.PositiveIntegerField(default=5),
        ),
    ]
