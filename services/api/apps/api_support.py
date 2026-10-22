from django.db import IntegrityError, transaction
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


def not_implemented():
    return Response({'detail': 'Not implemented.'}, status=status.HTTP_501_NOT_IMPLEMENTED)


def save_or_conflict(serializer, **kwargs):
    try:
        with transaction.atomic():
            return serializer.save(**kwargs)
    except IntegrityError:
        raise ValidationError({'detail': ['This change conflicts with an existing object.']}) from None
