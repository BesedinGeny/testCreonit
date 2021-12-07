from rest_framework.exceptions import ValidationError
from rest_framework.serializers import ModelSerializer
from rest_framework import serializers
from django.contrib.auth import get_user_model

from django.db import models
from rest_framework.validators import UniqueValidator

from .models import Test, Task, Answer, AnswerChoice, AnswerDone


class AnswerChoiceSerializer(ModelSerializer):
    class Meta:
        model = AnswerChoice
        fields = "__all__"


class AnswerDoneSerializer(ModelSerializer):
    id = serializers.ReadOnlyField()

    class Meta:
        model = AnswerDone
        fields = ["text", "test_id", "task_id", "id"]

    def create(self, validated_data):
        test_id = validated_data['test_id']
        value = validated_data.get('text', None)
        if value is None:
            raise ValidationError({'task_id': "Answer not found"})

        task = None
        task_id = validated_data['task_id']
        try:
            task = Task.objects.get(pk=task_id)
        except models.ObjectDoesNotExist:
            raise ValidationError({'task_id': "Task not found"})

        raw_value = ""
        if task.task_type == "SINGLE":
            raw_value = value[0]
        elif task.task_type == "MANY":
            raw_value = " ".join(value)
        elif task.task_type == "FULL":
            raw_value = value[0]
        validated_data['id'] = AnswerDone.objects.order_by('-id').first().id + 1
        instance = AnswerDone.objects.create(task_id=task_id, test_id=test_id, text=raw_value)

        return instance


class TaskSerializer(ModelSerializer):
    answer_choice = AnswerChoiceSerializer(many=True)

    class Meta:
        model = Task
        fields = "__all__"


class TestSerializer(ModelSerializer):
    tasks = TaskSerializer(many=True)
    users_passed_field = serializers.SerializerMethodField('users_passed')

    class Meta:
        model = Test
        fields = "__all__"

    def users_passed(self, obj):
        answered = Answer.objects.filter(test_id=obj.id)
        usernames = []
        for answer in answered:
            usernames.append(answer.username)
        return usernames

    def create(self, validated_data):
        limit = validated_data['limit']
        title = validated_data['title']
        slug = validated_data['slug']
        tasks_id = []
        for task in validated_data['tasks']:
            tasks_id.append(Task.objects.filter(**task).first())  # не важно какой таск будет, если они одинаковые
                                                                    # лучше надо было спроектировать ForienKey в Task на Test
        instance = Test.objects.create(title=title, slug=slug, limit=limit)
        instance.tasks.add(*tasks_id)
        instance.save()
        return instance

    def update(self, instance, validated_data):
        for key, value in validated_data.items():
            if key != 'tasks':
                setattr(instance, key, value)
        instance.save()
        return instance


UserModel = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    def create(self, validated_data):
        user = UserModel.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            second_name=validated_data['second_name'],
        )

        return user

    class Meta:
        model = UserModel
        fields = ("id", "username", "password", "first_name", "second_name")


class AnswerSerializer(ModelSerializer):
    answers = AnswerDoneSerializer(many=True)

    class Meta:
        model = Answer
        fields = "__all__"

    def create(self, validated_data):
        test_id = validated_data['test_id']
        username = validated_data['username']
        answers = []  # = validated_data['answers']
        instance = Answer.objects.create(test_id=test_id, username=username)

        for answer in validated_data['answers']:
            answers.append(AnswerDone.objects.filter(**answer).last())  # не важно какой ответ, если они отличаются только id
                                                                        # согласен, лучше было сделать в AnswerDone Forien Key а Answer
        instance.answers.add(*answers)  # получаем точно хорошие answers
        instance.save()
        return instance