from django.contrib import admin
from portfolio.models import *
from django.http import HttpResponse
from django.urls import reverse
from django.utils.html import format_html
from django.core.exceptions import ValidationError
from django.http import HttpResponse


class BotTelegramAdmin(admin.ModelAdmin):
    models = BotTelegram

class TransactionAdmin(admin.ModelAdmin):
    model = Transaction
    list_display = ('account','stock','position','price','str_qty','status','created_at','time_matched','time_receive','str_total_value', 'cut_loss_price', 'take_profit_price')
    fields = ('account','stock','position','price','qty', 'cut_loss_price', 'take_profit_price','str_total_value',)
    list_display_links=('stock',)
    readonly_fields = ('str_total_value',)
    list_filter = ('account_id','stock','position')
    @admin.display(description='qty')
    def str_qty(self, obj):
        return '{:,.0f}'.format(obj.qty)
    
    @admin.display(description='Total value')
    def str_total_value(self, obj):
        return obj.str_total_value
    @admin.display(description='Time Receive')
    def time_receive(self, obj):
        return obj.date_stock_on_account
    
    
   
    # def save_model(self, request, obj, form, change):
    #     account = Account.objects.get(pk =obj.account.pk)
    #     port = account.portfolio
    #      #ràng buộc phải đủ sức mua mới được mua
    #     if obj.position =='buy' and obj.qty * obj.price*1000 > account.net_cash_available:
    #         raise ValidationError('Không đủ sức mua')
    #     #ràng buộc bán phải đủ cổ phiếu
    #     elif obj.position =='sell':
    #         for item in port:
    #             if obj.stock == item['stock'] and obj.qty >item['qty_sellable'] - item['qty_sell_pending']:
    #                 raise ValidationError('Không đủ cổ phiếu bán')
    #             else:
    #                 obj.save()
    #     else:
    #         obj.save()
    
    
    
    

class CashTrasferAdmin(admin.ModelAdmin):
    model = CashTrasfer
    list_display = ('account','amount','created_at')
    list_filter = ('account',)

class AccountAdmin(admin.ModelAdmin):
    model = Account
    list_display = ('name','owner','ratio_risk','title_with_link',)
    list_filter = ('name',)
    def title_with_link(self, obj):
        url = reverse('portfolio:account', args=[obj.pk])
        return format_html("<a href='{}' target='_blank' style='background-color: #007bff; border-radius: 5px; color: white; padding: 5px;'>Xem Tài Khoản</a>", url)
    title_with_link.short_description = 'Thông tin Tài Khoản'
    


# Register your models here.
admin.site.register(CashTrasfer,CashTrasferAdmin)
admin.site.register(Transaction,TransactionAdmin)
admin.site.register(Account,AccountAdmin)
admin.site.register(DateNotTrading)
admin.site.register(BotTelegram,BotTelegramAdmin)
# admin.site.register(StockPrice)