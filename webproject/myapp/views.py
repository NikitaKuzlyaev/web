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
from django.db.models import Max, Prefetch
from django.db import models
from .models import AppConfig
from .forms import (
    CustomUserCreationForm, ContestForm, ContestPageForm,
    ContestUserProfileForm, CodeEditForm, ContestTagForm, QuizProblemForm, AppConfigForm
)
from .models import (
    User, Contest, ContestPage, BlogPage, ContestCheckerPythonCode,
    ContestCheckerAnswerFile, ContestThresholdSubmission,
    SubmissionFile, Submission, Profile, ContestTag, Quiz, QuizField, QuizFieldCell,
    QuizAttempt, QuizProblem, QuizUser
)
from .models import UploadedImage
# from .forms import ImageUploadForm
from .forms import FileUploadForm

from .utils import have_access
from . import utils

# Внешние библиотеки
import pandas as pd
import numpy as np
from sklearn.metrics import mean_squared_error
from io import StringIO
import ast
import pytz
import time
import logging
import json
import datetime
from .politics import Politics

# Имя логгера из настроек
logger = logging.getLogger('myapp')

# Получение текущего времени в UTC+7
timezone_utc7 = pytz.timezone('Asia/Bangkok')  # UTC+7


def is_admin(user):
    return user.is_staff  # или user.is_superuser, если хотите ограничить только суперпользователя


#
#
# def contest_user_access_politic(view_func):
#     """
#     Кастомный декоратор, проверяющий, имеет ли пользователь доступ к контесту.
#     """
#
#     def _wrapped_view(request, *args, **kwargs):
#         contest_id = kwargs.get('contest_id')
#         if contest_id:
#             user = request.user
#             if not have_access(user, contest_id=contest_id):
#                 return redirect('/contests/')  # Если доступа нет, редиректим на страницу с соревнованиями
#         return view_func(request, *args, **kwargs)
#
#     return user_passes_test(lambda u: u.is_authenticated)(_wrapped_view)
#
#
# def contest_time_access_politic(view_func):
#     """
#     Проверка по времени доступа к контесту.
#     Пользователь проходит по политике, когда он или администратор, или соревнование идет сейчас
#     """
#
#     def _wrapped_view(request, *args, **kwargs):
#         contest_id = kwargs.get('contest_id')
#         if contest_id:
#             contest = Contest.objects.filter(id=contest_id).first()
#             if not contest:
#                 return redirect('/contests/')
#
#             user = request.user
#             if user.is_staff:
#                 return view_func(request, *args, **kwargs)
#
#             current_time_utc7 = now().astimezone(timezone_utc7)
#             time_start = contest.time_start.astimezone(timezone_utc7)
#             time_end = contest.time_end.astimezone(timezone_utc7)
#
#             logger.debug(f"Current time: {current_time_utc7}, Start: {time_start}, End: {time_end}")
#             if current_time_utc7 < time_start or current_time_utc7 > time_end:
#                 logger.debug(f"Access denied: Current time {current_time_utc7} is outside [{time_start}, {time_end}]")
#                 return redirect('/contests/')
#
#         return view_func(request, *args, **kwargs)
#
#     return user_passes_test(lambda u: u.is_authenticated)(_wrapped_view)
#
#
# def contest_preview_time_access_politic(view_func):
#     """
#     Проверка по времени доступа к превью контеста.
#     """
#
#     def _wrapped_view(request, *args, **kwargs):
#         contest_id = kwargs.get('contest_id')
#         if contest_id:
#             contest = Contest.objects.filter(id=contest_id).first()
#             if not contest:
#                 return redirect('/contests/')
#
#             user = request.user
#             if user.is_staff:
#                 return view_func(request, *args, **kwargs)
#
#             current_time_utc7 = now().astimezone(timezone_utc7)
#             time_start = contest.time_start.astimezone(timezone_utc7)
#             time_end = contest.time_end.astimezone(timezone_utc7)
#
#             logger.debug(f"Current time: {current_time_utc7}, Start: {time_start}, End: {time_end}")
#             if contest.is_open_preview:
#                 # Ok. Доступ на просмотр разрешен
#                 return view_func(request, *args, **kwargs)
#
#             if current_time_utc7 < time_start or current_time_utc7 > time_end:
#                 logger.debug(f"Access denied: Current time {current_time_utc7} is outside [{time_start}, {time_end}]")
#                 return redirect('/contests/')
#
#         return view_func(request, *args, **kwargs)
#
#     return user_passes_test(lambda u: u.is_authenticated)(_wrapped_view)
#
#
# def contest_results_access_politic(view_func):
#     """
#     Проверка по времени доступа к результатам контеста.
#     """
#
#     def _wrapped_view(request, *args, **kwargs):
#         contest_id = kwargs.get('contest_id')
#         if contest_id:
#             contest = Contest.objects.filter(id=contest_id).first()
#             if not contest:
#                 return redirect('/contests/')
#
#             user = request.user
#             if user.is_staff:
#                 return view_func(request, *args, **kwargs)
#
#             if contest.is_open_results:
#                 # Ok. Доступ на просмотр разрешен
#                 return view_func(request, *args, **kwargs)
#
#             return redirect('/contests/')
#
#         return view_func(request, *args, **kwargs)
#
#     return user_passes_test(lambda u: u.is_authenticated)(_wrapped_view)


