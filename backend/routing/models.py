from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils import timezone


def _default_preferences():
    return {'greenery': 0, 'noise': 0, 'airQuality': 0}


def _default_route():
    return []


class RouteRecord(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='routes')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=120, blank=True)
    saved = models.BooleanField(default=False)
    start_point = models.JSONField()
    end_point = models.JSONField()
    start_label = models.CharField(max_length=160, blank=True)
    end_label = models.CharField(max_length=160, blank=True)
    preferences = models.JSONField(default=_default_preferences)
    route = models.JSONField(default=_default_route)
    distance_m = models.FloatField(default=0.0)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'{self.user_id}: {self.name or "Route"}'
