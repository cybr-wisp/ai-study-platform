from django.db.models import Avg, Count, F, FloatField, Max, Q
from django.db.models.functions import Coalesce
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Flashcard, StudyAttempt
from .serializers import FlashcardSerializer, StudyAttemptSerializer


class FlashcardListView(generics.ListCreateAPIView):
    queryset = Flashcard.objects.all()
    serializer_class = FlashcardSerializer


class FlashcardDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Flashcard.objects.all()
    serializer_class = FlashcardSerializer


class SubmitAttemptView(APIView):
    """Record one answer with a confidence rating (1-5)."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = StudyAttemptSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)  # user comes from login, never the request body
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class NextCardsView(APIView):
    """Cards to study next: unseen first, then lowest confidence, then most misses."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            limit = max(1, min(int(request.query_params.get('limit', 10)), 50))
        except ValueError:
            limit = 10

        mine = Q(attempts__user=request.user)
        cards = (
            Flashcard.objects.annotate(
                avg_conf=Coalesce(
                    Avg('attempts__confidence', filter=mine),
                    0.0,
                    output_field=FloatField(),
                ),
                misses=Count('attempts', filter=mine & Q(attempts__is_correct=False)),
                last_seen=Max('attempts__created_at', filter=mine),
            )
            .order_by('avg_conf', '-misses', F('last_seen').asc(nulls_first=True))[:limit]
        )
        return Response(FlashcardSerializer(cards, many=True).data)


class StudyStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        stats = StudyAttempt.objects.filter(user=request.user).aggregate(
            total=Count('id'),
            correct=Count('id', filter=Q(is_correct=True)),
            avg_confidence=Avg('confidence'),
        )
        stats['accuracy'] = stats['correct'] / stats['total'] if stats['total'] else None
        return Response(stats)