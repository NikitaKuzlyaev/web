import os
import django
from django.core.management import call_command
from io import StringIO

# Указываем модуль настроек Django
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'

# Инициализируем Django
django.setup()

# Получаем дамп данных
output = StringIO()
call_command('dumpdata', '--natural-primary', '--natural-foreign', '--exclude', 'auth.permission', '--exclude', 'contenttypes', stdout=output)

# Сохраняем в файл с нужной кодировкой (UTF-8)
with open('data.json', 'w', encoding='utf-8') as f:
    f.write(output.getvalue())
