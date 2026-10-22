from django_filters import rest_framework as filters
from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated

from api_support import StandardPagination, not_implemented, save_or_conflict
from .models import Flashcard
from .serializers import FlashcardSerializer


class FlashcardFilter(filters.FilterSet):
    study_kit = filters.NumberFilter(field_name='study_kit')
    difficulty = filters.CharFilter(field_name='difficulty')
    is_archived = filters.BooleanFilter(field_name='is_archived')

    class Meta:
        model = Flashcard
        fields = []


class FlashcardViewSetBase(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    serializer_class = FlashcardSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['delete', 'get', 'patch', 'post', 'head', 'options']
    lookup_value_regex = '[0-9]+'
    pagination_class = StandardPagination
    filterset_class = FlashcardFilter
    filter_backends = [filters.DjangoFilterBackend]

    def get_queryset(self):
        return Flashcard.objects.filter(study_kit__course__owner=self.request.user)

    def perform_update(self, serializer):
        save_or_conflict(serializer)

    def create(self, request, *args, **kwargs):
        return self.handle_create(request, *args, **kwargs)

    def handle_create(self, request, *args, **kwargs):
        return not_implemented()
