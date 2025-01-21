import pika


def send_to_queue(file_content, queue_name="file_queue"):
    # Подключаемся к RabbitMQ
    connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
    channel = connection.channel()

    # Объявляем очередь (если не существует)
    channel.queue_declare(queue=queue_name)

    # Отправляем сообщение (контент файла)
    channel.basic_publish(exchange="", routing_key=queue_name, body=file_content)

    connection.close()
