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
from ..models import AppConfig
from ..forms import (
    CustomUserCreationForm, ContestForm, ContestPageForm,
    ContestUserProfileForm, CodeEditForm, ContestTagForm, QuizProblemForm, AppConfigForm
)
from ..models import (
    User, Contest, ContestPage, BlogPage, ContestCheckerPythonCode,
    ContestCheckerAnswerFile, ContestThresholdSubmission,
    SubmissionFile, Submission, Profile, ContestTag, Quiz, QuizField, QuizFieldCell,
    QuizAttempt, QuizProblem, QuizUser
)
from ..models import UploadedImage
from ..forms import FileUploadForm

from ..utils import have_access

# Внешние библиотек
import pandas as pd
import numpy as np
from sklearn.metrics import mean_squared_error
from io import StringIO
import ast
import pytz
import time
import logging
import json


def image_list(request):
    images = UploadedImage.objects.all()
    return render(request, "image_service_templates/image_list.html", {"images": images})


def upload_image(request):
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            # Создаем новый объект модели UploadedImage
            uploaded_image = UploadedImage(
                image=form.cleaned_data['image'],  # Присваиваем загруженное изображение
                user=request.user  # Присваиваем текущего пользователя
            )
            uploaded_image.save()  # Сохраняем объект в базе данных
            return redirect('image_list')  # Перенаправляем на успешную страницу
    else:
        form = FileUploadForm()  # Создаем пустую форму

    return render(request, "image_service_templates/image_upload.html", {"form": form})
