from django_filters import rest_framework as filters
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated

from api_support import StandardPagination, not_implemented, save_or_conflict
from .models import Course
from .serializers import CourseSerializer


class CourseFilter(filters.FilterSet):
    is_archived = filters.BooleanFilter(field_name='is_archived')

    class Meta:
        model = Course
        fields = []


class CourseViewSetBase(mixins.ListModelMixin, mixins.CreateModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['delete', 'get', 'patch', 'post', 'head', 'options']
    lookup_value_regex = '[0-9]+'
    pagination_class = StandardPagination
    filterset_class = CourseFilter
    search_fields = ['title', 'code', 'term']
    ordering_fields = ['position', 'title', 'created_at']
    filter_backends = [filters.DjangoFilterBackend, SearchFilter, OrderingFilter]

    def get_queryset(self):
        return Course.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        save_or_conflict(serializer, owner=self.request.user)

    def perform_update(self, serializer):
        save_or_conflict(serializer)

    @action(detail=False, methods=['post'], url_path='reorder')
    def reorder(self, request, *args, **kwargs):
        method = request.method.lower()
        method = 'get' if method == 'head' else method
        return getattr(self, f'handle_reorder_{method}')(request, *args, **kwargs)

    def handle_reorder_post(self, request, *args, **kwargs):
        return not_implemented()
