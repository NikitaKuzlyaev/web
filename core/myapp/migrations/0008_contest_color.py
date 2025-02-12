# Generated by Django 5.1.2 on 2024-12-04 15:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0007_profile_contest_access'),
    ]

    operations = [
        migrations.AddField(
            model_name='contest',
            name='color',
            field=models.CharField(choices=[('#FF0000', 'Красный'), ('#0000FF', 'Синий'), ('#00FF00', 'Зеленый'), ('#FFA500', 'Оранжевый'), ('#FFFF00', 'Желтый'), ('#800080', 'Пурпурный'), ('#00FFFF', 'Циановый'), ('#FFC0CB', 'Розовый'), ('#000000', 'Черный'), ('#FFFFFF', 'Белый'), ('#A52A2A', 'Коричневый'), ('#808080', 'Серый'), ('#ADD8E6', 'Светло-голубой'), ('#FF6347', 'Томато'), ('#32CD32', 'Лаймовый')], default='#0000FF', max_length=7),
        ),
    ]
