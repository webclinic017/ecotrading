from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_save
from portfolio.models import *

# Create your models here.

class Signaldaily(models.Model):
    ticker = models.CharField(max_length=10)
    date = models.DateField()#auto_now_add=True)
    bottom = models.FloatField(default=0)
    signal = models.CharField(max_length=10)
    strategy = models.CharField(max_length=50)
    def __str__(self):
        return str(self.ticker) + str(self.strategy)
    
    @property
    def close(self):
        close = StockPrice.objects.filter(ticker = self.ticker).order_by('-date').first().close
        return close
    
    @property
    def distance_bottom(self):
        return round((self.close/self.bottom-1)*100,0)
    
@receiver(post_save, sender=Signaldaily)
def create_trasation_auto_bot(sender, instance, created, **kwargs):
    if created:
        account = Account.objects.get(name ='Bot_Breakout')
        close_price = StockPriceFilter.objects.filter(ticker = instance.ticker).order_by('-date').first().close
        try:
            Transaction.objects.create(
                account= account.pk,
                stock= instance.ticker,
                position='buy',
                price= round(close_price*(1+0.002),2),
                qty=1000,
                description = 'Auto trade' )
        except Exception as e:
            chat_id = account.bot.chat_id
            bot = Bot(token=account.bot.token)
            bot.send_message(
            chat_id='-870288807', 
            text=f"Tự động giao dịch {instance.ticker} theo chiến lược breakout thất bại, lỗi {e}   ")                  

