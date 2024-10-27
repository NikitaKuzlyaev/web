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


def is_admin(user):
    return user.is_staff  # или user.is_superuser, если хотите ограничить только суперпользователям


def logout_view(request):
    logout(request)  # Завершение сеанса
    return redirect('main')  # Перенаправление после logout


def main(request):
    return render(request, 'main.html')


def topics(request):
    return render(request, 'topics.html')


from .models import Topic, Comment
from .forms import TopicForm


def topics_view(request):
    topics = Topic.objects.all().order_by('-created_at')  # Получаем все обсуждения
    if request.method == 'POST':
        form = TopicForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('topics')  # Перенаправляем на страницу обсуждений после создания
    else:
        form = TopicForm()
    context = {
        'topics': topics,
        'form': form,
    }
    return render(request, 'topics.html', context)


def topic_detail_view(request, topic_id):
    topic = get_object_or_404(Topic, id=topic_id)
    # tasks = contest.tasks.all()

    # Получаем все правильные ответы пользователя
    # correct_answers = {answer.task.id for answer in UserAnswer.objects.filter(user=request.user, is_correct=True)}

    # if request.method == 'POST':
    #     pass
    #
    # else:
    #     form = TaskForm()

    context = {
        'topic': topic,
    }
    return render(request, 'topic_detail.html', context)


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


from django.contrib.auth.decorators import login_required
from .models import Contest
from .forms import ContestForm, Task

from django.http import JsonResponse


