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

class ContestPage(models.Model):
    contest = models.ForeignKey(Contest, related_name='pages', on_delete=models.CASCADE)
    title = models.CharField(max_length=100)  # Название вкладки
    content = models.TextField()  # Содержимое вкладки
    order = models.IntegerField(default=0)  # Порядок вкладки, если нужно сортировать

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['order']  # Сортируем страницы по порядку


