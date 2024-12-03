import time
from django.shortcuts import render
# Create your views here.
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from .forms import CustomUserCreationForm  # Импортируем кастомную форму
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.contrib.auth.models import User
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.decorators import login_required
from .models import Contest
from .forms import ContestForm
from .forms import ContestPageForm
from .models import ContestPage
from .models import BlogPage
from django.http import JsonResponse
from django.utils.timezone import now
# main/views.py
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from .models import Contest, ContestPage
from .forms import ContestPageForm
from .forms import ContestUserProfileForm
from django.db import models
from .models import Contest
from .models import Contest
from django.contrib import messages
from .forms import CodeEditForm
from .models import ContestCheckerPythonCode
from .models import ContestCheckerAnswerFile
import pandas as pd
import numpy as np
from sklearn.metrics import mean_squared_error
from io import StringIO
import ast
from .models import SubmissionFile
from .models import Submission
from .models import Profile
from .utils import have_access  # Импортируем функцию из utils.py

def is_admin(user):
    return user.is_staff  # или user.is_superuser, если хотите ограничить только суперпользователямp


def contest_access_required(view_func):
    """
    Кастомный декоратор, проверяющий, имеет ли пользователь доступ к конкурсу.
    Используется для проверки как у администратора, так и у обычного пользователя с доступом к конкурсу.
    """

    def _wrapped_view(request, *args, **kwargs):
        contest_id = kwargs.get('contest_id')
        if contest_id:
            user = request.user
            # Ваша логика проверки, например:
            if not have_access(user, contest_id=contest_id):
                return redirect('/contests/')  # Если доступа нет, редиректим на страницу с соревнованиями
        return view_func(request, *args, **kwargs)

    return user_passes_test(lambda u: u.is_authenticated)(_wrapped_view)


def logout_view(request):
    logout(request)  # Завершение сеанса
    return redirect('main')  # Перенаправление после logout


def main(request):
    blogs = BlogPage.objects.all().order_by('-created_at')
    context = {
        'blogs': blogs,
    }
    return render(request, 'main.html', context)


def contests(request):
    return render(request, 'contests.html')


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Автоматически авторизовать пользователя
            return redirect('main')  # Перенаправление на домашнюю страницу
    else:
        form = CustomUserCreationForm()
    return render(request, 'register.html', {'form': form})


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
                                    author=request.user,
                                    created_at=now())
            print('новость создана')

        elif 'save_blog' in request.POST:

            blog_id = request.POST.get('blog_id')
            blog = get_object_or_404(BlogPage, id=blog_id)

            if blog != None:
                title = request.POST.get('title')
                content = request.POST.get('content')

                # Обновление данных вкладки
                blog.title = title
                blog.content = content
                blog.save()

        elif 'delete_blog' in request.POST:
            pass

        blogs = BlogPage.objects.all().order_by('created_at')
        context = {
            'blogs': blogs,
        }

        return render(request, 'main.html', context)

    else:
        if blog_id:
            # Получаем существующую новость для редактирования
            blog = get_object_or_404(BlogPage, id=blog_id)
            message = f"Редактируется новость с ID {blog_id}"

            context = {
                'blog': blog,
            }

            return render(request, 'main_blog_edit.html', context)

        else:
            context = {
                'blog': None,
            }

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

        # if (not contest.is_open):
        #     messages.error(request, 'Не выбран файл для загрузки.')
        #     uploaded_file = None

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

            # messages.success(request, 'Файл успешно загружен!')

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
    contests = Contest.objects.all().order_by('-created_at')  # Получаем все соревнования

    if request.user.is_authenticated:
        user_profile = request.user.profile  # Access user profile if user is authenticated
    else:
        user_profile = None  # Handle case when user is not authenticated

    if request.method == 'POST':
        form = ContestForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('contests')  # Redirect to contests page after creating a contest
    else:
        form = ContestForm()

        # Combine context into one dictionary
    context = {
        'contests': contests,
        'form': form,
        'user_profile': user_profile,  # Pass user profile to template
    }

    return render(request, 'contests.html', context)


