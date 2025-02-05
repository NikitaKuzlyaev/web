# Generated by Django 5.1.2 on 2024-12-09 15:13

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0009_contestthresholdsubmission'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contestthresholdsubmission',
            name='contest',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='thresholds', to='myapp.contest'),
        ),
        migrations.CreateModel(
            name='ContestTag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=20)),
                ('color', models.CharField(choices=[('#FF0000', 'Красный'), ('#0000FF', 'Синий'), ('#00FF00', 'Зеленый'), ('#FFA500', 'Оранжевый'), ('#FFFF00', 'Желтый'), ('#800080', 'Пурпурный'), ('#00FFFF', 'Циановый'), ('#FFC0CB', 'Розовый'), ('#000000', 'Черный'), ('#FFFFFF', 'Белый'), ('#A52A2A', 'Коричневый'), ('#808080', 'Серый'), ('#ADD8E6', 'Светло-голубой'), ('#FF6347', 'Томато'), ('#32CD32', 'Лаймовый')], default='#0000FF', max_length=7)),
                ('contest', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tag', to='myapp.contest')),
            ],
        ),
    ]
