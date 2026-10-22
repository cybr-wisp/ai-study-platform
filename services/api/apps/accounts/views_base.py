from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView

from api_support import not_implemented


class RegisterViewBase(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        return not_implemented()


class MeViewBase(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        return not_implemented()
