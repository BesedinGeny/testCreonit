from django_filters import rest_framework as filters

from .models import Answer, Test


class TestFilter(filters.FilterSet):
    users_passed = filters.CharFilter(method='is_user_passed',
                                      field_name='user__username', lookup_expr='exact', label='users')

    class Meta:
        model = Test
        fields = ['users_passed', 'id', 'title']

    def is_user_passed(self, queryset, name, value):
        answered = Answer.objects.filter(user__username=value)
        tests_pk = []
        for answer in answered:
            tests_pk.append(answer.test.pk)
        print(tests_pk)
        queryset = Test.objects.filter(pk__in=tests_pk)
        # queryset = ListAsQuerySet() ??
        return queryset