def logout_view(request):
    logout(request)  # Завершение сеанса
    return redirect('main')  # Перенаправление после logout


def main(request):
    # blogs = BlogPage.objects.all().order_by('-created_at')
    blogs = BlogPage.objects.all()

    context = {
        'blogs': blogs,
    }

    return render(request, 'main.html', context)


def contests(request):
    return render(request, 'contests.html')


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid() and utils.is_registration_allowed():
            user = form.save()
            login(request, user)  # Автоматически авторизовать пользователя
            return redirect('main')  # Перенаправление на домашнюю страницу

    form = CustomUserCreationForm()
    context = {
        'form': form,
        'is_registration_allowed': utils.is_registration_allowed(),

    }

    return render(request, 'register.html', context)


def blank_page(request):
    return render(request, 'blank_page.html', {})


def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('main')  # Перенаправление на домашнюю страницу
    return render(request, 'login.html')


@user_passes_test(is_admin)
def main_blog_edit(request, blog_id=None):
    if request.method == 'POST':
        if 'create_blog' in request.POST:
            BlogPage.objects.create(title=request.POST.get('title'),
                                    content=request.POST.get('content'),
                                    priority=request.POST.get('priority'),
                                    author=request.user,
                                    created_at=now())
            print('новость создана')
            return redirect('main')

        elif 'save_blog' in request.POST:

            blog_id = request.POST.get('blog_id')
            blog = get_object_or_404(BlogPage, id=blog_id)

            if blog != None:
                title = request.POST.get('title')
                content = request.POST.get('content')
                priority = request.POST.get('priority')

                # Обновление данных вкладки
                blog.title = title
                blog.content = content
                blog.priority = priority
                blog.save()
                return redirect('main')

        elif 'delete_blog' in request.POST:
            pass
            return redirect('main')

        # blogs = BlogPage.objects.all().order_by('priority', 'created_at')
        blogs = BlogPage.objects.all()
        logger.debug('hehe')
        context = {
            'blogs': blogs,
        }

        return render(request, 'main.html', context)

    if blog_id:
        # Получаем существующую новость для редактирования
        blog = get_object_or_404(BlogPage, id=blog_id)
        message = f"Редактируется новость с ID {blog_id}"

        context = {
            'blog': blog,
        }
        logger.debug('hehe2')

        return render(request, 'main_blog_edit.html', context)

    else:
        context = {
            'blog': None,
        }
        logger.debug('hehe3')

        return render(request, 'main_blog_edit.html', context)


