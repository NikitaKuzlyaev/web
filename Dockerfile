# Базовый образ для Python
FROM python:3.12


# Установка зависимостей
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Создание рабочей директории в контейнере
WORKDIR /app

# Копирование кода проекта в контейнер

COPY . /app

# Удаляем старое окружение, если оно было скопировано
RUN rm -rf myenv

# Создаём новое окружение с теми же зависимостями
RUN python -m venv /app/venv

# Настраиваем окружение
ENV PATH="/app/venv/bin:$PATH"

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /app/core

# Установка uWSGI
RUN pip install uwsgi

# Создание директории для логов
RUN mkdir -p /var/log/uwsgi


# Открытие порта для uWSGI
EXPOSE 8001

# Запуск uWSGI с указанием конфигурационного файла
CMD uwsgi --ini /app/uwsgi.ini

# Запуск встроенного сервера Django
#CMD ["python", "manage.py", "runserver", "0.0.0.0:8001"]
