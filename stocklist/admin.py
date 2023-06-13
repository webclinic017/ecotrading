from django.contrib import admin
from .models import *
from django.urls import reverse
from django.utils.html import format_html


# Register your models here.

class SignaldailyAdmin(admin.ModelAdmin):
    model = Signaldaily
    list_display = ('date','ticker','strategy','signal','close','market_price','wavefoot','ratio_cutloss', 'modified_date')
    list_filter = ('date',)
    search_fields = ['ticker']

    @admin.display(description="Giá hiện tại")
    def market_price(self, obj):
        price = StockPriceFilter.objects.filter(ticker = obj.ticker).order_by('-date_time').first().close
        return price
    
    @admin.display(description="% tăng/giảm")
    def wavefoot(self, obj):
        price = price = StockPriceFilter.objects.filter(ticker = obj.ticker).order_by('-date_time').first().close
        return round((price/ obj.close - 1) * 100, 2)


class OverviewBacktestAdmin(admin.ModelAdmin):
    model = OverviewBacktest
    list_display =['strategy','ticker','rating_total','rating_profit','rating_win_trade','rating_day_hold','total_trades','win_trade_ratio',
                   'deal_average_pnl','drawdown','sharpe_ratio','view_transactions']
    search_fields = ['ticker']
    list_filter = ['strategy',]

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.filter(total_trades__gt=0)
    
    def view_transactions(self, obj):
        url = reverse('admin:stocklist_transactionbacktest_changelist') + f'?ticker={obj.ticker}'
        return format_html('<a href="{}">Xem giao dịch</a>', url)
    view_transactions.short_description = 'Xem giao dịch'

    
   
    
class TransactionBacktestAdmin(admin.ModelAdmin):
    model = TransactionBacktest
    list_display = ['strategy','ticker','ratio_pln','date_buy','qty','buy_price','date_sell','sell_price','len_days','stop_loss','take_profit','modified_date']
    search_fields = ['ticker']
    list_filter = ['strategy',]

class RatingStrategyAdmin(admin.ModelAdmin):
    model= RatingStrategy
    list_display = ['strategy','modified_date','ratio_pln','total_trades','win_trade_ratio','drawdown','sharpe_ratio',
                   'won_average_pnl', 'lost_average_pnl',
                 'average_won_trades_per_day','average_lost_trades_per_day']
    search_fields = ['strategy','name']
    

class ParamsOptimizeAdmin(admin.ModelAdmin):  
    model = ParamsOptimize
    list_display = ['strategy','ticker','multiply_volumn','rate_of_increase','change_day','ratio_cutloss','sma']
    search_fields = ['ticker']
    list_filter = ['strategy',]

class StrategyTradingAdmin(admin.ModelAdmin):
    model = StrategyTrading
    list_display = ['name','risk','nav','commission', 'period']

admin.site.register(StrategyTrading, StrategyTradingAdmin)
admin.site.register(ParamsOptimize, ParamsOptimizeAdmin)
admin.site.register(RatingStrategy,RatingStrategyAdmin)
admin.site.register(TransactionBacktest,TransactionBacktestAdmin)
admin.site.register(Signaldaily, SignaldailyAdmin)
admin.site.register(OverviewBacktest, OverviewBacktestAdmin)

