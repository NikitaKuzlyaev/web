# Generated by Django 5.1.2 on 2025-01-17 05:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0012_quizfieldcell_col_quizfieldcell_row_quizuser'),
    ]

    operations = [
        migrations.AlterField(
            model_name='quizfieldcell',
            name='cell_type',
            field=models.CharField(choices=[('normal', 'Normal'), ('not_created', 'NotCreated'), ('blocked', 'Blocked'), ('special', 'Special')], default='not_created', max_length=20),
        ),
    ]
