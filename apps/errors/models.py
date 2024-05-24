from django.db import models


class ZoomRecordingError(models.Model):
    error = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)