@login_required
@user_passes_test(is_admin)
def contest_detail_view_admin(request, contest_id):
    contest = get_object_or_404(Contest, id=contest_id)
    contest_pages = contest.pages.all()

    selected_page = None  # Для передачи выбранной вкладки в форму

    form_contest = ContestForm(instance=contest)
    # Передача в контекст выбранной страницы для редактирования
    page_id = request.GET.get('edit_page_id')
    if page_id:
        selected_page = get_object_or_404(ContestPage, id=page_id)

    context = {
        'contest': contest,
        'contest_pages': contest_pages,
        'selected_page': selected_page,
        'form_contest': form_contest,
    }

    if request.method == 'POST':
        if 'delete_contest' in request.POST:
            # contest_id = request.POST.get('contest_id')
            # contest = get_object_or_404(contest, id=contest_id)
            contest.delete()
            # messages.success(request, 'Задача успешно удалена.')
            return redirect('contests')

        elif 'edit_contest' in request.POST:
            form_contest = ContestForm(request.POST, instance=contest)
            if form_contest.is_valid():
                form_contest.save()
                # Здесь можно добавить редирект или сообщение об успехе
                context = {
                    'contest': contest,
                    'contest_pages': contest_pages,
                    'selected_page': selected_page,
                    'form_contest': form_contest,
                }
                return render(request, 'contest_detail_admin.html', context)

        # Обработка добавления вкладки
        elif 'add_page' in request.POST:
            # Найти максимальное значение order в таблице ContestPage для данного конкурса
            max_order = ContestPage.objects.filter(contest=contest).aggregate(max_order=models.Max('order'))['max_order']
            # Если нет страниц (max_order будет None), начнем с 0
            new_order = (max_order or 0) + 1

            ContestPage.objects.create(title='empty', content='empty', contest=contest, order=new_order)
            messages.success(request, 'Новая вкладка добавлена.')
            return redirect('contest_detail_admin', contest_id=contest.id)

        elif 'edit_page' in request.POST:
            page_id = request.POST.get('edit_page')
            selected_page = get_object_or_404(ContestPage, id=page_id)
            context = {
                'contest': contest,
                'contest_pages': contest_pages,
                'selected_page': selected_page,
                'form_contest': form_contest,
            }
            return render(request, 'contest_detail_admin.html', context)

        elif 'save_page' in request.POST:
            page_id = request.POST.get('page_id')

            if str(page_id).isnumeric():
                page = get_object_or_404(ContestPage, id=page_id)

                if page != None:
                    title = request.POST.get('title')
                    content = request.POST.get('content')

                    # Обновление данных вкладки
                    page.title = title
                    page.content = content
                    page.save()

                    messages.success(request, f'Вкладка "{title}" была успешно обновлена.')
            else:
                title = request.POST.get('title')
                content = request.POST.get('content')
                # Найти максимальное значение order в таблице ContestPage для данного конкурса
                max_order = ContestPage.objects.filter(contest=contest).aggregate(max_order=models.Max('order'))['max_order']
                # Если нет страниц (max_order будет None), начнем с 0
                new_order = (max_order or 0) + 1

                ContestPage.objects.create(title=title, content=content, contest=contest, order=new_order)
                messages.success(request, 'Новая вкладка добавлена.')
                return redirect('contest_detail_admin', contest_id=contest.id)
            return redirect('contest_detail_admin', contest_id=contest.id)

        # Обработка удаления страницы
        elif 'delete_page' in request.POST:
            page_id = request.POST.get('page_id')
            page = get_object_or_404(ContestPage, id=page_id)
            page.delete()

            messages.success(request, 'Вкладка была удалена.')
            return redirect('contest_detail_admin', contest_id=contest.id)

        elif 'add_answer_file' in request.POST:
            # Получаем файл через get() для безопасной обработки, если файл отсутствует
            uploaded_file = request.FILES.get('file')

            if uploaded_file:
                # Проверяем, существует ли уже запись для этого контеста и пользователя
                try:
                    # Получаем или создаем новый объект
                    existing_file = ContestCheckerAnswerFile.objects.get(contest=contest)
                    # Если объект существует, обновляем его файл
                    existing_file.file = uploaded_file
                    existing_file.save()  # Сохраняем изменения
                    messages.success(request, 'Файл успешно обновлен!')
                except ContestCheckerAnswerFile.DoesNotExist:
                    # Если такого файла нет, создаем новый
                    new_file = ContestCheckerAnswerFile(
                        contest=contest,
                        user=request.user,
                        file=uploaded_file,
                    )
                    new_file.save()
                    messages.success(request, 'Файл успешно загружен!')

            else:
                messages.error(request, 'Не выбран файл для загрузки.')

        elif 'run_checker' in request.POST:
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

            csv_part = csv_answer
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

            # Преобразование строки в словарь
            # result_dict = ast.literal_eval(result)
            print(result)  # {'mse': 0.0, 'status': 'ok'}

            messages.success(request, result)

    else:
        # form = ContestPageForm(instance=contest)
        form_contest = ContestForm(instance=contest)
        pass

    # Передача в контекст выбранной страницы для редактирования
    page_id = request.GET.get('edit_page_id')
    if page_id:
        selected_page = get_object_or_404(ContestPage, id=page_id)

    form_contest = ContestForm(instance=contest)
    context = {
        'contest': contest,
        'contest_pages': contest_pages,
        'selected_page': selected_page,
        'form_contest': form_contest,
    }

    return render(request, 'contest_detail_admin.html', context)


