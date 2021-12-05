import uuid

from django.db import models
from django.contrib.auth.models import User, AbstractUser

from django.urls import reverse


class TypeOfTask(models.TextChoices):
    FULL = 'FULL', 'Полный ответ'
    SINGLE = 'SINGLE', 'Выбор одного'
    MANY = 'MANY', 'Выбор нескольких'


class AnswerChoice(models.Model):
    text = models.CharField(max_length=64, default='Текст задания')

    def __str__(self):
        return self.text


class Task(models.Model):
    title = models.CharField(max_length=64, default="Заголовок вопроса")
    text = models.TextField(default="Условие задания")
    task_type = models.CharField('Тип задания', max_length=150, choices=TypeOfTask.choices, default=TypeOfTask.SINGLE)
    answer_choice = models.ManyToManyField(AnswerChoice, blank=True)
    answer = models.CharField(max_length=256)

    def __str__(self):
        return self.title


class Test(models.Model):
    title = models.CharField(max_length=64, default="Заголовок теста")
    limit = models.IntegerField(default=1, verbose_name='n')
    tasks = models.ManyToManyField(Task)
    slug = models.SlugField(max_length=50, verbose_name='Ссылка', unique=True, db_index=True)

    def get_absolute_url(self):
        return reverse('test_page', kwargs={'test_slug': self.slug})

    @property  # not used -_-
    def users_passed(self):
        answered = Answer.objects.filter(test__id=self.pk)
        usernames = []
        for answer in answered:
            usernames.append(answer.user.username)
        return usernames


class MyUser(AbstractUser):
    sex = [
        ('Муж', 'Мужской'),
        ('Жен', 'Женский')
    ]
    gender = models.CharField(max_length=3, choices=sex, default='Муж', verbose_name='Пол')
    first_name = models.CharField(max_length=32, verbose_name="Имя")
    second_name = models.CharField(max_length=32, verbose_name="Фамилия")
    test_passed = models.ManyToManyField(Test)

    def save(self, *args, **kw):
        self.personal_id = uuid.uuid4().hex
        return super(MyUser, self).save(*args, **kw)

    def get_absolute_url(self):
        return reverse('match', kwargs={'personal_id': self.personal_id})


class AnswerDone(AnswerChoice):
    task_id = models.IntegerField()
    test_id = models.IntegerField()  # возможно лишняя свзяь, может пригодиться для обратной совместимости


class Answer(models.Model):
    user = models.ForeignKey(MyUser, on_delete=models.CASCADE)
    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    answers = models.ManyToManyField(AnswerDone)
