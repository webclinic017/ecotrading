from django.contrib import admin
from .models import *


# Register your models here.

class SignaldailyAdmin(admin.ModelAdmin):
    model = Signaldaily
    list_display = ('date','ticker','close','strategy','signal','milestone','distance')
    list_filter = ('ticker','signal', 'ticker')

class OverviewBreakoutBacktestAdmin(admin.ModelAdmin):
    models = OverviewBreakoutBacktest
    list_display =['ticker','ratio_pln','total_trades','won_total_trades','drawdown',
                   'won_average_pnl','won_max_pnl', 'lost_total_trades', 'lost_average_pnl',
                   'lost_max_pnl', 'average_won_trades_per_day', 'sharpe_ratio']
    search_fields = ['ticker']

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.filter(total_trades__gt=0)


admin.site.register(Signaldaily, SignaldailyAdmin)
admin.site.register(OverviewBreakoutBacktest, OverviewBreakoutBacktestAdmin)
