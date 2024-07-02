from django.urls import path
from . import views

urlpatterns = [
    path("drive/", views.DriveAuthView.as_view() ,name="drive"),
   # path("drive-account")
]