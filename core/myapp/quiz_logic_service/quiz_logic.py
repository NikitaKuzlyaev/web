import logging
from datetime import timedelta

import pytz
import pandas as pd
import numpy as np
from sklearn.metrics import mean_squared_error

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse

from ..models import (
    User, Contest, Quiz, QuizUser, QuizField, QuizFieldCell, QuizProblem, QuizAttempt, Profile, ContestTag
)
from ..forms import (
    ContestForm, QuizProblemForm, ContestUserProfileForm, SinglePasswordChangeForm
)
from ..policies import Policies
from .. import utils
from ..utils import user_has_access_to_quizfield
from .message_box import MessageText

logger = logging.getLogger('myapp')


def clear_messages(request):
    """
    Очистка сообщений путем простого перебора.
    """
    list(messages.get_messages(request))


@csrf_exempt
@Policies.contest_status_access_politic(redirect_path='/quizzes/')
def api_get_quiz_last_attempts(request):
    """
        API endpoint, возвращающий последние попытки решения задач по заданному contest_id.
    """
    contest_id = request.GET.get("contest_id")
    if not contest_id:
        return JsonResponse({"error": "contest_id is required"}, status=400)

    quiz_attempts = QuizAttempt.objects.filter(
        problem__quizFieldCell__quizField__quiz__contest_id=contest_id
    ).exclude(user__is_staff=True).order_by("-created_at")

    timezone_utc7 = pytz.timezone('Asia/Bangkok')
    attempts_data = [
        {
            "user": attempt.user.profile.name,
            "attempt_number": attempt.attempt_number,
            "is_successful": attempt.is_successful,
            "problem_title": attempt.problem.title,
            "problem_points": attempt.problem.points,
            "created_at": attempt.created_at.astimezone(timezone_utc7).strftime("%H:%M:%S %d-%m-%Y"),
            "is_recent": attempt.created_at >= timezone.now() - timedelta(seconds=10),
            "is_recent_2": attempt.created_at >= timezone.now() - timedelta(seconds=30)
        } for attempt in quiz_attempts]

    return JsonResponse(attempts_data, safe=False)


@Policies.contest_status_access_politic(redirect_path='/quizzes/')
def quiz_realtime_log(request, contest_id):
    """
        Отображает страницу с realtime логом для конкурса.
    """
    contest = get_object_or_404(Contest, pk=contest_id)
    return render(request, 'quiz_templates/quiz_realtime_log.html', {'contest': contest})


@csrf_exempt
@user_passes_test(lambda u: u.is_staff)
def api_get_quiz_current_results(request):
    """
        API endpoint для получения текущих результатов конкурса.
    """
    contest_id = request.GET.get("contest_id")
    if not contest_id:
        return JsonResponse({"error": "contest_id is required"}, status=400)

    contest = get_object_or_404(Contest, pk=contest_id)
    quiz_users = QuizUser.objects.filter(quiz__contest=contest).select_related('user', 'user__profile')

    # Составляем список пользователей и их очков, исключая администраторов
    user_and_score = [
        (qu.user.profile.name, qu.score)
        for qu in quiz_users if not qu.user.is_staff
    ]
    user_and_score.sort(key=lambda x: -x[1])
    data = [{"user": name, "score": score} for name, score in user_and_score]

    logger.debug(data)
    return JsonResponse(data, safe=False)


@user_passes_test(lambda u: u.is_staff)
def quiz_realtime_results(request, contest_id):
    """
        Отображает страницу с realtime результатами конкурса.
    """
    contest = get_object_or_404(Contest, pk=contest_id)
    return render(request, 'quiz_templates/quiz_realtime_results.html', {'contest': contest})


def quiz_view(request):
    """
        Отображает список конкурсов, для которых существует связанный Quiz.
    """
    clear_messages(request)
    contests = Contest.objects.filter(quiz__isnull=False).prefetch_related('tag').order_by('-created_at')
    user_profile = request.user.profile if request.user.is_authenticated else None

    if request.method == 'POST':
        form = ContestForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('quizzes')
    else:
        form = ContestForm()

    contests_with_tags = [{
        'contest': contest,
        'tags': contest.tag.all()
    } for contest in contests]

    context = {
        'contests_with_tags': contests_with_tags,
        'form': form,
        'user_profile': user_profile,
    }
    return render(request, 'quiz_templates/quizzes.html', context)


