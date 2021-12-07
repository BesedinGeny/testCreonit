from django_filters import rest_framework as filters

from .models import Answer, Test


class TestFilter(filters.FilterSet):
    users_passed = filters.CharFilter(method='is_user_passed',
                                      field_name='user__username', lookup_expr='exact', label='users')

    class Meta:
        model = Test
        fields = ['users_passed', 'id', 'title']

    def is_user_passed(self, queryset, name, value):
        answered = Test.objects.filter(answer__username=value)
        return answered
