from django.shortcuts import (
    render, redirect, get_object_or_404
)
from django.http import HttpResponse, JsonResponse
from django.contrib.auth import (
    login, authenticate, logout
)
from django.contrib.auth.decorators import (
    login_required, user_passes_test
)
from django.core.exceptions import ObjectDoesNotExist
from django.contrib import messages
from django.utils.timezone import now
from django.forms import modelformset_factory
from django.db.models import Max
from django.db import models

from .forms import (
    CustomUserCreationForm, ContestForm, ContestPageForm,
    ContestUserProfileForm, CodeEditForm, ContestTagForm, TagFormSet
)
from .models import (
    User, Contest, ContestPage, BlogPage, ContestCheckerPythonCode,
    ContestCheckerAnswerFile, ContestThresholdSubmission,
    SubmissionFile, Submission, Profile, ContestTag
)

# Внешние библиотеки
import pandas as pd
import numpy as np
from sklearn.metrics import mean_squared_error
from io import StringIO
import ast
import pytz
import time
import logging

# utils.py
from .models import AppConfig

# Имя логгера из настроек
logger = logging.getLogger('myapp')
# Получение текущего времени в UTC+7
timezone_utc7 = pytz.timezone('Asia/Bangkok')  # UTC+7


def get_app_config():
    return AppConfig.objects.first()  # Получаем первые настройки (предполагаем, что они будут единственными)


def is_registration_allowed():
    return get_app_config().allow_registration  # Получаем значение флага для регистрации


def have_access(user, contest_id):
    if user.is_staff:
        return True

    contest = get_object_or_404(Contest, id=contest_id)

    if contest.is_open:
        return True

    try:
        profile = Profile.objects.get(user=user)
        if profile.contest_access == contest:
            return True
    except Profile.DoesNotExist:
        return False

    return False


def user_has_access_to_results(user, contest_id):
    if not have_access(user, contest_id):
        return False
    if user.is_staff:
        return True
    contest = get_object_or_404(Contest, id=contest_id)
    return contest.is_open_results

def user_has_access_to_status(user, contest_id):
    if not have_access(user, contest_id):
        return False
    if user.is_staff:
        return True
    contest = get_object_or_404(Contest, id=contest_id)
    return contest.is_open_status


def user_has_access_to_quizfield(user, contest_id):
    contest = get_object_or_404(Contest, id=contest_id)

    if user.is_staff:
        return True

    current_time_utc7 = now().astimezone(timezone_utc7)
    time_start = contest.time_start.astimezone(timezone_utc7)
    time_end = contest.time_end.astimezone(timezone_utc7)

    if current_time_utc7 < time_start or current_time_utc7 > time_end:
        logger.debug(f"Access denied: Current time {current_time_utc7} is outside [{time_start}, {time_end}]")
        return False

    return True


def execute_checker_for_contest(contest, answer_file=None):
    """
    Выполняет код из ContestCheckerPythonCode для заданного контеста,
    используя данные из answer_file (если он передан).

    :param contest: объект контеста
    :param answer_file: объект файла с ответами (опционально)
    :return: результат выполнения кода или ошибка
    """
    try:
        # Получаем код из модели ContestCheckerPythonCode, связанный с контестом
        contest_checker_code = ContestCheckerPythonCode.objects.get(contest=contest)
        code = contest_checker_code.code  # Код, который нужно выполнить
    except ObjectDoesNotExist:
        return {"error": "Контест не найден."}

    csv_answer = None
    if answer_file:
        try:
            with open(answer_file.file.path, 'r') as file:
                csv_answer = file.read()
        except Exception as e:
            return {"error": f"Ошибка при чтении файла: {e}"}

    # Подготовим данные для передачи в код
    locals_dict = {
        'csv_str_1': csv_answer,  # Параметр csv_data передается в код
        'csv_str_2': csv_answer  # Повторное использование
    }

    try:
        exec(code, {}, locals_dict)
        result = locals_dict.get('result_dict', '{}')  # Если результат сохраняется в переменную result
        return result
    except Exception as e:
        return {"error": f"Ошибка при выполнении кода: {e}"}