@Policies.contest_user_access_politic(redirect_path='/quizzes/')
@Policies.contest_time_access_politic(redirect_path='/quizzes/')
def quiz_field_view(request, contest_id):
    """
        Отображает игровое поле конкурса (quiz field) с задачами, статусами попыток и возможностью покупки.
    """
    clear_messages(request)
    contest = get_object_or_404(Contest, pk=contest_id)
    quiz_field = get_object_or_404(QuizField, quiz__contest=contest)
    quiz = get_object_or_404(Quiz, contest=contest)
    quiz_user, _ = QuizUser.objects.get_or_create(quiz=quiz, user=request.user)

    if request.method == 'POST':
        if 'check_answer' in request.POST:
            quiz_check_answer(request, contest)

        return redirect('quiz_field', contest_id=contest.id)

    width, height = quiz_field.width, quiz_field.height
    quiz_field_cells = QuizFieldCell.objects.filter(quizField=quiz_field).select_related('quizField')

    if not quiz_field_cells.exists():
        # Если ячейки еще не созданы – создаем их пакетно
        cells = [
            QuizFieldCell(
                quizField=quiz_field,
                row=row,
                col=col,
                title=f"Cell {row}-{col}",
                cell_type='normal'
            )
            for row in range(height) for col in range(width)
        ]
        QuizFieldCell.objects.bulk_create(cells)
        quiz_field_cells = QuizFieldCell.objects.filter(quizField=quiz_field)

    # Инициализация сетки задач, флагов и возможности покупки
    task_field = [[None for _ in range(width)] for _ in range(height)]
    quiz_field_flags = [['ok' for _ in range(width)] for _ in range(height)]
    can_buy_flags = [[True for _ in range(width)] for _ in range(height)]
    hearts_data = []
    potential_score = []
    problems_to_show = []

    for cell in quiz_field_cells:
        quiz_problem = QuizProblem.objects.filter(quizFieldCell=cell).first()

        if not quiz_problem:
            quiz_problem = QuizProblem.objects.create(quizFieldCell=cell, title='problem', points=100, answer='0', content='-')
            task_field[cell.row][cell.col] = quiz_problem

        if cell.row < height and cell.col < width:
            task_field[cell.row][cell.col] = quiz_problem

    for row in range(height):
        for col in range(width):
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

            can_buy = can_buy and quiz_user.score >= quiz_problem.points or request.user.is_staff

            quiz_field_flags[row][col] = verdict
            can_buy_flags[row][col] = can_buy

    tasks_ids = [[None if not task_field[j][i] else task_field[j][i].id for i in range(width)] for j in range(height)]

    user_profile = Profile.objects.filter(user=request.user).first()

    make_redirect = not request.user.is_staff

    context = {
        'user_profile': user_profile.name,
        'columns': list(range(width)),  # Диапазон для столбцов
        'rows': list(range(height)),  # Диапазон для строк
        'task_field': task_field,  # Двумерный массив с задачами
        'tasks_ids': tasks_ids,
        'problems': problems_to_show,
        'contest': contest,
        'make_redirect': make_redirect,
        'quiz_user': quiz_user,
        'potential_score': potential_score,
        'quiz_field_flags': quiz_field_flags,
        'hearts_data': hearts_data,
        'number_of_current_user_problems': number_of_current_user_problems(quiz=quiz, user=request.user),
        'can_buy_flags': can_buy_flags,
    }
    logger.debug(quiz_field_flags)
    return render(request, 'quiz_templates/quiz_field.html', context)


@user_passes_test(lambda u: u.is_staff)
def edit_quiz_problem(request, quiz_problem_id):
    """
        Отображает форму редактирования задачи.
    """
    quiz_problem = get_object_or_404(QuizProblem, pk=quiz_problem_id)
    quiz_field_cell = get_object_or_404(QuizFieldCell, pk=quiz_problem.quizFieldCell.pk)
    quiz_field = quiz_field_cell.quizField
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
            return render(request, 'quiz_templates/edit_quiz_problem.html', context=context)
    else:
        form = QuizProblemForm(instance=quiz_problem)
    context['form'] = form
    return render(request, 'quiz_templates/edit_quiz_problem.html', context=context)


@Policies.contest_user_access_politic(redirect_path='/quizzes/')
@Policies.contest_time_access_politic(redirect_path='/quizzes/')
def quiz_buy_problem(request, quiz_problem_id):
    """
        Обрабатывает покупку задачи пользователем.
    """
    clear_messages(request)

    quiz_problem = get_object_or_404(QuizProblem, pk=quiz_problem_id)
    quiz_field_cell = get_object_or_404(QuizFieldCell, pk=quiz_problem.quizFieldCell.pk)
    quiz_field = quiz_field_cell.quizField
    quiz = get_object_or_404(Quiz, contest=quiz_field.quiz.contest)
    contest = get_object_or_404(Contest, quiz=quiz)

    if not utils.user_has_access_to_quizfield(request.user, contest.id):
        return redirect('quizzes')

    quiz_user, _ = QuizUser.objects.get_or_create(quiz=quiz, user=request.user)

    if number_of_current_user_problems(quiz=quiz, user=request.user) >= 3:
        return quiz_field_view(request, contest_id=contest.id)
    if quiz_user.score < quiz_problem.points:
        return quiz_field_view(request, contest_id=contest.id)

    last_attempt = QuizAttempt.objects.filter(user=request.user, problem=quiz_problem).order_by('-attempt_number').first()

    if not last_attempt:
        last_attempt = QuizAttempt.objects.create(
            user=request.user,
            problem=quiz_problem,
            attempt_number=0,
            is_successful=False
        )
        logger.debug('Bought a problem')
        quiz_user.decrease_score(quiz_problem.points)
        last_attempt.save()

    messages.add_message(request, messages.INFO, MessageText.problem_add(quiz_problem.title, quiz_problem.points), extra_tags='info')
    messages.add_message(request, messages.INFO, MessageText.points_decrease(quiz_problem.points), extra_tags='info')
    return quiz_field_view(request, contest_id=contest.id)


