from django.contrib import admin
from .models import *

# # Register your models here.
# class UserAdmin (admin.ModelAdmin):
#     model = User
#     fields = ('username','password','first_name', 'last_name', 'phone_number', 'avatar', 
#               'email','is_staff', 'is_active', 'is_superuser')
#     list_display = ('avatar','username','first_name', 'last_name', 'phone_number', 
#               'email','is_staff', 'is_active', 'last_login')
#     list_display_links = ('username',)
    

# admin.site.register(User, UserAdmin )