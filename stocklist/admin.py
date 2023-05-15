from django.contrib import admin
from .models import *

# Register your models here.

class SignaldailyAdmin(admin.ModelAdmin):
    model = Signaldaily
    list_display = ('date','ticker','close','strategy','signal','bottom','distance_bottom')
    list_filter = ('ticker','signal')

admin.site.register(Signaldaily, SignaldailyAdmin)
