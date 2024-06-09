
from django.contrib import admin
from django.urls import path,include
from rest_framework_simplejwt.views import TokenObtainPairView,TokenRefreshView 
from rest_framework_simplejwt.views import TokenBlacklistView


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include("apps.users.urls")),
    path('api/',include("apps.zoom.urls")),
    path('',include('apps.download_notifications.routing')),
    path('api/',include('apps.clients.urls'))
]
