from django.db import models

# Create your models here.

class Signaldaily(models.Model):
    ticker = models.CharField(max_length=10)
    date = models.DateField()#auto_now_add=True)
    signal = models.CharField(max_length=10)
    strategy = models.CharField(max_length=50)
    def __str__(self):
        return str(self.ticker) + str(self.strategy)


