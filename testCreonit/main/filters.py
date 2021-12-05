from django_filters import rest_framework as filters

from .models import Test, Answer, MyUser


class TestFilter(filters.FilterSet):
    users_passed = filters.CharFilter(method='is_user_passed', field_name='users_passed')

    """class Meta:
        model = Test
        fields = {'users_passed': ['exact']}"""

    def is_user_passed(self, queryset, name, value):
        answered = Answer.objects.filter(test__id=self.pk)
        usernames = []
        for answer in answered:
            usernames.append(answer.user.username)
        querset = MyUser.objects.filter(username__in=usernames)
        # queryset = ListAsQuerySet() ??
        return querset