@user_passes_test(is_admin)
def main_blog_delete(request, blog_id):
    blog = get_object_or_404(BlogPage, id=blog_id)
    blog.delete()

    blogs = BlogPage.objects.all().order_by('-created_at')
    context = {
        'blogs': blogs,
    }

    return render(request, 'main.html', context)


@login_required
def submit_file(request):
    # Получаем contest_id и select_page из POST-запроса
    contest_id = request.POST.get('contest_id')
    select_page_id = request.POST.get('select_page')

    # Получаем объект конкурса (contest) и страницу (page)
    contest = get_object_or_404(Contest, id=contest_id)
    selected_page = None
    if str(select_page_id).isnumeric():
        selected_page = get_object_or_404(ContestPage, id=select_page_id)  # Здесь предполагается, что Page — это модель для страниц
    contest_pages = contest.pages.all()

    # Контекст, который будет передан в шаблон
    context = {
        'contest': contest,
        'contest_pages': contest_pages,
        'selected_page': selected_page,
    }

    if request.method == 'POST':
        # Получаем файл через get() для безопасной обработки, если файл отсутствует
        uploaded_file = request.FILES.get('file')

        if uploaded_file:

            # Создаем объект SubmissionFile
            submission_file = SubmissionFile.objects.create(
                file=uploaded_file,
                file_type=uploaded_file.content_type,  # Определяем тип файла (например, 'text/csv')
            )
            submission_file.save()

            # Создаем объект Submission
            submission = Submission.objects.create(
                contest=contest,
                user=request.user,
                submission_file=submission_file,
                status_code=0,  # Например, статус "в ожидании проверки"
                metrics={},  # Пустой JSON для метрик
            )
            submission.save()

            # Здесь можно сохранить файл
            messages.success(request, 'Файл успешно загружен!')

            # Получаем код из модели ContestCheckerPythonCode, связанный с конкретным контестом
            contest_checker_code = ContestCheckerPythonCode.objects.get(contest=contest)
            code = contest_checker_code.code  # Код, который нужно выполнить

            # Получаем файл из модели ContestCheckerAnswerFile, связанный с контестом
            answer_file = ContestCheckerAnswerFile.objects.filter(contest=contest).first()

            if answer_file:
                # Открываем файл и читаем его содержимое
                with open(answer_file.file.path, 'r') as file:
                    csv_answer = file.read()  # Содержимое CSV файла
            else:
                csv_answer = None

            if uploaded_file:
                # Считываем содержимое загруженного файла
                with open(submission_file.file.path, 'r') as file:
                    csv_part = file.read()  # Содержимое CSV файла
            else:
                csv_part = None
            # Подготовим данные для передачи в exec

            globals_dict = {}
            locals_dict = {
                'csv_str_1': csv_answer,  # Параметр csv_data передается в код
                'csv_str_2': csv_part
            }

            # Выполняем код из базы данных
            exec(code, globals_dict, locals_dict)

            # После выполнения кода можно получить результат из locals_dict
            result = locals_dict.get('result_dict', '{}')  # Например, если результат сохраняется в переменную result

            if 'status' not in result:
                # Обновляем поле metrics
                submission.status_code = 1
            else:
                metrics = {}
                for key in result:
                    if key != 'status':
                        try:
                            metrics[str(key)] = float(result[key])
                        except:
                            pass

            submission.metrics = metrics
            # Сохраняем изменения
            submission.save()

            # Преобразование строки в словарь
            # result_dict = ast.literal_eval(result)
            print(result)  # {'mse': 0.0, 'status': 'ok'}

            messages.success(request, result)

        else:
            messages.error(request, 'Не выбран файл для загрузки.')

    else:
        messages.error(request, 'Неверный метод запроса.')

    return render(request, 'contest_detail.html', context)


