from django.contrib import admin
from django import forms
from django.core.exceptions import ValidationError

from .models import MyUser, Test, Task, Answer, AnswerChoice, AnswerDone


# Register your models here.


class TestForm(forms.ModelForm):
    class Meta:
        model = Test
        exclude = ['slug']

    def clean(self):  # валидация кол-ва заданий в тесте
        tasks = self.cleaned_data.get("tasks")
        limit = self.cleaned_data.get('limit')
        if tasks.count() > limit:  # поле лимита заданий в тесте.
            raise ValidationError("To many tasks!")
        return self.cleaned_data


class TestAdmin(admin.ModelAdmin):
    form = TestForm


admin.site.register(MyUser)
admin.site.register(AnswerChoice)
admin.site.register(AnswerDone)
admin.site.register(Task)
admin.site.register(Answer)
admin.site.register(Test, TestAdmin)
