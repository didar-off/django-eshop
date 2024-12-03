from django.contrib import admin
from userauths import models

# Admin Models
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email']


class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'full_name', 'mobile', 'user_type']


admin.site.register(models.User, UserAdmin)
admin.site.register(models.Profile, ProfileAdmin)