# @login_required
def contests_view(request):
    # Получаем все соревнования и связанные теги
    # Получаем только те соревнования, для которых существует связанный Quiz
    contests = (
        Contest.objects.filter(quiz__isnull=True)
        .prefetch_related('tag')  # Предзагрузка связанных тегов
        .order_by('-created_at')  # Сортировка по дате создания
    )
    # contests = Contest.objects.all().prefetch_related('tag').order_by('-created_at')

    if request.user.is_authenticated:
        user_profile = request.user.profile
    else:
        user_profile = None

    if request.method == 'POST':
        form = ContestForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('contests')
    else:
        form = ContestForm()

    contests_with_tags = []  # Собираем теги в словарь, чтобы удобнее было обращаться в шаблоне
    for contest in contests:
        tags = contest.tag.all()  # Все теги, связанные с соревнованием

        contests_with_tags.append({
            'contest': contest,
            'tags': tags,
        })

    context = {  # Формируем контекст
        'contests_with_tags': contests_with_tags,  # Список соревнований с их тегами
        'form': form,
        'user_profile': user_profile,
    }

    return render(request, 'contests.html', context)


@login_required
@user_passes_test(is_admin)
def contest_detail_view_admin(request, contest_id):
    contest = get_object_or_404(Contest, id=contest_id)

    if request.method == 'POST':
        if 'delete_contest' in request.POST:
            return utils.ContestDetailViewAdmin.handle_contest_delete(request, contest)

        elif 'edit_contest' in request.POST:
            return utils.ContestDetailViewAdmin.handle_edit_contest(request, contest)

        elif 'add_page' in request.POST:  # Обработка добавления вкладки
            return utils.ContestDetailViewAdmin.handle_add_page(request, contest)

        elif 'edit_page' in request.POST:
            return utils.ContestDetailViewAdmin.handle_edit_page(request, contest)

        elif 'save_page' in request.POST:
            return utils.ContestDetailViewAdmin.handle_save_page(request, contest)

        elif 'delete_page' in request.POST:  # Обработка удаления страницы
            return utils.ContestDetailViewAdmin.handle_delete_page(request, contest)

        elif 'add_threshold' in request.POST:  # Обработка добавления вкладки
            return utils.ContestDetailViewAdmin.handle_add_threshold(request, contest)

        elif 'add_answer_file' in request.POST:
            utils.ContestDetailViewAdmin.handle_add_answer_file(request, contest)

        elif 'run_checker' in request.POST:
            utils.ContestDetailViewAdmin.handle_run_checker(request, contest)

        elif 'add_tag' in request.POST:  # Добавление нового тега
            utils.ContestDetailViewAdmin.handle_add_tag(request, contest)

        elif 'edit_tag' in request.POST:  # Редактирование существующего тега
            utils.ContestDetailViewAdmin.handle_edit_tag(request, contest)

        elif 'delete_tag' in request.POST:  # Удаление существующего тега
            utils.ContestDetailViewAdmin.handle_delete_tag(request, contest)

    context = utils.ContestDetailViewAdmin.get_context(request, contest)
    # Проверяем, существует ли связанный Quiz для этого contest
    quiz = Quiz.objects.filter(contest=contest).first()  # Получаем первый найденный Quiz или None
    context['quiz'] = quiz

    return render(request, 'contest_detail_admin.html', context)


@login_required
@user_passes_test(is_admin)
def admin_panel(request):
    config = AppConfig.objects.first()

    if request.method == 'POST':
        form = AppConfigForm(request.POST, instance=config)
        if form.is_valid():
            form.save()
            return redirect('admin_panel')
    else:
        form = AppConfigForm(instance=config)

    context = {
        'form': form,
    }

    return render(request, 'admin_panel.html', context)


