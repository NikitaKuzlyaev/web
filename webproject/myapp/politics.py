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
#from .forms import ImageUploadForm
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

# Имя логгера из настроек
logger = logging.getLogger('myapp')

# Получение текущего времени в UTC+7
timezone_utc7 = pytz.timezone('Asia/Bangkok')  # UTC+7


class Politics:

    @staticmethod
    def is_admin(user):
        return user.is_staff  # или user.is_superuser, если хотите ограничить только суперпользователя

    @staticmethod
    def contest_user_access_politic(redirect_path):
        """
        Кастомный декоратор, проверяющий, имеет ли пользователь доступ к контесту.
        """

        def decorator(view_func):

            def _wrapped_view(request, *args, **kwargs):
                contest_id = kwargs.get('contest_id')
                if contest_id:
                    user = request.user
                    if not have_access(user, contest_id=contest_id):
                        # return redirect('/contests/')  # Если доступа нет, редиректим на страницу с соревнованиями
                        return redirect(redirect_path)  # Если доступа нет, редиректим на страницу с соревнованиями
                return view_func(request, *args, **kwargs)

            return user_passes_test(lambda u: u.is_authenticated)(_wrapped_view)

        return decorator

    @staticmethod
    def contest_time_access_politic(redirect_path):
        """
        Проверка по времени доступа к контесту.
        Пользователь проходит по политике, когда он или администратор, или соревнование идет сейчас
        """

        def decorator(view_func):
            def _wrapped_view(request, *args, **kwargs):
                contest_id = kwargs.get('contest_id')
                if contest_id:
                    contest = Contest.objects.filter(id=contest_id).first()
                    if not contest:
                        # return redirect('/contests/')
                        return redirect(redirect_path)

                    user = request.user
                    if user.is_staff:
                        return view_func(request, *args, **kwargs)

                    current_time_utc7 = now().astimezone(timezone_utc7)
                    time_start = contest.time_start.astimezone(timezone_utc7)
                    time_end = contest.time_end.astimezone(timezone_utc7)

                    logger.debug(f"Current time: {current_time_utc7}, Start: {time_start}, End: {time_end}")
                    if current_time_utc7 < time_start or current_time_utc7 > time_end:
                        logger.debug(f"Access denied: Current time {current_time_utc7} is outside [{time_start}, {time_end}]")
                        # return redirect('/contests/')
                        return redirect(redirect_path)

                return view_func(request, *args, **kwargs)

            return user_passes_test(lambda u: u.is_authenticated)(_wrapped_view)

        return decorator

    @staticmethod
    def contest_preview_time_access_politic(redirect_path):
        """
        Проверка по времени доступа к превью контеста.
        """

        def decorator(view_func):
            def _wrapped_view(request, *args, **kwargs):
                contest_id = kwargs.get('contest_id')
                if contest_id:
                    contest = Contest.objects.filter(id=contest_id).first()
                    if not contest:
                        # return redirect('/contests/')
                        return redirect(redirect_path)

                    user = request.user
                    if user.is_staff:
                        return view_func(request, *args, **kwargs)

                    current_time_utc7 = now().astimezone(timezone_utc7)
                    time_start = contest.time_start.astimezone(timezone_utc7)
                    time_end = contest.time_end.astimezone(timezone_utc7)

                    logger.debug(f"Current time: {current_time_utc7}, Start: {time_start}, End: {time_end}")
                    if contest.is_open_preview:
                        # Ok. Доступ на просмотр разрешен
                        return view_func(request, *args, **kwargs)

                    if current_time_utc7 < time_start or current_time_utc7 > time_end:
                        logger.debug(f"Access denied: Current time {current_time_utc7} is outside [{time_start}, {time_end}]")
                        # return redirect('/contests/')
                        return redirect(redirect_path)

                return view_func(request, *args, **kwargs)

            return user_passes_test(lambda u: u.is_authenticated)(_wrapped_view)

        return decorator

    @staticmethod
    def contest_results_access_politic(redirect_path):
        """
        Проверка по времени доступа к результатам контеста.
        """

        def decorator(view_func):
            def _wrapped_view(request, *args, **kwargs):
                contest_id = kwargs.get('contest_id')
                if contest_id:
                    contest = Contest.objects.filter(id=contest_id).first()
                    if not contest:
                        return redirect(redirect_path)

                    user = request.user
                    if user.is_staff or contest.is_open_results:
                        return view_func(request, *args, **kwargs)

                    return redirect(redirect_path)

                return view_func(request, *args, **kwargs)

            return user_passes_test(lambda u: u.is_authenticated)(_wrapped_view)

        return decorator