# Представление для получения деталей задачи по её ID
def task_details(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    data = {
        'name': task.name,
        'condition': task.condition,
    }
    return JsonResponse(data)


@login_required
def contests_view(request):
    contests = Contest.objects.all().order_by('-created_at')  # Получаем все соревнования
    if request.method == 'POST':
        form = ContestForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('contests')  # Перенаправляем на страницу соревнований после создания
    else:
        form = ContestForm()
    context = {
        'contests': contests,
        'form': form,
    }
    return render(request, 'contests.html', context)


# main/views.py
from django.shortcuts import get_object_or_404

from django.contrib.auth.decorators import user_passes_test


@login_required
@user_passes_test(is_admin)
def contest_detail_view_admin(request, contest_id):
    contest = get_object_or_404(Contest, id=contest_id)
    tasks = contest.tasks.all()

    if request.method == 'POST':
        if 'add_task' in request.POST:
            form = TaskForm(request.POST)
            if form.is_valid():
                new_task = form.save(commit=False)
                new_task.contest = contest
                new_task.save()
                messages.success(request, 'Задача успешно добавлена.')
                return redirect('contest_detail_admin', contest_id=contest.id)
        elif 'delete_task' in request.POST:
            task_id = request.POST.get('task_id')
            task = get_object_or_404(Task, id=task_id, contest=contest)
            task.delete()
            messages.success(request, 'Задача успешно удалена.')
            return redirect('contest_detail_admin', contest_id=contest.id)
        elif 'delete_contest' in request.POST:
            # contest_id = request.POST.get('contest_id')
            # contest = get_object_or_404(contest, id=contest_id)
            contest.delete()
            # messages.success(request, 'Задача успешно удалена.')
            return redirect('contests')
    else:
        form = TaskForm()

    context = {
        'contest': contest,
        'tasks': tasks,
        'form': form,
    }
    return render(request, 'contest_detail_admin.html', context)


@login_required
def contest_detail_view(request, contest_id):
    contest = get_object_or_404(Contest, id=contest_id)
    tasks = contest.tasks.all()

    # Получаем все правильные ответы пользователя
    correct_answers = {answer.task.id for answer in UserAnswer.objects.filter(user=request.user, is_correct=True)}

    if request.method == 'POST':
        pass

    else:
        form = TaskForm()

    context = {
        'contest': contest,
        'tasks': tasks,
        'form': form,
        'correct_answers': correct_answers,  # Передаем правильные ответы в контекст
    }
    return render(request, 'contest_detail.html', context)


from .models import Contest, Task, UserAnswer


def users_answers_view(request, contest_id):
    contest = Contest.objects.get(id=contest_id)
    tasks = contest.tasks.all()
    # users = User.objects.all()

    # Получаем пользователей, которые имеют хотя бы один ответ на задачи
    users = User.objects.filter(useranswer__task__in=tasks).distinct()
    # Получаем все ответы пользователей
    user_answers = UserAnswer.objects.filter(task__in=tasks).select_related('user', 'task')

    # Создаем структуру для хранения результатов
    answers_dict = {user.id: {task.id: None for task in tasks} for user in users}

    # Подсчитываем количество решенных задач для каждого пользователя
    user_solved_count = {user.id: 0 for user in users}

    for answer in user_answers:
        if answer.user.id in answers_dict:
            answers_dict[answer.user.id][answer.task.id] = answer.is_correct
            if answer.is_correct:
                user_solved_count[answer.user.id] += 1

    # Сортируем пользователей по количеству решенных задач (по убыванию)
    sorted_users = sorted(users, key=lambda user: user_solved_count[user.id], reverse=True)

    context = {
        'contest': contest,
        'users': sorted_users,
        'tasks': tasks,
        'answers_dict': answers_dict,
        'user_solved_count': user_solved_count
    }
    return render(request, 'users_answers.html', context)


from .models import Contest, Task, UserAnswer
from .forms import TaskForm
from django.contrib import messages


@login_required
def submit_answer_view(request, contest_id):
    contest = get_object_or_404(Contest, id=contest_id)
    tasks = contest.tasks.all()
    answer_result = None
    selected_task_id = None  # Для хранения выбранной задачи

    # Получаем все правильные ответы пользователя
    correct_answers = {answer.task.id for answer in UserAnswer.objects.filter(user=request.user, is_correct=True)}

    if request.method == 'POST':
        selected_task_id = request.POST.get('task_id')  # Сохраняем выбранную задачу
        user_answer = request.POST.get('user_answer', '').strip()

        task = get_object_or_404(Task, id=selected_task_id, contest=contest)
        # Проверка, существует ли уже ответ пользователя на эту задачу
        existing_answer = UserAnswer.objects.filter(user=request.user, task=task).first()

        if existing_answer is None:  # Если ответа нет, сохраняем новый ответ
            is_correct = (user_answer.lower() == task.correct_answer.lower())

            # Сохранение ответа пользователя
            UserAnswer.objects.create(
                user=request.user,
                task=task,
                user_answer=user_answer,
                is_correct=is_correct
            )

            answer_result = {
                'is_correct': is_correct,
                'task': task,
                'user_answer': user_answer,
                'correct_answer': task.correct_answer,
            }
        else:
            # Если ответ уже существует и правильный
            answer_result = {
                'is_correct': existing_answer.is_correct,
                'task': task,
                'user_answer': existing_answer.user_answer,
                'correct_answer': task.correct_answer,
                'message': "Вы уже ответили на эту задачу правильно."
            }

    context = {
        'contest': contest,
        'tasks': tasks,
        'answer_result': answer_result,
        'selected_task_id': selected_task_id,  # Добавляем выбранную задачу в контекст
        'correct_answers': correct_answers,  # Передаем правильные ответы в контекст
    }
    return render(request, 'contest_detail.html', context)


@login_required
def contest_results_view(request, contest_id):
    contest = get_object_or_404(Contest, id=contest_id)
    # Получаем все уникальные пользователей, которые решали задачи в этом соревновании
    user_answers = UserAnswer.objects.filter(task__contest=contest).select_related('user', 'task')
    # Агрегируем результаты по пользователям
    from django.db.models import Count, Q

    results = user_answers.values('user__username').annotate(
        total_attempts=Count('id'),
        correct_answers=Count('id', filter=Q(is_correct=True))
    ).order_by('-correct_answers')

    context = {
        'contest': contest,
        'results': results,
    }
    return render(request, 'contest_results.html', context)
