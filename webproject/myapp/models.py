from django.db import models
from django.contrib.auth.models import User


class Contest(models.Model):
    name = models.CharField(max_length=255, unique=True)  # Поле Name
    created_at = models.DateTimeField(auto_now_add=True)  # Дата создания

    def __str__(self):
        return self.name


class Topic(models.Model):
    name = models.CharField(max_length=255)  # Название топика
    content = models.TextField()  # Текст поста
    created_at = models.DateTimeField(auto_now_add=True)  # Дата создания

    def __str__(self):
        return self.name


class Comment(models.Model):
    text = models.TextField()  # Текст комментария
    created_at = models.DateTimeField(auto_now_add=True)  # Дата создания

    # Ссылка на автора комментария (пользователь)
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='comments'
    )

    # Комментарий может быть связан с топиком
    topic = models.ForeignKey(
        Topic, on_delete=models.CASCADE, related_name='comments',
        blank=True, null=True
    )

    # Или с другим комментарием (для вложенных ответов)
    parent_comment = models.ForeignKey(
        'self', on_delete=models.CASCADE, related_name='replies',
        blank=True, null=True
    )

    def __str__(self):
        return f'Comment by {self.author.username} on {self.created_at}'


class Task(models.Model):
    contest = models.ForeignKey(Contest, related_name='tasks', on_delete=models.CASCADE)
    name = models.CharField(max_length=255, default='default_value')
    condition = models.TextField()  # Условие задачи
    correct_answer = models.CharField(max_length=255)  # Верный ответ

    def __str__(self):
        return f"{self.contest.name} - Задача {self.id}"


class UserAnswer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    user_answer = models.CharField(max_length=255)
    is_correct = models.BooleanField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.task} - {'Правильно' if self.is_correct else 'Неправильно'}"
