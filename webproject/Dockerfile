# our base image
FROM python:3.12
RUN pip install --upgrade pip

COPY ./ ./
RUN pip install -r requirements.txt
# specify the port number the container should expose
EXPOSE 8000


# Команда для запуска вашего приложения
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "webproject.wsgi:application"]