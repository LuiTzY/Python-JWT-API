from django.urls import path
from . import views
urlpatterns = [
    path("zoom/", views.ZoomCredentialsView.as_view(),name='zoom' ),
    path("recording/", views.ZoomRecordingsViews.as_view(), name='recording'),
    path("zoom-account/",views.ZoomEmailUserAccount.as_view(), name='zoom-account')
]