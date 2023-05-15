from django.contrib import admin
from .models import *

# Register your models here.

class SignaldailyAdmin(admin.ModelAdmin):
    model = Signaldaily
    list_display = ('date','ticker','close','strategy','signal','milestone','distance')
    list_filter = ('ticker','signal', 'ticker')

admin.site.register(Signaldaily, SignaldailyAdmin)
