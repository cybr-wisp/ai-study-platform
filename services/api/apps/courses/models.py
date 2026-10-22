from django.conf import settings
from django.db import models


class Course(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='courses')
    title = models.CharField(max_length=200)
    code = models.CharField(max_length=32, blank=True, default='')
    description = models.TextField(blank=True, default='')
    term = models.CharField(max_length=64, blank=True, default='')
    color = models.CharField(max_length=7, default='#6366F1')
    position = models.PositiveIntegerField(default=0)
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['position', 'title']
        indexes = [
            models.Index(fields=['owner', 'is_archived'], name='crs_owner_arch_idx'),
        ]
        constraints = [
            models.UniqueConstraint(fields=['owner', 'code'], name='crs_owner_code_uniq', condition=~models.Q(code='')),
        ]

    def __str__(self):
        return str(self.title)
