from django.db import models
from django.contrib.auth.models import User

class More(models.Model):
    user =  models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    phone = models.CharField(max_length=10, null=True, blank=True)
    avatar = models.ImageField(upload_to='member', null = True, blank=True,default = "")



