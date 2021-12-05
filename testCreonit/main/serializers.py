from rest_framework.serializers import ModelSerializer
from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import Test, Task, MyUser, Answer, AnswerChoice


class AnswerChoiceSerializer(ModelSerializer):
    class Meta:
        model = AnswerChoice
        fields = "__all__"


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
        answered = Answer.objects.filter(test__id=obj.id)
        usernames = []
        for answer in answered:
            usernames.append(answer.user.username)
        return usernames

    def create(self, validated_data):
        print(validated_data)
        #id = validated_data['id']
        limit = validated_data['limit']
        title = validated_data['title']
        slug = validated_data['slug']
        tasks_id = []
        for task in validated_data['tasks']:
            tasks_id.append(Task.objects.get(**task))
        print(tasks_id)
        instance = Test.objects.create(title=title, slug=slug, limit=limit)
        instance.tasks.add(*tasks_id)
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


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(
        max_length=100,
        style={'placeholder': 'Email', 'autofocus': True}
    )
    password = serializers.CharField(
        max_length=100,
        style={'input_type': 'password', 'placeholder': 'Password'}
    )
    remember_me = serializers.BooleanField()
