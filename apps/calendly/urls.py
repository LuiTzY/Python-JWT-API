from django.urls import path
from . import views

urlpatterns = [
    path("calendly/", views.CalendlyCredentialsView.as_view(), name="calendly")
]