@login_required
@Politics.contest_results_access_politic(redirect_path='/contests/')
def contest_detail_results(request, contest_id):
    contest = get_object_or_404(Contest, id=contest_id)
    contest_thresholds = contest.thresholds.all()

    # Получаем все Submission для конкретного контеста
    submissions = Submission.objects.filter(contest=contest).exclude(status_code=5)

    # Сортируем по пользователю и времени создания
    submissions = submissions.order_by('user', '-created_at')

    # Фильтруем последние Submission для каждого пользователя
    last_submissions = {}
    for submission in submissions:
        if submission.user not in last_submissions:
            last_submissions[submission.user] = submission

    list_thresholds = []
    for threshold in contest_thresholds:
        sub = threshold.submission
        list_thresholds.append(sub)

    # Преобразуем в список
    final_submissions = list(last_submissions.values()) + list_thresholds

    # Сортируем по последней метрике
    def get_last_metric(submission):
        if submission.metrics:
            last_key = list(submission.metrics.keys())[-1]
            return submission.metrics[last_key]
        return float('-inf')  # Если метрик нет, ставим минимальное значение

    final_submissions.sort(key=get_last_metric, reverse=False)

    objects = []
    counter = 1
    used = set()
    for sub in final_submissions:
        if sub.status_code == 5:
            if sub.metrics != {}:
                # Получаем связанные ContestThresholdSubmission для текущего submission
                threshold_submission = ContestThresholdSubmission.objects.filter(submission=sub).first()
                objects.append({'sub': sub, 'counter': 0, 'name': threshold_submission.title})
        else:
            if sub.user not in used:
                objects.append({'sub': sub, 'counter': counter})
                counter += 1
                used.add(sub.user)

    # Передаем в шаблон
    context = {
        'contest': contest,
        'contest_thresholds': contest_thresholds,
        'submissions': final_submissions,
        'objects': objects
    }

    return render(request, 'contest_detail_results.html', context)


def contest_detail_submissions(request, contest_id):
    contest = get_object_or_404(Contest, id=contest_id)

    # Получаем все Submission для конкретного контеста
    submissions = Submission.objects.filter(contest=contest).exclude(status_code=5)

    # Сортируем по пользователю и времени создания
    submissions = submissions.order_by('-created_at')
    first_sub = 0
    # Передаем в шаблон
    context = {
        'contest': contest,
        'submissions': submissions,
        'first_sub': first_sub,
    }

    return render(request, 'contest_detail_submissions.html', context)


@login_required
@user_passes_test(is_admin)
def contest_detail_view_admin_checker(request, contest_id):
    # Получаем контест
    contest = get_object_or_404(Contest, id=contest_id)

    # Проверяем, существует ли уже код для данного контеста
    code_instance = ContestCheckerPythonCode.objects.filter(contest=contest).first()

    # Создаем форму в случае GET-запроса
    if request.method == 'POST':
        form_code = CodeEditForm(request.POST)  # Получаем данные из POST
        if form_code.is_valid():
            code = form_code.cleaned_data['code']
            # Здесь можно обработать код, например, сохранить в базе данных или выполнить
            # print(code)  # Выводим код в консоль для примера

            # Если код уже существует, обновляем его, иначе создаем новый
            if code_instance:
                code_instance.code = code
                code_instance.save()
            else:
                ContestCheckerPythonCode.objects.create(
                    contest=contest,
                    user=request.user,  # Используем текущего пользователя
                    code=code
                )

            context = {
                'contest': contest,
                'form_code': form_code,  # Отправляем форму в контекст
            }
            # После обработки редиректим или отображаем страницу с успешным сообщением
            return render(request, 'contest_detail_admin_checker.html', context)
        else:
            # Если форма невалидна, выводим ошибки
            print(form_code.errors)  # Выводим ошибки формы для отладки
    else:
        if code_instance:
            form_code = CodeEditForm(instance=code_instance)
        else:
            # Если это GET-запрос, создаем пустую форму
            form_code = CodeEditForm()

    context = {
        'contest': contest,
        'form_code': form_code,  # Отправляем форму в контекст
    }

    return render(request, 'contest_detail_admin_checker.html', context)


