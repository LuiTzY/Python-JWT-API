from django.contrib import admin
from .models import Drive,UserDriveEmail

class DriveAdmin(admin.ModelAdmin):
    
    list_display = ("mentor","access_token","refresh_token")
    read_only_fields = ('created_at','update_at')

admin.site.register(Drive,DriveAdmin)
admin.site.register(UserDriveEmail)