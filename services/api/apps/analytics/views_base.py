from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from api_support import not_implemented


class DashboardViewBase(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        return not_implemented()


class CourseProgressViewBase(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        return not_implemented()


class StudyKitProgressViewBase(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        return not_implemented()
