from django.urls import path
from . import views 
urlpatterns = [
    
    path("mentor/", views.MentorView.as_view(), name="register-mentor")
]