from django.db.models import Max


def contest_detail_results(request, contest_id):
    contest = get_object_or_404(Contest, id=contest_id)

    # Получаем все Submission для конкретного контеста
    submissions = Submission.objects.filter(contest=contest)

    # Сортируем по пользователю и времени создания
    submissions = submissions.order_by('user', '-created_at')

    # Фильтруем последние Submission для каждого пользователя
    last_submissions = {}
    for submission in submissions:
        if submission.user not in last_submissions:
            last_submissions[submission.user] = submission

    # Преобразуем в список
    final_submissions = list(last_submissions.values())

    # Сортируем по последней метрике
    def get_last_metric(submission):
        if submission.metrics:
            last_key = list(submission.metrics.keys())[-1]
            return submission.metrics[last_key]
        return float('-inf')  # Если метрик нет, ставим минимальное значение

    final_submissions.sort(key=get_last_metric, reverse=False)

    # Передаем в шаблон
    context = {
        'contest': contest,
        'submissions': final_submissions,
    }

    return render(request, 'contest_detail_results.html', context)


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

    contest_pages = contest.pages.all()
    selected_page = None  # Для передачи выбранной вкладки в форму
    target_page = None
    if direction == 'up':
        # Найти страницу выше по order
        target_page = ContestPage.objects.filter(
            contest=page.contest,
            order__lt=page.order  # Меньший порядок
        ).order_by('-order').first()  # Самый большой из меньших
    elif direction == 'down':
        # Найти страницу ниже по order
        target_page = ContestPage.objects.filter(
            contest=page.contest,
            order__gt=page.order  # Больший порядок
        ).order_by('order').first()  # Самый маленький из больших

    # Если есть страница для обмена
    if target_page:
        # Меняем их значения order
        page.order, target_page.order = target_page.order, page.order
        page.save()
        target_page.save()

    form_contest = ContestForm(instance=contest)
    context = {
        'contest': contest,
        'contest_pages': contest_pages,
        'selected_page': selected_page,
        'form_contest': form_contest,
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


# @login_required

# Используем лямбда-функцию для получения contest_id из request
@contest_access_required
def contest_detail_view(request, contest_id):
    contest = get_object_or_404(Contest, id=contest_id)

    contest_pages = contest.pages.all()
    selected_page = None  # Для передачи выбранной вкладки в форму

    if request.method == 'POST':
        if 'select_page' in request.POST:
            page_id = request.POST.get('select_page')
            selected_page = get_object_or_404(ContestPage, id=page_id)
            # return redirect('contest_detail_admin', contest_id=contest.id)
    else:
        pass

    context = {
        'contest': contest,
        'contest_pages': contest_pages,
        'selected_page': selected_page,
    }
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