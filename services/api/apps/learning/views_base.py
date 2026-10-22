from django_filters import rest_framework as filters
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from api_support import StandardPagination, not_implemented
from .models import CardProgress, StudySession
from .serializers import CardProgressSerializer, StudySessionSerializer


class StudySessionFilter(filters.FilterSet):
    course = filters.NumberFilter(field_name='course')
    study_kit = filters.NumberFilter(field_name='study_kit')
    mode = filters.CharFilter(field_name='mode')

    class Meta:
        model = StudySession
        fields = []


class CardProgressFilter(filters.FilterSet):
    flashcard = filters.NumberFilter(field_name='flashcard')
    study_kit = filters.NumberFilter(field_name='flashcard__study_kit')
    course = filters.NumberFilter(field_name='flashcard__study_kit__course')

    class Meta:
        model = CardProgress
        fields = []


class StudySessionViewSetBase(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = StudySessionSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'head', 'options']
    lookup_value_regex = '[0-9]+'
    pagination_class = StandardPagination
    filterset_class = StudySessionFilter
    filter_backends = [filters.DjangoFilterBackend]

    def get_queryset(self):
        return StudySession.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        return self.handle_create(request, *args, **kwargs)

    def handle_create(self, request, *args, **kwargs):
        return not_implemented()

    @action(detail=True, methods=['get'], url_path='queue')
    def queue(self, request, *args, **kwargs):
        method = request.method.lower()
        method = 'get' if method == 'head' else method
        return getattr(self, f'handle_queue_{method}')(request, *args, **kwargs)

    def handle_queue_get(self, request, *args, **kwargs):
        return not_implemented()

    @action(detail=True, methods=['post'], url_path='reviews')
    def reviews(self, request, *args, **kwargs):
        method = request.method.lower()
        method = 'get' if method == 'head' else method
        return getattr(self, f'handle_reviews_{method}')(request, *args, **kwargs)

    def handle_reviews_post(self, request, *args, **kwargs):
        return not_implemented()

    @action(detail=True, methods=['post'], url_path='complete')
    def complete(self, request, *args, **kwargs):
        method = request.method.lower()
        method = 'get' if method == 'head' else method
        return getattr(self, f'handle_complete_{method}')(request, *args, **kwargs)

    def handle_complete_post(self, request, *args, **kwargs):
        return not_implemented()


class CardProgressViewSetBase(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = CardProgressSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'head', 'options']
    lookup_value_regex = '[0-9]+'
    pagination_class = StandardPagination
    filterset_class = CardProgressFilter
    filter_backends = [filters.DjangoFilterBackend]

    def get_queryset(self):
        return CardProgress.objects.filter(user=self.request.user)


class StrugglingCardsViewBase(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        return not_implemented()
