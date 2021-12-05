from django.contrib.auth.forms import UserCreationForm
#from django.contrib.gis import forms
from django.contrib.auth.forms import forms
from .models import MyUser

sex_choice = [
    ('Муж', 'Мужской'),
    ('Жен', 'Женский')
]


class RegistrationForm(UserCreationForm, forms.ModelForm):
    gender = forms.ChoiceField(choices=sex_choice, label='Пол')
    first_name = forms.CharField(max_length=32, label='Имя')
    second_name = forms.CharField(max_length=32, label='Фамилия')

    class Meta:
        model = MyUser
        fields = ('username', 'password1', 'password2', 'gender', 'first_name', 'second_name')


class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = MyUser
        fields = ('username', 'password')

