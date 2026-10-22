from django_filters import rest_framework as filters
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from api_support import StandardPagination, not_implemented, save_or_conflict
from .models import PracticeTest, TestAttempt
from .serializers import PracticeTestSerializer, TestAttemptSerializer


class TestAttemptFilter(filters.FilterSet):
    status = filters.CharFilter(field_name='status')
    practice_test = filters.NumberFilter(field_name='practice_test')

    class Meta:
        model = TestAttempt
        fields = []


class PracticeTestFilter(filters.FilterSet):
    course = filters.NumberFilter(field_name='course')
    status = filters.CharFilter(field_name='status')
    difficulty = filters.CharFilter(field_name='difficulty')

    class Meta:
        model = PracticeTest
        fields = []


class TestAttemptViewSetBase(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = TestAttemptSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'put', 'head', 'options']
    lookup_value_regex = '[0-9]+'
    filterset_class = TestAttemptFilter
    filter_backends = [filters.DjangoFilterBackend]

    def get_queryset(self):
        return TestAttempt.objects.filter(user=self.request.user)

    @action(detail=True, methods=['put'], url_path='answers/(?P<question_id>[0-9]+)')
    def answers(self, request, *args, **kwargs):
        method = request.method.lower()
        method = 'get' if method == 'head' else method
        return getattr(self, f'handle_answers_{method}')(request, *args, **kwargs)

    def handle_answers_put(self, request, *args, **kwargs):
        return not_implemented()

    @action(detail=True, methods=['post'], url_path='submit')
    def submit(self, request, *args, **kwargs):
        method = request.method.lower()
        method = 'get' if method == 'head' else method
        return getattr(self, f'handle_submit_{method}')(request, *args, **kwargs)

    def handle_submit_post(self, request, *args, **kwargs):
        return not_implemented()

    @action(detail=True, methods=['get'], url_path='results')
    def results(self, request, *args, **kwargs):
        method = request.method.lower()
        method = 'get' if method == 'head' else method
        return getattr(self, f'handle_results_{method}')(request, *args, **kwargs)

    def handle_results_get(self, request, *args, **kwargs):
        return not_implemented()


class PracticeTestViewSetBase(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    serializer_class = PracticeTestSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['delete', 'get', 'patch', 'post', 'head', 'options']
    lookup_value_regex = '[0-9]+'
    pagination_class = StandardPagination
    filterset_class = PracticeTestFilter
    filter_backends = [filters.DjangoFilterBackend]

    def get_queryset(self):
        return PracticeTest.objects.filter(course__owner=self.request.user)

    def perform_update(self, serializer):
        save_or_conflict(serializer)

    def create(self, request, *args, **kwargs):
        return self.handle_create(request, *args, **kwargs)

    def handle_create(self, request, *args, **kwargs):
        return not_implemented()

    @action(detail=True, methods=['get'], url_path='questions')
    def questions(self, request, *args, **kwargs):
        method = request.method.lower()
        method = 'get' if method == 'head' else method
        return getattr(self, f'handle_questions_{method}')(request, *args, **kwargs)

    def handle_questions_get(self, request, *args, **kwargs):
        return not_implemented()

    @action(detail=True, methods=['get', 'post'], url_path='attempts')
    def attempts(self, request, *args, **kwargs):
        method = request.method.lower()
        method = 'get' if method == 'head' else method
        return getattr(self, f'handle_attempts_{method}')(request, *args, **kwargs)

    def handle_attempts_get(self, request, *args, **kwargs):
        return not_implemented()

    def handle_attempts_post(self, request, *args, **kwargs):
        return not_implemented()