def score_file_for_contest(contest, answer_file=None, uploaded_file=None):
    try:
        # Получаем код из модели ContestCheckerPythonCode, связанный с контестом
        contest_checker_code = ContestCheckerPythonCode.objects.get(contest=contest)
        code = contest_checker_code.code  # Код, который нужно выполнить
    except ObjectDoesNotExist:
        return {"error": "Контест или проверяющий код не найден."}

    csv_answer = None
    if answer_file:
        try:
            with open(answer_file.file.path, 'r') as file:
                csv_answer = file.read()
        except Exception as e:
            return {"error": f"Ошибка при чтении файла: {e}"}

    csv_part = None
    if uploaded_file:
        try:
            with open(uploaded_file.file.path, 'r') as file:  # Считываем содержимое загруженного файла
                csv_part = file.read()  # Содержимое CSV файла
        except Exception as e:
            return {"error": f"Ошибка при чтении файла: {e}"}

    # Подготовим данные для передачи в код
    locals_dict = {
        'csv_str_1': csv_answer,  # Параметр csv_data передается в код
        'csv_str_2': csv_part  # Повторное использование
    }

    try:
        exec(code, {}, locals_dict)

        result = locals_dict.get('result_dict', '{}')  # Если результат сохраняется в переменную result
        return result
    except Exception as e:
        return {"error": f"Ошибка при выполнении кода: {e}"}