@Policies.contest_user_access_politic(redirect_path='/quizzes/')
@Policies.contest_time_access_politic(redirect_path='/quizzes/')
def quiz_check_answer(request, contest):
    """
       Обрабатывает отправку ответа пользователя.
    """
    if not utils.user_has_access_to_quizfield(request.user, contest.id):
        return redirect('quizzes')

    clear_messages(request)
    logger.debug('quiz_check_answer')
    user_answer = request.POST.get('user_answer', '').strip()
    if not user_answer or len(user_answer) == 0:
        messages.error(request, "Поле ответа не может быть пустым!")
        return redirect('quiz_field', contest_id=contest.id)

    quiz_problem_id = request.POST.get('problem_id')
    quiz_problem = get_object_or_404(QuizProblem, pk=quiz_problem_id)
    quiz_field_cell = get_object_or_404(QuizFieldCell, pk=quiz_problem.quizFieldCell.pk)
    quiz_field = quiz_field_cell.quizField
    quiz_user = QuizUser.objects.filter(quiz=quiz_field.quiz, user=request.user).first()

    last_attempt = QuizAttempt.objects.filter(user=request.user, problem=quiz_problem).order_by('-attempt_number').first()
    if last_attempt.is_successful:
        return redirect('quiz_field', contest_id=contest.id)

    if user_answer in get_unique_user_answers(quiz_user, quiz_problem):
        messages.add_message(request, messages.WARNING, MessageText.repeat_answer(), extra_tags='warning')
        return redirect('quiz_field', contest_id=contest.id)

    is_correct_answer = (user_answer == quiz_problem.answer)
    new_attempt = QuizAttempt.objects.create(
        user=request.user,
        problem=quiz_problem,
        attempt_number=last_attempt.attempt_number + 1,
        answer=user_answer,
        is_successful=is_correct_answer
    )

    if is_correct_answer:
        base_points = quiz_problem.points
        reward_score_table = {
            1: base_points * 2,
            2: base_points * 3 // 2,
            3: base_points,
        }
        reward_score = reward_score_table.get(new_attempt.attempt_number, base_points)
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
        if new_attempt.attempt_number >= 3:
            quiz_user.remove_combo_score()
            messages.add_message(request, messages.INFO, MessageText.combo_points_remove(), extra_tags='info')
            messages.add_message(request, messages.INFO, MessageText.problem_remove(quiz_problem.title, quiz_problem.points), extra_tags='info')
            messages.error(request, MessageText.wrong_answer_last_try())
        else:
            messages.error(request, MessageText.wrong_answer())

    return redirect('quiz_field', contest_id=contest.id)


@Policies.contest_results_access_politic(redirect_path='/quizzes/')
def quiz_results(request, contest_id):
    """
        Отображает результаты конкурса с подсчетом очков и определением призовых мест.
    """
    clear_messages(request)

    contest = get_object_or_404(Contest, pk=contest_id)
    quiz_users = QuizUser.objects.filter(quiz__contest=contest).select_related('user', 'user__profile')
    user_and_score = [(qu.user.profile.name, qu.score) for qu in quiz_users if not qu.user.is_staff]
    user_and_score.sort(key=lambda x: x[1])

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
        'users': quiz_users,
        'user_and_score': user_and_score,
        'gold_place_name': gold_place_name,
        'gold_place_score': gold_place_score,
        'silver_place_name': silver_place_name,
        'silver_place_score': silver_place_score,
        'bronze_place_name': bronze_place_name,
        'bronze_place_score': bronze_place_score,
    }
    return render(request, 'quiz_templates/quiz_results.html', context)


