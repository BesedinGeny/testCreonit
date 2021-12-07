import uuid

from django.db import models
from django.contrib.auth.models import User, AbstractUser
from django.utils.translation import ugettext_lazy as _

from django.urls import reverse


class TypeOfTask(models.TextChoices):
    FULL = 'FULL', 'Полный ответ'
    SINGLE = 'SINGLE', 'Выбор одного'
    MANY = 'MANY', 'Выбор нескольких'


class AnswerChoice(models.Model):
    text = models.CharField(max_length=64, default='Текст задания', verbose_name='Ответ')

    def __str__(self):
        return self.text

    class Meta:
        verbose_name = _("Вариант ответа")
        verbose_name_plural = _("Варианты ответа")


class Task(models.Model):
    title = models.CharField(max_length=64, default="Заголовок вопроса", verbose_name='Заголовок вопроса')
    text = models.TextField(default="Условие задания", verbose_name='Условие')
    task_type = models.CharField('Тип задания', max_length=150, choices=TypeOfTask.choices, default=TypeOfTask.SINGLE)
    answer_choice = models.ManyToManyField(AnswerChoice, blank=True, verbose_name='Выбор ответов')
    answer = models.CharField(max_length=256, verbose_name='Правильный ответ')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = _("Задание")
        verbose_name_plural = _("Задания")


class Test(models.Model):
    title = models.CharField(max_length=64, default="Заголовок теста")
    limit = models.IntegerField(default=1, verbose_name='Максимальное количество заданий')
    tasks = models.ManyToManyField(Task, verbose_name='Задания')
    slug = models.SlugField(max_length=50, verbose_name='Ссылка', unique=True, db_index=True)  # выключить из админки и добавить в save

    class Meta:
        verbose_name = _("Тест")
        verbose_name_plural = _("Тесты")

    def get_absolute_url(self):
        return reverse('test_page', kwargs={'test_slug': self.slug})

    def __str__(self):
        return self.title

    def save(self, *args, **kw):
        if self.slug in None or self.slug == "":
            self.slug = uuid.uuid4().hex
        return super(Test, self).save(*args, **kw)


class MyUser(AbstractUser):
    sex = [
        ('Муж', 'Мужской'),
        ('Жен', 'Женский')
    ]
    gender = models.CharField(max_length=3, choices=sex, default='Муж', verbose_name='Пол')
    first_name = models.CharField(max_length=32, verbose_name="Имя")
    second_name = models.CharField(max_length=32, verbose_name="Фамилия")

    def save(self, *args, **kw):
        self.personal_id = uuid.uuid4().hex
        return super(MyUser, self).save(*args, **kw)

    def get_absolute_url(self):
        return reverse('match', kwargs={'personal_id': self.personal_id})

    class Meta:
        verbose_name = _("Пользователь")
        verbose_name_plural = _("Пользователи")


class AnswerDone(AnswerChoice):
    task_id = models.IntegerField(verbose_name='ID задания')
    test_id = models.IntegerField(verbose_name='ID теста')  # возможно лишняя свзяь, может пригодиться для обратной совместимости

    class Meta:
        verbose_name = _("Ответ на задание")
        verbose_name_plural = _("Ответы на задание")


class Answer(models.Model):
    """Модель связи пользователей и пройденных ими тестов"""
    username = models.CharField(verbose_name='имя пользователя', max_length=64, default="")
    test_id = models.IntegerField(verbose_name='ID Теста', default=0)
    answers = models.ManyToManyField(AnswerDone, verbose_name='Ответы')

    def __str__(self):
        return "user: " + str(self.username) + " - test: " + str(self.test_id)

    class Meta:
        verbose_name = _("Ответ дан")
        verbose_name_plural = _("Ответы даны")
