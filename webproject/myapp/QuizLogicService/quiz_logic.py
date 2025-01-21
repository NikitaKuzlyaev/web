from ..models import QuizAttempt, QuizProblem
from django.shortcuts import (
    render, redirect, get_object_or_404
)
from ..views import is_admin
from django.contrib.auth.decorators import (
    login_required, user_passes_test
)
from django.core.exceptions import ObjectDoesNotExist
from django.contrib import messages
from django.utils.timezone import now
from django.forms import modelformset_factory
from django.db.models import Max, Prefetch, Q
from django.db import models

from ..forms import (
    CustomUserCreationForm, ContestForm, ContestPageForm,
    ContestUserProfileForm, CodeEditForm, ContestTagForm, QuizProblemForm
)
from ..models import (
    User, Contest, ContestPage, BlogPage, ContestCheckerPythonCode,
    ContestCheckerAnswerFile, ContestThresholdSubmission,
    SubmissionFile, Submission, Profile, ContestTag, Quiz, QuizField, QuizFieldCell,
    QuizAttempt, QuizProblem, QuizUser
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
import json

# Имя логгера из настроек
logger = logging.getLogger('myapp')


#
#
# class AnswerProcessingService:
#     @staticmethod
#     def process_answer(request, user_answer: str, quiz_problem_id: int):
#         # Получаем задачу по ID
#         quiz_problem = QuizProblem.objects.get(id=quiz_problem_id)
#
#         # Проверяем правильность ответа
#         is_correct = user_answer.strip().lower() == quiz_problem.answer.strip().lower()
#
#         last_quiz_attempt = QuizAttempt.objects.filter(user=user, problem=problem).order_by('-attempt_number').first()
#
#         result = {
#             'status': 'ok',
#             'attempt': None,
#         }
#
#         if last_quiz_attempt:
#             if last_quiz_attempt.is_successful:
#                 pass
#             else:
#                 quiz_attempt = QuizAttempt.objects.create(
#                     user=request.user,
#                     problem=quiz_problem,
#                     attempt_number=last_quiz_attempt.attempt_number + 1,
#                     is_successful=is_correct
#                 )
#
#                 result['attempt'] = quiz_attempt
#
#         return result
#
#
# class LeaderboardProcessingService:
#     pass

def quiz_view(request):
    # Получаем только те соревнования, для которых существует связанный Quiz
    contests = (
        Contest.objects.filter(quiz__isnull=False)
        .prefetch_related('tag')  # Предзагрузка связанных тегов
        .order_by('-created_at')  # Сортировка по дате создания
    )

    if request.user.is_authenticated:
        user_profile = request.user.profile
    else:
        user_profile = None

    if request.method == 'POST':
        form = ContestForm(request.POST)
        if form.is_valid():
            new_contest = form.save()
            quiz = Quiz.objects.create(contest=new_contest)
            quiz_field = QuizField.objects.create(quiz=quiz)
            return redirect('quizzes')
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

    return render(request, 'quizzes.html', context)


def quiz_field_view(request, contest_id):
    contest = get_object_or_404(Contest, id=contest_id)

    quiz_field = get_object_or_404(QuizField, quiz__contest=contest)

    w = quiz_field.width  # Ширина
    h = quiz_field.height  # Высота
    columns = list(range(w))
    rows = list(range(h))

    # Находим все QuizFieldCell, которые принадлежат данному Contest через Quiz
    quiz_field_cells = QuizFieldCell.objects.filter(
        quizField__quiz__contest=contest
    ).select_related('quizField')  # Оптимизация запросов через select_related

    # Если ячеек нет, создаем их для всех возможных row и col
    if not quiz_field_cells.exists():
        for row in range(quiz_field.height):  # h - высота
            for col in range(quiz_field.width):  # w - ширина
                # Создаем новую ячейку
                QuizFieldCell.objects.create(quizField=quiz_field, row=row, col=col, title=f"Cell {row}-{col}")

    # Инициализируем двумерный массив для задач
    task_field = [[None for _ in range(w)] for _ in range(h)]
    quiz_field_flags = [['ok' for _ in range(w)] for _ in range(h)]

    used_hearts = []
    full_hearts = []
    potential_score = []

    logger.debug(' 2')

    # Проходим по всем QuizFieldCell и заполняем двумерный массив задачами
    for cell in quiz_field_cells:
        quiz_problem = QuizProblem.objects.filter(quizFieldCell=cell).first()

        if quiz_problem:
            if cell.row < h and cell.col < w:
                task_field[cell.row][cell.col] = quiz_problem
        else:
            # Если задачи нет, создаем новую
            quiz_problem = QuizProblem.objects.create(quizFieldCell=cell, title='problem', points=100, answer='0', content='-')
            task_field[cell.row][cell.col] = quiz_problem

        verdict = 'ok'

        last_attempt = QuizAttempt.objects.filter(user=request.user, problem=quiz_problem).order_by('-attempt_number').first()
        if last_attempt:
            if last_attempt.is_successful:
                verdict = 'solved'
            elif last_attempt.attempt_number >= 3:
                verdict = 'failed'
            else:
                verdict = 'in-progress'

        if cell.row < h and cell.col < w:
            quiz_field_flags[cell.row][cell.col] = verdict

    logger.debug(used_hearts)

    tasks_ids = []
    for row in task_field:
        task_row = []
        for task in row:
            if task:
                task_row.append(task.id)
            else:
                task_row.append(None)
        tasks_ids.append(task_row)

    # Находим все QuizProblems, для которых:
    # 1. Есть попытки этого пользователя.
    # 2. Все попытки для этого задания имеют attempt_number < 3 и is_successful=False.
    problems = QuizProblem.objects.filter(
        attempts__user=request.user  # Фильтруем задачи по пользователю через связанные попытки
    ).exclude(
        Q(attempts__attempt_number__gte=3) | Q(attempts__is_successful=True)  # Исключаем задачи с неудачными попытками или с количеством попыток >= 3
    ).distinct()  # Убираем дубли

    quiz_user = QuizUser.objects.filter(quiz=quiz_field.quiz, user=request.user).first()

    # Сначала создайте пустые списки для сердец
    hearts_data = []

    # Пример получения информации о задачах
    for prob in problems:
        last_attempt = QuizAttempt.objects.filter(user=request.user, problem=prob).order_by('-attempt_number').first()
        pt = prob.points

        if last_attempt:
            if last_attempt.attempt_number == 0:
                hearts_data.append((prob, '', '333', pt * 2))
            elif last_attempt.attempt_number == 1:
                hearts_data.append((prob, '1', '22', pt * 3 // 2))
            elif last_attempt.attempt_number == 2:
                hearts_data.append((prob, '22', '1', pt))
        else:
            hearts_data.append((prob, '', '333', pt))  # Если попыток не было, то все сердца полные

    if request.method == 'POST':
        if 'check_answer' in request.POST:
            quiz_check_answer(request, contest)

        return redirect('quiz_field', contest_id=contest.id)

    context = {
        'columns': columns,  # Диапазон для столбцов
        'rows': rows,  # Диапазон для строк
        'task_field': task_field,  # Двумерный массив с задачами
        'tasks_ids': tasks_ids,
        'problems': problems,
        'contest': contest,
        'quiz_user': quiz_user,

        'potential_score': potential_score,
        'used_hearts': used_hearts,
        'full_hearts': full_hearts,
        'quiz_field_flags': quiz_field_flags,
        'hearts_data': hearts_data,

    }

    logger.debug(quiz_field_flags)
    return render(request, 'quiz_field.html', context)


@user_passes_test(is_admin)
def edit_quiz_problem(request, quiz_problem_id):
    quiz_problem = get_object_or_404(QuizProblem, id=quiz_problem_id)

    quiz_field_cell = get_object_or_404(QuizFieldCell, quizField=quiz_problem.quizFieldCell.quizField, id=quiz_problem.quizFieldCell.id)
    quiz_field = get_object_or_404(QuizField, id=quiz_field_cell.quizField.id)
    quiz = get_object_or_404(Quiz, contest=quiz_field.quiz.contest)
    contest = get_object_or_404(Contest, quiz=quiz)

    context = {'quiz_problem_id': quiz_problem_id,
               'quiz_problem': quiz_problem,
               'contest': contest,
               }

    if request.method == 'POST':
        form = QuizProblemForm(request.POST, instance=quiz_problem)
        if form.is_valid():
            form.save()
            context['form'] = form

            # return render(request, 'edit_quiz_problem.html', context=context)
            # return redirect('quiz_field', contest_id=contest.id)
            return render(request, 'edit_quiz_problem.html', context=context)
    else:
        form = QuizProblemForm(instance=quiz_problem)
        context['form'] = form

    return render(request, 'edit_quiz_problem.html', context=context)
    # return redirect('quiz_field', contest_id=contest.id)


def quiz_buy_problem(request, quiz_problem_id):
    quiz_problem = get_object_or_404(QuizProblem, id=quiz_problem_id)

    if not quiz_problem:
        return redirect('quiz_field')

    quiz_field_cell = get_object_or_404(QuizFieldCell, quizField=quiz_problem.quizFieldCell.quizField, id=quiz_problem.quizFieldCell.id)
    quiz_field = get_object_or_404(QuizField, id=quiz_field_cell.quizField.id)
    quiz = get_object_or_404(Quiz, contest=quiz_field.quiz.contest)
    contest = get_object_or_404(Contest, quiz=quiz)

    quiz_user = QuizUser.objects.filter(quiz=quiz_field.quiz, user=request.user).first()

    if not quiz_user:
        quiz_user = QuizUser.objects.create(
            user=request.user,
            quiz=quiz
        )

    # Проверка, что хватает денег на покупку задачи
    if not quiz_user.score >= quiz_problem.points:
        return quiz_field_view(request, contest_id=contest.id)

    last_attempt = QuizAttempt.objects.filter(user=request.user, problem=quiz_problem).order_by('-attempt_number').first()
    logger.debug(last_attempt)

    if not last_attempt:
        # Создаем новую попытку
        last_attempt = QuizAttempt.objects.create(
            user=request.user,
            problem=quiz_problem,
            attempt_number=0,  # Можно рассчитать номер попытки, если нужно
            is_successful=False  # Пока неудачная попытка
        )
        logger.debug('Bought a problem')
        logger.debug(quiz_problem.points)
        quiz_user.decrease_score(quiz_problem.points)
    else:
        pass

    return quiz_field_view(request, contest_id=contest.id)


def quiz_check_answer(request, contest):
    logger.debug('quiz_check_answer')

    user_answer = request.POST.get('user_answer')  # Используем get() для безопасного доступа
    quiz_problem_id = request.POST.get('problem_id')  # Можно задать значение по умолчанию, если ключ не найден

    quiz_problem = get_object_or_404(QuizProblem, id=quiz_problem_id)

    quiz_field_cell = get_object_or_404(QuizFieldCell, quizField=quiz_problem.quizFieldCell.quizField, id=quiz_problem.quizFieldCell.id)
    quiz_field = get_object_or_404(QuizField, id=quiz_field_cell.quizField.id)
    quiz = get_object_or_404(Quiz, contest=quiz_field.quiz.contest)
    quiz_user = QuizUser.objects.filter(quiz=quiz_field.quiz, user=request.user).first()

    last_attempt = QuizAttempt.objects.filter(user=request.user, problem=quiz_problem).order_by('-attempt_number').first()
    logger.debug(last_attempt.is_successful)
    if last_attempt.is_successful:
        return redirect('quiz_field', contest_id=contest.id)

    is_correct_answer = False
    base_points = quiz_problem.points
    reward_score_table = {1: base_points * 2,
                          2: base_points // 2 * 3,
                          3: base_points}

    logger.debug(f'Correct {quiz_problem.answer}, user answer {user_answer}')

    if user_answer == quiz_problem.answer:
        is_correct_answer = True
    else:
        pass

    new_attempt = QuizAttempt.objects.create(
        user=request.user,
        problem=quiz_problem,
        attempt_number=last_attempt.attempt_number + 1,
        is_successful=is_correct_answer
    )

    if is_correct_answer:
        reward_score = reward_score_table[new_attempt.attempt_number]
        quiz_user.increase_score(reward_score)
    else:
        pass

    return redirect('quiz_field', contest_id=contest.id)