@user_passes_test(lambda u: u.is_staff)
def quiz_participants_admin(request, contest_id):
    contest = get_object_or_404(Contest, id=contest_id)
    profiles = Profile.objects.filter(contest_access=contest)

    participants = []
    for profile in profiles:
        user = profile.user
        quiz_user = QuizUser.objects.filter(user=user, quiz__contest=contest).first()

        if not quiz_user:
            quiz = Quiz.objects.filter(contest=contest).first()
            if quiz:
                quiz_user = QuizUser.objects.create(user=user, quiz=quiz)

        participants.append({
            "user": user,
            "profile": profile,
            "quiz_user": quiz_user,
        })

    # logger.debug(participants)

    if request.method == 'POST':
        participant_id = request.POST.get('participant_id')

        if participant_id:
            participant = get_object_or_404(Profile, id=participant_id)
            user = participant.user  # Теперь получаем напрямую

            if 'delete_participant' in request.POST:
                logger.debug('delete_participant')
                user.delete()  # Удаляем пользователя, связанный с Profile

            elif 'show_attempts' in request.POST:
                logger.debug('show_attempts')
                # return redirect('show_attempts', user_id=user.id)

            elif 'edit_info' in request.POST:
                logger.debug('edit_info')
                # return redirect('edit_user_info', user_id=user.id)

            return redirect('quiz_participants_admin', contest_id=contest.id)

        form = ContestUserProfileForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('quiz_participants_admin', contest_id=contest.id)

    else:
        form = ContestUserProfileForm(initial={'contest_access': contest})

    context = {
        'contest': contest,
        'participants': participants,
        'form': form,
    }

    return render(request, 'quiz_templates/quiz_participants_admin.html', context)


@user_passes_test(lambda u: u.is_staff)
def quiz_edit_user_profile(request, quiz_user_id):
    profile = get_object_or_404(Profile, id=quiz_user_id)
    user = profile.user
    quiz_user = QuizUser.objects.filter(user=user).first()

    if request.method == 'POST':
        new_name = request.POST.get('name')
        new_score = request.POST.get('score')
        new_combo_score = request.POST.get('combo_score')

        if new_name:
            profile.name = new_name
            profile.save()

        if quiz_user:
            if new_score and new_score.isdigit():
                quiz_user.score = int(new_score)
            if new_combo_score and new_combo_score.isdigit():
                quiz_user.combo_score = int(new_combo_score)
            quiz_user.save()

        # Обработка изменения пароля
        password_form = SinglePasswordChangeForm(request.POST)
        if password_form.is_valid():
            password_form.save(user)
            return redirect('quiz_participants_admin', contest_id=profile.contest_access.id)

        return redirect('quiz_participants_admin', contest_id=profile.contest_access.id)

    # Создание пустой формы для пароля
    password_form = SinglePasswordChangeForm()

    context = {
        'profile': profile,
        'quiz_user': quiz_user,
        'password_form': password_form,
    }

    return render(request, 'quiz_templates/quiz_edit_userprofile.html', context)


@user_passes_test(lambda u: u.is_staff)
def quiz_edit_user_attempts(request, quiz_user_id):
    # Получаем объект QuizUser по переданному id
    quiz_user = QuizUser.objects.filter(id=quiz_user_id).first()
    if not quiz_user:
        messages.error(request, "QuizUser не найден.")
        return redirect('some_view')  # Замените на нужное представление

    quiz_id = quiz_user.quiz.id  # Получаем quiz_id из QuizUser

    # Фильтруем попытки по user_id, используя id связанного объекта User
    user_attempts = QuizAttempt.objects.filter(
        user_id=quiz_user.user.id,
        problem__quizFieldCell__quizField__quiz__id=quiz_id
    )

    # Удаление попытки, если был отправлен запрос
    if request.method == 'POST':
        if 'delete_attempt' in request.POST:
            attempt_id = request.POST.get('attempt_id')
            attempt = QuizAttempt.objects.filter(id=attempt_id, user_id=quiz_user.user.id).first()
            if attempt:
                attempt.delete()
                messages.success(request, "Попытка удалена успешно.")
            else:
                messages.error(request, "Попытка не найдена.")

        return redirect(reverse('quiz_edit_user_attempts', args=[quiz_user_id]))

    # Собираем попытки и связанные задачи для отображения
    attempts_with_problems = []
    for attempt in user_attempts:
        problem = QuizProblem.objects.filter(id=attempt.problem_id).first()
        attempts_with_problems.append({
            'attempt': attempt,
            'problem': problem
        })

    context = {
        'attempts_with_problems': attempts_with_problems
    }

    return render(request, 'quiz_templates/quiz_edit_user_attempts.html', context)


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


def get_unique_user_answers(quiz_user, quiz_problem):
    """
    Возвращает множество уникальных ответов пользователя для указанной задачи.
    """
    attempts = QuizAttempt.objects.filter(user=quiz_user.user, problem=quiz_problem)
    return set(attempt.answer for attempt in attempts)
