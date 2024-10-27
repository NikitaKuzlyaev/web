from django.urls import path
from django.contrib import admin
from django.urls import path, include
from .views import main, register, user_login, contests, logout_view, contests_view, contest_detail_view_admin, \
    submit_answer_view, contest_results_view, contest_detail_view, task_details, users_answers_view, topics, \
    topics_view, topic_detail_view
from django.contrib.auth import views as auth_views

from .forms import CustomAuthenticationForm  # Импортируем кастомную форму входа

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', main, name='main'),
    path('topics/', topics_view, name='topics'),
    path('topics/<int:topic_id>/', topic_detail_view, name='topic_detail'),
    path('contests/', contests_view, name='contests'),
    path('contests/admin/<int:contest_id>/', contest_detail_view_admin, name='contest_detail_admin'),
    path('contests/<int:contest_id>/', contest_detail_view, name='contest_detail'),
    path('contests/<int:contest_id>/submit_answer/', submit_answer_view, name='submit_answer'),
    path('contests/<int:contest_id>/results/', contest_results_view, name='contest_results'),
    path('tasks/<int:task_id>/details/', task_details, name='task_details'),
    path('contests/<int:contest_id>/users-answers/', users_answers_view, name='users_answers'),
    path('register/', register, name='register'),
    path('login/',
         auth_views.LoginView.as_view(template_name='myapp/login.html', authentication_form=CustomAuthenticationForm),
         name='login'),
    path('logout/', logout_view, name='logout'),

]
