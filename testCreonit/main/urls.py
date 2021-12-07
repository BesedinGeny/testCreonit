from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import index, TestsView, TestView, login_user


urlpatterns = [
    path('', index),
    path('login/', login_user, name='login'),
    path('tests/', TestsView.as_view(), name='tests'),
    path('tests/<slug:test_slug>/', TestView.as_view(), name='test_page'),
]

