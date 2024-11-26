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

from django.http import JsonResponse


def is_admin(user):
    return user.is_staff  # или user.is_superuser, если хотите ограничить только суперпользователям


def logout_view(request):
    logout(request)  # Завершение сеанса
    return redirect('main')  # Перенаправление после logout


def main(request):
    return render(request, 'main.html')


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
from .models import Contest, ContestPage
from .forms import ContestPageForm

@login_required
@user_passes_test(is_admin)
def contest_detail_view_admin(request, contest_id):
    contest = get_object_or_404(Contest, id=contest_id)
    contest_pages = contest.pages.all()

    selected_page = None  # Для передачи выбранной вкладки в форму

    if request.method == 'POST':
        if 'delete_contest' in request.POST:
            # contest_id = request.POST.get('contest_id')
            # contest = get_object_or_404(contest, id=contest_id)
            contest.delete()
            # messages.success(request, 'Задача успешно удалена.')
            return redirect('contests')

        # Обработка добавления вкладки
        elif 'add_page' in request.POST:
            ContestPage.objects.create(title='empty', content='empty', contest=contest)
            messages.success(request, 'Новая вкладка добавлена.')
            return redirect('contest_detail_admin', contest_id=contest.id)

        elif 'edit_page' in request.POST:
            page_id = request.POST.get('edit_page')
            selected_page = get_object_or_404(ContestPage, id=page_id)
            #return redirect('contest_detail_admin', contest_id=contest.id)

        elif 'save_page' in request.POST:
            page_id = request.POST.get('page_id')
            page = get_object_or_404(ContestPage, id=page_id)

            if page != None:
                title = request.POST.get('title')
                content = request.POST.get('content')

                # Обновление данных вкладки
                page.title = title
                page.content = content
                page.save()

                messages.success(request, f'Вкладка "{title}" была успешно обновлена.')
            return redirect('contest_detail_admin', contest_id=contest.id)

        # Обработка удаления страницы
        elif 'delete_page' in request.POST:
            page_id = request.POST.get('page_id')
            page = get_object_or_404(ContestPage, id=page_id)
            page.delete()

            messages.success(request, 'Вкладка была удалена.')
            return redirect('contest_detail_admin', contest_id=contest.id)

    else:
        #form = ContestPageForm()
        pass

    # Передача в контекст выбранной страницы для редактирования
    page_id = request.GET.get('edit_page_id')
    if page_id:
        selected_page = get_object_or_404(ContestPage, id=page_id)

    context = {
        'contest': contest,
        'contest_pages': contest_pages,
        'selected_page': selected_page,
    }

    return render(request, 'contest_detail_admin.html', context)


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

def delete_contest_page(request, page_id):
    page = get_object_or_404(ContestPage, id=page_id)
    contest_id = page.contest.id
    page.delete()
    return redirect('contest_detail_admin', contest_id=contest_id)

@login_required
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


from .models import Contest

from .models import Contest
from django.contrib import messages