@user_passes_test(is_admin)
def move_contest_page(request, page_id, direction):
    page = get_object_or_404(ContestPage, id=page_id)
    contest = page.contest

    # Определяем направление сортировки и фильтрации
    order_filter = 'order__lt' if direction == 'up' else 'order__gt'
    order_by = '-order' if direction == 'up' else 'order'

    # Находим целевую страницу
    target_page = ContestPage.objects.filter(
        contest=contest, **{order_filter: page.order}
    ).order_by(order_by).first()

    # Обмениваем значения `order`, если нашли целевую страницу
    if target_page:
        page.order, target_page.order = target_page.order, page.order
        ContestPage.objects.bulk_update([page, target_page], ['order'])

    # Формируем контекст
    context = {
        'contest': contest,
        'contest_pages': contest.pages.all(),
        'selected_page': None,
        'form_contest': ContestForm(instance=contest),
    }

    return render(request, 'contest_detail_admin.html', context)


@user_passes_test(is_admin)
def edit_contest_page(request, page_id):
    page = get_object_or_404(ContestPage, id=page_id)

    if request.method == 'POST':
        form = ContestPageForm(request.POST, instance=page)
        if form.is_valid():
            form.save()
            return redirect('contest_detail_admin', contest_id=page.contest.id)
    else:
        form = ContestPageForm(instance=page)

    context = {
        'form': form,
        'page': page,
    }

    return render(request, 'edit_contest_page.html', context)


@user_passes_test(is_admin)
def delete_contest_page(request, page_id):
    page = get_object_or_404(ContestPage, id=page_id)
    contest_id = page.contest.id
    page.delete()
    return redirect('contest_detail_admin', contest_id=contest_id)


@Politics.contest_user_access_politic(redirect_path='/contests/')
@Politics.contest_preview_time_access_politic(redirect_path='/contests/')
def contest_detail_view(request, contest_id):
    contest = get_object_or_404(Contest, id=contest_id)
    contest_pages = contest.pages.all()
    selected_page = None  # Для передачи выбранной вкладки в форму

    if request.method == 'POST' and 'select_page' in request.POST:
        page_id = request.POST.get('select_page')
        selected_page = get_object_or_404(ContestPage, id=page_id)

    # Получаем связанный Quiz (если он существует)
    quiz = Quiz.objects.filter(contest=contest).first()

    user_profile = Profile.objects.filter(user=request.user).first()

    context = {
        'user_profile': user_profile.name,
        'contest': contest,
        'contest_pages': contest_pages,
        'selected_page': selected_page,
        'quiz': quiz,
    }

    if quiz:
        user = request.user
        context.update({
            'access_to_results': utils.user_has_access_to_results(user, contest_id),
            'access_to_status': utils.user_has_access_to_status(user, contest_id),
            'access_to_quizfield': utils.user_has_access_to_quizfield(user, contest_id),
        })
        logger.debug(f'{context['access_to_results'], context['access_to_status'], context['access_to_quizfield']}')

    return render(request, 'contest_detail.html', context)



@user_passes_test(is_admin)
def contest_participants_admin(request, contest_id):
    contest = get_object_or_404(Contest, id=contest_id)
    participants = Profile.objects.filter(contest_access=contest)

    if request.method == 'POST':
        if 'delete_participant' in request.POST:
            participant_id = request.POST.get('participant_id')
            if participant_id:
                participant = get_object_or_404(Profile, id=participant_id)
                user = User.objects.filter(profile=participant)
                user.delete()  # Удаляем участника
                return redirect('contest_participants_admin', contest_id=contest.id)  # Перенаправляем на страницу с участниками

        form = ContestUserProfileForm(request.POST)
        if form.is_valid():
            form.save()  # Сохраняем нового пользователя и его профиль
            return redirect('contest_participants_admin', contest_id=contest.id)  # Перенаправляем обратно на страницу с участниками
    else:
        form = ContestUserProfileForm(initial={'contest_access': contest})  # Передаем текущий contest в форму

    context = {
        'contest': contest,
        'participants': participants,
        'form': form,
    }

    return render(request, 'contest_participants_admin.html', context)
