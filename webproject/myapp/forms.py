from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

# your_app/forms.py
from django import forms
from .models import Contest
from .models import Task


from django.contrib.auth.forms import AuthenticationForm

class ContestForm(forms.ModelForm):
    class Meta:
        model = Contest
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Название соревнования'}),
        }
        labels = {
            'name': 'Название',
        }

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['name', 'condition', 'correct_answer']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите название задачи'}),
            'condition': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Введите условие задачи'}),
            'correct_answer': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите верный ответ'}),
        }


class CustomUserCreationForm(UserCreationForm):
    username = forms.CharField(
        max_length=10,
        min_length=1,
        required=True,
        help_text='',
        error_messages={
            'required': 'Пожалуйста, введите имя пользователя.',
            'max_length': 'Имя пользователя не должно превышать 10 символов.',
            'min_length': 'Имя пользователя должно содержать как минимум 1 символ.'
        }
    )
    password1 = forms.CharField(
        label="Пароль",
        strip=False,
        widget=forms.PasswordInput,
        min_length=1,
        max_length=10,
        error_messages={
            'required': 'Пожалуйста, введите пароль.',
            'min_length': 'Пароль должен содержать как минимум 1 символ.',
            'max_length': 'Пароль не должен превышать 10 символов.'
        }
    )
    password2 = forms.CharField(
        label="Подтверждение пароля",
        widget=forms.PasswordInput,
        strip=False,
        min_length=1,
        max_length=10,
        error_messages={
            'required': 'Пожалуйста, подтвердите пароль.',
            'min_length': 'Пароль должен содержать как минимум 1 символ.',
            'max_length': 'Пароль не должен превышать 10 символов.'
        }
    )

    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Пароли не совпадают.")
        return password2


class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        max_length=10,
        min_length=1,
        required=True,
        error_messages={
            'required': 'Пожалуйста, введите имя пользователя.',
            'max_length': 'Имя пользователя не должно превышать 10 символов.',
            'min_length': 'Имя пользователя должно содержать как минимум 1 символ.'
        }
    )
    password = forms.CharField(
        label="Пароль",
        strip=False,
        widget=forms.PasswordInput,
        min_length=1,
        max_length=10,
        error_messages={
            'required': 'Пожалуйста, введите пароль.',
            'min_length': 'Пароль должен содержать как минимум 1 символ.',
            'max_length': 'Пароль не должен превышать 10 символов.'
        }
    )
