from django.urls import path
from .views import ZoomRecordDownloadView


urlpatterns = [
    path('api/download/', ZoomRecordDownloadView.as_view(), name='download'),
]
