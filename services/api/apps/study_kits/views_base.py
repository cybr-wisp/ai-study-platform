from django_filters import rest_framework as filters
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from api_support import StandardPagination, not_implemented, save_or_conflict
from .models import StudyKit
from .serializers import StudyKitSerializer


class StudyKitFilter(filters.FilterSet):
    course = filters.NumberFilter(field_name='course')
    status = filters.CharFilter(field_name='status')

    class Meta:
        model = StudyKit
        fields = []


class StudyKitViewSetBase(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    serializer_class = StudyKitSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['delete', 'get', 'patch', 'post', 'head', 'options']
    lookup_value_regex = '[0-9]+'
    pagination_class = StandardPagination
    filterset_class = StudyKitFilter
    filter_backends = [filters.DjangoFilterBackend]

    def get_queryset(self):
        return StudyKit.objects.filter(course__owner=self.request.user)

    def perform_update(self, serializer):
        save_or_conflict(serializer)

    def create(self, request, *args, **kwargs):
        return self.handle_create(request, *args, **kwargs)

    def handle_create(self, request, *args, **kwargs):
        return not_implemented()

    @action(detail=True, methods=['post'], url_path='regenerate')
    def regenerate(self, request, *args, **kwargs):
        method = request.method.lower()
        method = 'get' if method == 'head' else method
        return getattr(self, f'handle_regenerate_{method}')(request, *args, **kwargs)

    def handle_regenerate_post(self, request, *args, **kwargs):
        return not_implemented()
