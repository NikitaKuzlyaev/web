from django.urls import path
from django.contrib import admin
from django.urls import path, include
from .views import main, register, user_login, contests, logout_view, contests_view, contest_detail_view_admin, contest_detail_view
from django.contrib.auth import views as auth_views
from . import views

from .forms import CustomAuthenticationForm  # Импортируем кастомную форму входа

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', main, name='main'),
    path('contests/', contests_view, name='contests'),
    path('contests/admin/<int:contest_id>/', contest_detail_view_admin, name='contest_detail_admin'),
    path('contests/<int:contest_id>/', contest_detail_view, name='contest_detail'),
    path('register/', register, name='register'),
    path('login/',
         auth_views.LoginView.as_view(template_name='myapp/login.html', authentication_form=CustomAuthenticationForm),
         name='login'),
    path('logout/', logout_view, name='logout'),

    path('contest/page/<int:page_id>/edit/', views.edit_contest_page, name='edit_contest_page'),  # Новый маршрут
    path('contest/page/<int:page_id>/delete/', views.delete_contest_page, name='delete_contest_page'),  # Новый маршрут для удаления

]
