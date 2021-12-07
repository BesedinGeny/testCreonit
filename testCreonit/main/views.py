import json

from django.contrib.auth import authenticate, login, get_user_model
from django.contrib.auth.hashers import check_password
from django.shortcuts import render
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, status, generics, filters, renderers
from rest_framework.authentication import SessionAuthentication, BasicAuthentication, TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated, BasePermission, OperandHolder
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from .filters import TestFilter
from .models import Test, Answer, AnswerDone, Task, MyUser
from .serializers import TestSerializer, UserSerializer, AnswerDoneSerializer, AnswerSerializer


def method_permission_classes(classes):
    def decorator(func):
        def decorated_func(self, *args, **kwargs):
            self.permission_classes = classes
            for cls in classes:
                if not issubclass(cls.__class__, OperandHolder):
                    # Если у нас странный пермишен, то установим только для админа
                    self.permission_classes = [IsAdminUser]
                    break
            self.check_permissions(self.request)
            return func(self, *args, **kwargs)

        return decorated_func

    return decorator


def index(request):
    return render(request, 'main/index.html')


class TestsView(generics.ListAPIView):
    queryset = Test.objects.all()
    serializer_class = TestSerializer
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = TestFilter


class TestView(APIView):
    """
        Обработка теста
        для админа: возможность получить/добавить/изменить/удалить тест
        для пользователя: возможность пройти тест/просмотреть результаты пройденного теста
    """
    authentication_classes = [TokenAuthentication, ]

    @method_permission_classes((permissions.IsAdminUser | permissions.IsAuthenticated,))
    def get(self, request, test_slug):
        test = Test.objects.get(slug=test_slug)
        button_disabled = False
        previous_results = None
        passed_before = Answer.objects.filter(
            test_pk=test.pk,
            username=request.user.username
        ).first()  # только 1 объект
        if passed_before is not None:
            button_disabled = True
            previous_results = passed_before

        serializer = TestSerializer(test)
        if not request.user.is_staff:
            self.renderer_classes = [TemplateHTMLRenderer]
            return Response({
                'test': test,
                'disabled': button_disabled,
                'result': previous_results
            }, template_name='main/single_test.html')
        return Response(serializer.data)

    @method_permission_classes((permissions.IsAdminUser | permissions.IsAuthenticated,))
    def post(self, request, test_slug):
        json_data = {}
        if request.accepted_renderer.format == 'json':  # приведение к единому типу запроса с формы и с внешнего запроса
            json_data = json.loads(request.body.decode('utf-8'))["data"]
        else:
            json_data = dict(request.POST)
        if request.accepted_renderer.format == 'json' or (
                request.method == 'POST' and request.POST.get("btn_submit", "") == 'Закончить тест'):
            answered = []  # список ответов пользователя
            test_id = json_data['test_id'][0]
            tasks_id = json_data['task_id']  # miss naming :(
            username = request.user.username

            passed_before = Answer.objects.filter(
                test_pk=test_id,
                username=request.user.username
            ).first()
            if passed_before is not None:
                return Response({"detail": "Тест уже пройден этим пользователем"})

            for task_id in tasks_id:
                serializer = AnswerDoneSerializer(data={
                    'test_id': test_id,
                    'task_id': task_id,
                    'text': " ".join(json_data.get(task_id, None))
                })
                if serializer.is_valid(raise_exception=True):
                    serializer.save()
                    answered.append(serializer.data)
            serializer = AnswerSerializer(data={
                'test_id': test_id,
                'username': username,
                'answers': answered
            })
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        elif request.user.is_staff:  # POST от админа на создание теста
            serializer = TestSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:  # Странный случай, не админ и не форма
            serializer = TestSerializer(data=request.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @method_permission_classes((permissions.IsAdminUser,))
    def put(self, request, test_slug):
        test = Test.objects.get(slug=test_slug)
        serializer = TestSerializer(test, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @method_permission_classes((permissions.IsAdminUser,))
    def delete(self, request, test_slug):
        test = Test.objects.get(slug=test_slug)
        test.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["POST"])
@permission_classes([AllowAny])
def login_user(request):  #
    data = {}
    reqBody = json.loads(request.body)
    username = reqBody['username']
    password = reqBody['password']
    try:
        Account = MyUser.objects.get(username=username)
    except BaseException as e:
        raise ValidationError({"400": f'{str(e)}'})

    token = Token.objects.get_or_create(user=Account)[0].key
    if not check_password(password, Account.password):
        raise ValidationError({"message": "Incorrect Login credentials"})

    if Account:
        if Account.is_active:
            login(request, Account)
            data["message"] = "user logged in"
            data["email_address"] = Account.email

            Res = {"data": data, "token": token}

            return Response(Res)

        else:
            raise ValidationError({"400": f'Account not active'})

    else:
        raise ValidationError({"400": f'Account not active'})
