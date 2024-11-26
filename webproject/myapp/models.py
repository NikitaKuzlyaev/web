from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    name = models.CharField(max_length=255, unique=False)

    def __str__(self):
        return f"Profile of {self.user.username}"

class Contest(models.Model):
    name = models.CharField(max_length=255, unique=True)  # Поле Name
    created_at = models.DateTimeField(auto_now_add=True)  # Дата создания

    def __str__(self):
        return self.name


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
