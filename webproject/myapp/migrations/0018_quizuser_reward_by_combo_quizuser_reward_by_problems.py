# Generated by Django 5.1.2 on 2025-01-31 08:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0017_quizuser_combo_score'),
    ]

    operations = [
        migrations.AddField(
            model_name='quizuser',
            name='reward_by_combo',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='quizuser',
            name='reward_by_problems',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
