from django.contrib import admin
from .models import *
from django.urls import reverse
from django.utils.html import format_html


# Register your models here.

class SignaldailyAdmin(admin.ModelAdmin):
    model = Signaldaily
    list_display = ('date','ticker','signal','close','market_price','wavefoot','ratio_cutloss','rating_total','rating_fundamental', 'is_closed','noted','view_transactions')
    list_filter = ('date','is_closed','noted')
    search_fields =['ticker',]
    def get_search_results(self, request, queryset, search_term):
        # Xử lý khi search_term không trống
        if search_term:
            # Tách các giá trị ticker thành một danh sách
            tickers = search_term.split(',')

            # Sử dụng Q objects để tạo ra điều kiện OR cho mỗi ticker
            q_objects = Q()
            for ticker in tickers:
                q_objects |= Q(ticker__iexact=ticker.strip())

            # Áp dụng điều kiện tìm kiếm
            queryset = queryset.filter(q_objects)
        # Trả về kết quả tìm kiếm
        return queryset, False

    # @admin.display(description="Giá hiện tại")
    # def market_price(self, obj):
    #     price = StockPriceFilter.objects.filter(ticker = obj.ticker).order_by('-date_time').first().close
    #     return price
    
    
    @admin.display(description="Điểm kỹ thuật")
    def rating_total(self, obj):
        point = OverviewBacktest.objects.filter(ticker = obj.ticker).first().rating_total
        return point
    
    @admin.display(description="% tăng/giảm")
    def wavefoot(self, obj):
        price = obj.market_price
        if obj.is_closed == True:
            if obj.noted == 'Cắt lỗ':
                ratio = round(obj.ratio_cutloss*-1,2)
            elif obj.noted =='Chốt lời':    
                ratio = round(obj.ratio_cutloss*2,2)
            else:
                ratio = 0
        else:
            ratio = round((price/ obj.close - 1) * 100, 2)
        return ratio
    
    @admin.display(description="Điểm cơ bản") 
    def rating_fundamental(self, obj):
        fa = StockFundamentalData.objects.filter(ticker = obj.ticker).first()
        return fa.fundamental_rating
    
    def view_transactions(self, obj):
        url = reverse('admin:stocklist_overviewbacktest_changelist') + f'?ticker={obj.ticker}'
        return format_html('<a href="{}">Xem kiểm định</a>', url)
    view_transactions.short_description = 'Xem kiểm định'


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

class StockFundamentalDataAdmin(admin.ModelAdmin):
    model= StockFundamentalData
    list_display = ['ticker','p_e','p_b','roa','roe','dept_ratio','growth_rating','stable_rating','valuation_rating','fundamental_rating']
    search_fields = ['ticker',]

admin.site.register(StockFundamentalData,StockFundamentalDataAdmin)
admin.site.register(StrategyTrading, StrategyTradingAdmin)
admin.site.register(ParamsOptimize, ParamsOptimizeAdmin)
admin.site.register(RatingStrategy,RatingStrategyAdmin)
admin.site.register(TransactionBacktest,TransactionBacktestAdmin)
admin.site.register(Signaldaily, SignaldailyAdmin)
admin.site.register(OverviewBacktest, OverviewBacktestAdmin)

