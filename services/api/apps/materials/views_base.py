from django_filters import rest_framework as filters
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated

from api_support import StandardPagination, not_implemented, save_or_conflict
from .models import AIJob, Document, DocumentChunk
from .serializers import AIJobSerializer, DocumentSerializer, DocumentChunkSerializer


class DocumentFilter(filters.FilterSet):
    course = filters.NumberFilter(field_name='course')
    status = filters.CharFilter(field_name='status')
    file_type = filters.CharFilter(field_name='file_type')

    class Meta:
        model = Document
        fields = []


class AIJobFilter(filters.FilterSet):
    course = filters.NumberFilter(field_name='course')
    job_type = filters.CharFilter(field_name='job_type')
    status = filters.CharFilter(field_name='status')

    class Meta:
        model = AIJob
        fields = []


class DocumentViewSetBase(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['delete', 'get', 'patch', 'post', 'head', 'options']
    lookup_value_regex = '[0-9]+'
    pagination_class = StandardPagination
    filterset_class = DocumentFilter
    search_fields = ['title', 'original_filename']
    filter_backends = [filters.DjangoFilterBackend, SearchFilter]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        return Document.objects.filter(course__owner=self.request.user)

    def perform_update(self, serializer):
        save_or_conflict(serializer)

    def create(self, request, *args, **kwargs):
        return self.handle_create(request, *args, **kwargs)

    def handle_create(self, request, *args, **kwargs):
        return not_implemented()

    @action(detail=True, methods=['get'], url_path='download')
    def download(self, request, *args, **kwargs):
        method = request.method.lower()
        method = 'get' if method == 'head' else method
        return getattr(self, f'handle_download_{method}')(request, *args, **kwargs)

    def handle_download_get(self, request, *args, **kwargs):
        return not_implemented()

    @action(detail=True, methods=['post'], url_path='reprocess')
    def reprocess(self, request, *args, **kwargs):
        method = request.method.lower()
        method = 'get' if method == 'head' else method
        return getattr(self, f'handle_reprocess_{method}')(request, *args, **kwargs)

    def handle_reprocess_post(self, request, *args, **kwargs):
        return not_implemented()


class DocumentChunkViewSetBase(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = DocumentChunkSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'head', 'options']
    lookup_value_regex = '[0-9]+'

    def get_queryset(self):
        return DocumentChunk.objects.filter(document__course__owner=self.request.user)


class AIJobViewSetBase(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = AIJobSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'head', 'options']
    lookup_value_regex = '[0-9]+'
    pagination_class = StandardPagination
    filterset_class = AIJobFilter
    filter_backends = [filters.DjangoFilterBackend]

    def get_queryset(self):
        return AIJob.objects.filter(course__owner=self.request.user)

    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel(self, request, *args, **kwargs):
        method = request.method.lower()
        method = 'get' if method == 'head' else method
        return getattr(self, f'handle_cancel_{method}')(request, *args, **kwargs)

    def handle_cancel_post(self, request, *args, **kwargs):
        return not_implemented()
