from django.contrib.auth import authenticate, login, get_user_model
from django.shortcuts import render
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, status, generics, filters
from rest_framework.mixins import CreateModelMixin
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from .filters import TestFilter
from .models import Test, Answer, AnswerDone, Task
from .serializers import TestSerializer, UserSerializer


def method_permission_classes(classes):
    def decorator(func):
        def decorated_func(self, *args, **kwargs):
            self.permission_classes = classes
            self.check_permissions(self.request)
            return func(self, *args, **kwargs)

        return decorated_func

    return decorator


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 2
    page_size_query_param = 'page_size'
    max_page_size = 20


def index(request):
    return render(request, 'main/index.html')


class TestsView(generics.ListAPIView):
    queryset = Test.objects.all()
    serializer_class = TestSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = TestFilter


class TestView(APIView):
    """
        Обработка теста
        для админа: возможность получить/добавить/изменить/удалить тест
        для пользователя: возможность пройти тест/просмотреть результаты пройденного теста
    """

    @method_permission_classes((permissions.IsAdminUser | permissions.IsAuthenticated,))
    def get(self, request, test_slug):
        test = Test.objects.get(slug=test_slug)
        button_disabled = False
        previous_results = None
        passed_before = Answer.objects.filter(
            test__pk=test.pk,
            user__username=request.user.username
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

        if request.method == 'POST' and request.POST.get("btn_submit", "") == 'Закончить тест':
            # поля отправляемые формой, но нам не нужны
            STUFF_FIELDS = ['btn_submit', 'csrfmiddlewaretoken', 'test_id', 'task_id']
            answered = []  # список ответов пользователя
            test_id = request.POST['test_id']
            user_pk = request.user.pk

            for key in request.POST:
                value = dict(request.POST)[key]
                task_id = request.POST['task_id']
                if key not in STUFF_FIELDS:
                    task = Task.objects.get(pk=key)  # TODO: немного хардкода ..
                    raw_value = ""
                    if task.task_type == "SINGLE":
                        raw_value = value[0]
                    elif task.task_type == "MANY":
                        raw_value = " ".join(value)
                    elif task.task_type == "FULL":
                        raw_value = value[0]
                    current_answer = AnswerDone.objects.create(test_id=test_id, task_id=task_id, text=raw_value)
                    answered.append(current_answer)

            answer = Answer.objects.create(test_id=test_id, user_id=user_pk)
            answer.answers.add(*answered)
            return self.get(request, test_slug)  # смотрим что напроходили

        else:  # POST от админа на создание теста
            serializer = TestSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
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


class CreateUserView(CreateModelMixin, GenericViewSet):
    permission_classes = [AllowAny]
    queryset = get_user_model().objects.all()
    serializer_class = UserSerializer


class LoginView(APIView):
    template_name = 'main/login.html'

    def post(self, request, format=None):
        data = request.data

        username = data.get('username', None)
        password = data.get('password', None)

        user = authenticate(username=username, password=password)

        if user is not None:
            if user.is_active:
                login(request, user)
                return Response(status=status.HTTP_200_OK, template_name=self.template_name)  # render ??
            else:
                return Response(status=status.HTTP_404_NOT_FOUND)
        else:
            return Response(status=status.HTTP_404_NOT_FOUND)

    def get(self, request):
        return Response(template_name=self.template_name)
