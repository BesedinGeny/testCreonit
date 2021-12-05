from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import index, TestsView, CreateUserView, LoginView, TestView

router = DefaultRouter()
router.register(r'register', CreateUserView)

urlpatterns = [
    path('', index),
    path('login/', LoginView.as_view(), name='login'),
    #  path('register/', create_auth, name='register'),
    path('tests/', TestsView.as_view(), name='tests'),
    path('tests/<slug:test_slug>/', TestView.as_view(), name='test_page'),
]

urlpatterns += router.urls
