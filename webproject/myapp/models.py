from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    name = models.CharField(max_length=255, unique=False)
    contest_access = models.ForeignKey(
        'Contest',  # Связь с моделью Contest
        on_delete=models.SET_NULL,  # Указывает, что поле останется null, если Contest будет удалён
        null=True,  # Поле может быть пустым в базе данных
        blank=True,  # Поле не обязательно для заполнения в формах
        related_name='profiles',  # Связь для обратного доступа (от Contest к Profile)
        verbose_name='Доступ к соревнованию'
    )

    def __str__(self):
        return f"Profile of {self.user.username}"


class Contest(models.Model):
    name = models.CharField(max_length=255, unique=True)  # Поле Name
    created_at = models.DateTimeField(auto_now_add=True)  # Дата создания
    time_start = models.DateTimeField()  # Время начала
    time_end = models.DateTimeField()  # Время окончания
    is_open = models.BooleanField(default=True)  # Флаг, открыт ли конкурс

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


class BlogPage(models.Model):
    title = models.CharField(max_length=100)  # Название новости
    content = models.TextField()  # Содержимое вкладки
    author = models.ForeignKey(User, on_delete=models.CASCADE)  # Внешний ключ к пользователю
    created_at = models.DateTimeField(auto_now_add=True)  # Время создания

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['created_at']  # Сортируем страницы по времени создания


class SubmissionFile(models.Model):
    file = models.FileField(upload_to='uploads/')  # Сохраняет файл в указанной папке
    file_type = models.CharField(max_length=50, blank=True, null=True)  # Тип файла
    created_at = models.DateTimeField(auto_now_add=True)  # Время создания


class Submission(models.Model):
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE)  # Внешний ключ к соревнованию
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Внешний ключ к пользователю
    created_at = models.DateTimeField(auto_now_add=True)  # Время создания
    submission_file = models.ForeignKey(SubmissionFile, on_delete=models.CASCADE)  # Внешний ключ к посылке
    status_code = models.IntegerField(default=0)
    metrics = models.JSONField()


class ContestChecker(models.Model):
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE)  # Внешний ключ к соревнованию
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Внешний ключ к пользователю
    created_at = models.DateTimeField(auto_now_add=True)  # Время создания
    checker_file = models.FileField(upload_to='uploads/')  # Сохраняет файл в указанной папке


class ContestCheckerPythonCode(models.Model):
    code = models.TextField()  # Поле для хранения кода
    created_at = models.DateTimeField(auto_now_add=True)  # Дата создания
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE)  # Внешний ключ к соревнованию
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Внешний ключ к пользователю

    def __str__(self):
        return f"Python code created on {self.created_at}"


class ContestCheckerAnswerFile(models.Model):
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE)  # Внешний ключ к соревнованию
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Внешний ключ к пользователю
    file = models.FileField(upload_to='uploads/')  # Сохраняет файл в указанной папке
    file_type = models.CharField(max_length=50, blank=True, null=True)  # Тип файла
    created_at = models.DateTimeField(auto_now_add=True)  # Время создания

    def __str__(self):
        return f"Python code created on {self.created_at}"
