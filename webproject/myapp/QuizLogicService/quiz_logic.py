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
from .message_box import MessageText
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
from ..politics import Politics

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
    # Очистка сообщений. временное решение/заглушка
    storage = messages.get_messages(request)
    for _ in storage:
        pass  # Просто итерируемся, чтобы очистить их

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


@Politics.contest_time_access_politic(redirect_path='/quizzes/')
def quiz_field_view(request, contest_id):
    # Очистка сообщений. временное решение/заглушка
    storage = messages.get_messages(request)
    for _ in storage:
        pass  # Просто итерируемся, чтобы очистить их

    contest = get_object_or_404(Contest, id=contest_id)
    quiz_field = get_object_or_404(QuizField, quiz__contest=contest)
    quiz = get_object_or_404(Quiz, contest=quiz_field.quiz.contest)
    quiz_user = QuizUser.objects.filter(quiz=quiz_field.quiz, user=request.user).first()

    if not quiz_user:
        quiz_user = QuizUser.objects.create(user=request.user, quiz=quiz)

    if request.method == 'POST':
        if 'check_answer' in request.POST:
            quiz_check_answer(request, contest)
        return redirect('quiz_field', contest_id=contest.id)

    w, h = quiz_field.width, quiz_field.height  # Ширина, Высота
    quiz_field_cells = QuizFieldCell.objects.filter(quizField__quiz__contest=contest).select_related('quizField')

    # Если ячеек нет, создаем их для всех возможных row и col
    if not quiz_field_cells.exists():
        for row in range(quiz_field.height):
            for col in range(quiz_field.width):
                QuizFieldCell.objects.create(quizField=quiz_field, row=row, col=col, title=f"Cell {row}-{col}")

    # Инициализируем двумерный массив для задач
    task_field = [[None for _ in range(w)] for _ in range(h)]
    quiz_field_flags = [['ok' for _ in range(w)] for _ in range(h)]
    can_buy_flags = [[True for _ in range(w)] for _ in range(h)]
    potential_score, hearts_data, problems_to_show = [], [], []

    for cell in quiz_field_cells:
        quiz_problem = QuizProblem.objects.filter(quizFieldCell=cell).first()

        if not quiz_problem:
            quiz_problem = QuizProblem.objects.create(quizFieldCell=cell, title='problem', points=100, answer='0', content='-')
            task_field[cell.row][cell.col] = quiz_problem

        if cell.row < h and cell.col < w:
            task_field[cell.row][cell.col] = quiz_problem

    for row in range(h):
        for col in range(w):
            quiz_problem = task_field[row][col]

            verdict = 'ok'
            can_buy = number_of_current_user_problems(quiz=quiz, user=request.user) < 3
            pt = quiz_problem.points

            last_attempt = QuizAttempt.objects.filter(user=request.user, problem=quiz_problem).order_by('-attempt_number').first()
            if last_attempt:
                if last_attempt.is_successful:
                    verdict = 'solved'
                    can_buy = False
                elif last_attempt.attempt_number >= 3:
                    verdict = 'failed'
                    can_buy = False
                else:
                    verdict = 'in-progress'
                    can_buy = False
                    if last_attempt.attempt_number == 0:
                        hearts_data.append((quiz_problem, '', '333', pt * 2))
                    elif last_attempt.attempt_number == 1:
                        hearts_data.append((quiz_problem, '1', '22', pt * 3 // 2))
                    elif last_attempt.attempt_number == 2:
                        hearts_data.append((quiz_problem, '22', '1', pt))

                if quiz_problem.points > quiz_user.score:
                    can_buy = False

            can_buy = can_buy or request.user.is_staff

            quiz_field_flags[row][col] = verdict
            can_buy_flags[row][col] = can_buy

    tasks_ids = [[None if not task_field[j][i] else task_field[j][i].id for i in range(w)] for j in range(h)]

    context = {
        'columns': list(range(w)),  # Диапазон для столбцов
        'rows': list(range(h)),  # Диапазон для строк
        'task_field': task_field,  # Двумерный массив с задачами
        'tasks_ids': tasks_ids,
        'problems': problems_to_show,
        'contest': contest,
        'quiz_user': quiz_user,
        'potential_score': potential_score,
        'quiz_field_flags': quiz_field_flags,
        'hearts_data': hearts_data,
        'number_of_current_user_problems': number_of_current_user_problems(quiz=quiz, user=request.user),
        'can_buy_flags': can_buy_flags,
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
            return render(request, 'edit_quiz_problem.html', context=context)
    else:
        form = QuizProblemForm(instance=quiz_problem)
        context['form'] = form

    return render(request, 'edit_quiz_problem.html', context=context)


@Politics.contest_time_access_politic(redirect_path='/quizzes/')
def quiz_buy_problem(request, quiz_problem_id):
    # Очистка сообщений. временное решение/заглушка
    storage = messages.get_messages(request)
    for _ in storage:
        pass  # Просто итерируемся, чтобы очистить их

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

    if number_of_current_user_problems(quiz=quiz, user=request.user) >= 3:
        return quiz_field_view(request, contest_id=contest.id)

    # Проверка, что хватает денег на покупку задачи
    if not quiz_user.score >= quiz_problem.points:
        return quiz_field_view(request, contest_id=contest.id)

    last_attempt = QuizAttempt.objects.filter(user=request.user, problem=quiz_problem).order_by('-attempt_number').first()

    if not last_attempt:
        # Создаем новую попытку
        last_attempt = QuizAttempt.objects.create(
            user=request.user,
            problem=quiz_problem,
            attempt_number=0,  # Можно рассчитать номер попытки, если нужно
            is_successful=False  # Пока неудачная попытка
        )
        logger.debug('Bought a problem')
        quiz_user.decrease_score(quiz_problem.points)
        last_attempt.save()
    else:
        pass

    # messages.success(request, MessageText.points_decrease(quiz_problem.points))
    messages.add_message(request, messages.INFO, MessageText.problem_add(quiz_problem.title, quiz_problem.points), extra_tags='info')
    messages.add_message(request, messages.INFO, MessageText.points_decrease(quiz_problem.points), extra_tags='info')
    return quiz_field_view(request, contest_id=contest.id)


@Politics.contest_time_access_politic(redirect_path='/quizzes/')
def quiz_check_answer(request, contest):
    # Очистка сообщений. временное решение/заглушка
    storage = messages.get_messages(request)
    for _ in storage:
        pass  # Просто итерируемся, чтобы очистить их

    logger.debug('quiz_check_answer')
    # messages.success(request, "Ответ принят!")

    user_answer = request.POST.get('user_answer')  # Используем get() для безопасного доступа

    # Обработка на случай пустого ответа. Хотя он не должен возникать, если не изменять код страницы формы отправки
    if len(user_answer) == 0:
        messages.error(request, "Поле ответа не может быть пустым!")
        return redirect('quiz_field', contest_id=contest.id)

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

        reward_combo_score = (reward_score + 99) // 100
        messages.add_message(request, messages.INFO, MessageText.combo_points_increase(reward_combo_score), extra_tags='info')

        messages.add_message(request, messages.INFO, MessageText.points_increase(reward_score), extra_tags='info')
        if quiz_user.combo_score > 0:
            messages.add_message(request, messages.INFO, MessageText.points_increase_with_combo_points(quiz_user.combo_score), extra_tags='info')
            quiz_user.increase_score_by_combo(quiz_user.combo_score)

        quiz_user.increase_combo_score(reward_combo_score)
        messages.success(request, MessageText.correct_answer())
    else:
        is_problem_lose = False
        if new_attempt.attempt_number >= 3:
            is_problem_lose = True

        if is_problem_lose:
            quiz_user.remove_combo_score()
            messages.add_message(request, messages.INFO, MessageText.combo_points_remove(), extra_tags='info')
            messages.add_message(request, messages.INFO, MessageText.problem_remove(quiz_problem.title, quiz_problem.points), extra_tags='info')
            messages.error(request, MessageText.wrong_answer_last_try())
        else:
            reward_score = reward_score_table[new_attempt.attempt_number]
            messages.error(request, MessageText.wrong_answer())

    return redirect('quiz_field', contest_id=contest.id)


@Politics.contest_results_access_politic(redirect_path='/quizzes/')
def quiz_results(request, contest_id):
    # Очистка сообщений. временное решение/заглушка
    storage = messages.get_messages(request)
    for _ in storage:
        pass  # Просто итерируемся, чтобы очистить их

    contest = get_object_or_404(Contest, id=contest_id)

    # Получаем всех пользователей, у которых quiz привязан к данному contest
    users = QuizUser.objects.filter(quiz__contest=contest).select_related('user', 'user__profile')

    user_and_score = []
    for quiz_user in users:
        user = quiz_user.user

        if user.is_staff and not request.user.is_staff:
            continue

        profile = user.profile
        user_and_score.append((profile.name, quiz_user.score))

    user_and_score.sort(key=lambda x: (x[1]))
    gold_place_name = None
    gold_place_score = None

    silver_place_name = None
    silver_place_score = None

    bronze_place_name = None
    bronze_place_score = None

    # 200 iq moment
    if len(user_and_score) > 0:
        gold_place_name, gold_place_score = user_and_score.pop()
    if len(user_and_score) > 0:
        silver_place_name, silver_place_score = user_and_score.pop()
    if len(user_and_score) > 0:
        bronze_place_name, bronze_place_score = user_and_score.pop()

    user_and_score = user_and_score[::-1]

    context = {
        'contest': contest,
        'users': users,
        'user_and_score': user_and_score,

        'gold_place_name': gold_place_name,
        'gold_place_score': gold_place_score,

        'silver_place_name': silver_place_name,
        'silver_place_score': silver_place_score,

        'bronze_place_name': bronze_place_name,
        'bronze_place_score': bronze_place_score,
    }

    return render(request, 'quiz_results.html', context)


@user_passes_test(is_admin)
def quiz_participants_admin(request, contest_id):
    contest = get_object_or_404(Contest, id=contest_id)
    participants = Profile.objects.filter(contest_access=contest)

    if request.method == 'POST':
        if 'delete_participant' in request.POST:
            participant_id = request.POST.get('participant_id')
            if participant_id:
                participant = get_object_or_404(Profile, id=participant_id)
                user = User.objects.filter(profile=participant)
                user.delete()  # Удаляем участника
                return redirect('quiz_participants_admin', contest_id=contest.id)  # Перенаправляем на страницу с участниками

        form = ContestUserProfileForm(request.POST)
        if form.is_valid():
            form.save()  # Сохраняем нового пользователя и его профиль
            return redirect('quiz_participants_admin', contest_id=contest.id)  # Перенаправляем обратно на страницу с участниками
    else:
        form = ContestUserProfileForm(initial={'contest_access': contest})  # Передаем текущий contest в форму

    context = {
        'contest': contest,
        'participants': participants,
        'form': form,
    }

    return render(request, 'quiz_participants_admin.html', context)


def number_of_current_user_problems(quiz: Quiz, user: User):
    quiz_field = get_object_or_404(QuizField, quiz=quiz)
    quiz_field_cells = QuizFieldCell.objects.filter(quizField=quiz_field)

    result = 0

    for cell in quiz_field_cells:
        quiz_problem = QuizProblem.objects.filter(quizFieldCell=cell).first()

        if not quiz_problem:
            continue
        if not (cell.row < quiz_field.height and cell.col < quiz_field.width):
            continue

        last_attempt = QuizAttempt.objects.filter(user=user, problem=quiz_problem).order_by('-attempt_number').first()
        if last_attempt:
            if last_attempt.is_successful:
                pass
            elif last_attempt.attempt_number >= 3:
                pass
            else:
                result += 1

    return result