class ContestDetailViewAdmin:
    @staticmethod
    def get_context(request, contest, selected_page=None):
        selected_page = selected_page  # Для передачи выбранной вкладки в форму
        page_id = request.GET.get('page_id')  # Передача в контекст выбранной страницы для редактирования
        if page_id:
            selected_page = get_object_or_404(ContestPage, id=page_id)
        return {
            'contest': contest,
            'contest_pages': contest.pages.all(),
            'selected_page': selected_page,
            'contest_thresholds': contest.thresholds.all(),
            'form_contest': ContestForm(instance=contest),
            'tag_form': ContestTagForm(),
            'tag_formset': modelformset_factory(ContestTag, form=ContestTagForm, extra=0)(queryset=contest.tag.all()),
        }

    @staticmethod
    def handle_contest_delete(request, contest):
        contest.delete()
        return redirect('contests')

    @staticmethod
    def handle_edit_contest(request, contest):
        # Создаем форму с данными из POST-запроса и экземпляром contest
        form_contest = ContestForm(request.POST, instance=contest)

        # Проверяем, валидна ли форма
        if form_contest.is_valid():
            form_contest.save()  # Сохраняем изменения
            # Получаем контекст для рендеринга страницы
            context = ContestDetailViewAdmin.get_context(request, contest)
            return render(request, 'contest_detail_admin.html', context)
        else:
            # Если форма не валидна, можно вернуть ошибку или вернуть форму на страницу
            messages.error(request, 'Ошибка при обновлении контеста.')
            return redirect('contest_detail_admin', contest_id=contest.id)

    @staticmethod
    def handle_add_page(request, contest):
        max_order = ContestPage.objects.filter(contest=contest).aggregate(max_order=models.Max('order'))['max_order']
        new_order = (max_order or 0) + 1  # Если нет страниц (max_order будет None), начнем с 0
        ContestPage.objects.create(title='empty', content='empty', contest=contest, order=new_order)
        messages.success(request, 'Новая вкладка добавлена.')
        return redirect('contest_detail_admin', contest_id=contest.id)

    @staticmethod
    def handle_edit_page(request, contest):
        page_id = request.POST.get('edit_page')
        selected_page = get_object_or_404(ContestPage, id=page_id)
        context = ContestDetailViewAdmin.get_context(request, contest, selected_page=selected_page)
        return render(request, 'contest_detail_admin.html', context)

    @staticmethod
    def handle_save_page(request, contest):
        page_id = str(request.POST.get('page_id'))
        title = request.POST.get('title')
        content = request.POST.get('content')
        if page_id and page_id.isnumeric():
            try:
                page = ContestPage.objects.get(id=page_id)
                page.title = title
                page.content = content
                page.save()
                messages.success(request, f'Вкладка "{title}" была успешно обновлена.')
            except ContestPage.DoesNotExist:
                messages.error(request, 'Ошибка: Вкладка не найдена.')
        else:
            max_order = ContestPage.objects.filter(contest=contest).aggregate(max_order=models.Max('order'))['max_order']
            new_order = (max_order or 0) + 1
            ContestPage.objects.create(title=title, content=content, contest=contest, order=new_order)
            messages.success(request, 'Новая вкладка добавлена.')

        return redirect('contest_detail_admin', contest_id=contest.id)

    @staticmethod
    def handle_delete_page(request, contest):
        page_id = request.POST.get('page_id')
        page = get_object_or_404(ContestPage, id=page_id)
        page.delete()
        messages.success(request, 'Вкладка была удалена.')
        return redirect('contest_detail_admin', contest_id=contest.id)

    @staticmethod
    def handle_add_threshold(request, contest):
        uploaded_file = request.FILES.get('file_threshold')

        submission_file = SubmissionFile.objects.create(  # Создаем объект SubmissionFile
            file=uploaded_file,
            file_type=uploaded_file.content_type,
        )
        submission_file.save()

        submission = Submission.objects.create(  # Создаем объект Submission
            contest=contest,
            user=request.user,
            submission_file=submission_file,
            status_code=5,  # не показывать в таблице лидеров
            metrics={},  # Пустой JSON для метрик
        )
        submission.save()

        messages.success(request, 'Файл успешно загружен!')

        # Получаем файл из модели ContestCheckerAnswerFile, связанный с контестом
        answer_file = ContestCheckerAnswerFile.objects.filter(contest=contest).first()

        result = score_file_for_contest(contest, answer_file, submission_file)

        if 'status' not in result:
            # Обновляем поле metrics
            submission.status_code = 5
        else:
            metrics = {}
            for key in result:
                if key != 'status':
                    try:
                        metrics[str(key)] = float(result[key])
                    except Exception as e:
                        return {"error": f"Ошибка при формировании метрик: {e}"}

            submission.metrics = metrics

        print('\n', submission.metrics, '\n')
        submission.save()

        # Создаем объект Submission
        contest_threshold = ContestThresholdSubmission.objects.create(
            contest=contest,
            title=request.POST.get('title_threshold'),
            user=request.user,
            submission=submission,
        )
        contest_threshold.save()

        context = ContestDetailViewAdmin.get_context(request, contest)
        return render(request, 'contest_detail_admin.html', context=context)

    @staticmethod
    def handle_add_answer_file(request, contest):
        uploaded_file = request.FILES.get('file')
        if uploaded_file:
            # Получаем или создаем новый объект для файла, связанного с контестом и пользователем
            existing_file, created = ContestCheckerAnswerFile.objects.update_or_create(
                contest=contest, user=request.user,
                defaults={'file': uploaded_file}
            )
            if created:
                messages.success(request, 'Файл успешно загружен!')
            else:
                messages.success(request, 'Файл успешно обновлен!')
        else:
            messages.error(request, 'Не выбран файл для загрузки.')

    @staticmethod
    def handle_run_checker(request, contest):
        answer_file = ContestCheckerAnswerFile.objects.filter(contest=contest).first()
        result = execute_checker_for_contest(contest, answer_file=answer_file)
        if "error" in result:
            messages.error(request, result["error"])
        else:
            messages.success(request, f"Результат выполнения: {result}")

    @staticmethod
    def handle_add_tag(request, contest):
        tag_form = ContestTagForm(request.POST)
        if tag_form.is_valid():
            contest_id = request.POST.get('contest_id')
            contest = get_object_or_404(Contest, id=contest_id)
            tag = tag_form.save(commit=False)
            tag.contest = contest
            tag.save()
            messages.success(request, 'тег добавлен')

    @staticmethod
    def handle_edit_tag(request, contest):
        tag_formset1 = TagFormSet(request.POST)
        if tag_formset1.is_valid():
            tag_formset1.save()  # Сохраняем все формы в форме-сете
            messages.success(request, 'Теги обновлены')
        else:
            messages.error(request, 'Ошибка при обновлении тегов')

    @staticmethod
    def handle_delete_tag(request, contest):
        action = request.POST.get('delete_tag')
        if action and action.startswith('delete_'):
            tag_id = action.split('_')[1]
            if not tag_id.isdigit():
                messages.error(request, "Ошибка: Неверный идентификатор тега.")
                return redirect('contest_detail_admin', contest_id=contest.id)
            try:
                tag = ContestTag.objects.get(id=tag_id, contest=contest)  # Проверка на принадлежность конкурсу
                tag.delete()
                messages.success(request, f"Тег '{tag.title}' был успешно удален.")
            except ContestTag.DoesNotExist:
                messages.error(request, "Ошибка: Тег не найден или уже удален.")
        else:
            messages.error(request, "Ошибка: Некорректный формат действия.")
