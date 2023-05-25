from django.contrib import admin
from .models import *


# Register your models here.

class SignaldailyAdmin(admin.ModelAdmin):
    model = Signaldaily
    list_display = ('date','ticker','close','strategy','signal','milestone','distance')
    list_filter = ('ticker','signal', 'ticker')

class OverviewBreakoutBacktestAdmin(admin.ModelAdmin):
    models = OverviewBreakoutBacktest
    list_display =['ticker','ratio_pln','total_trades','win_trade_ratio','drawdown','sharpe_ratio',
                   'won_average_pnl', 'lost_average_pnl',
                 'average_won_trades_per_day','average_lost_trades_per_day']
    search_fields = ['ticker']

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.filter(total_trades__gt=0)
    
class TransactionBacktestAdmin(admin.ModelAdmin):
    model = TransactionBacktest
    list_display = ['ticker','ratio_pln','date_buy','qty','buy_price','date_sell','sell_price','len_days','stop_loss','take_profit']
    search_fields = ['ticker']


admin.site.register(TransactionBacktest,TransactionBacktestAdmin)
admin.site.register(Signaldaily, SignaldailyAdmin)
admin.site.register(OverviewBreakoutBacktest, OverviewBreakoutBacktestAdmin)

