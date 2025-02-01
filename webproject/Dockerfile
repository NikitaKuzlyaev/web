# our base image
FROM python:3.12

# Устанавливаем pip
RUN pip install --upgrade pip

# Копируем только requirements.txt
COPY requirements.txt .
RUN pip install -r requirements.txt

# Копируем весь проект
COPY ./ ./

# expose the port the app runs on
EXPOSE 8000

# Command to run the app
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "webproject.wsgi:application"]
