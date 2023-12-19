from django.contrib import admin
from .models import *
from django.contrib.humanize.templatetags.humanize import intcomma

# Register your models here.


class AccountAdmin(admin.ModelAdmin):
    model= Account
    # list_display = ['name','id','formatted_cash_balance','interest_cash_balance','market_value','nav','margin_ratio','status']
    # readonly_fields=['cash_balance','market_value','nav','margin_ratio','excess_equity','user_created','initial_margin_requirement','net_cash_flow','net_trading_value','status']
    list_display = ['name', 'id', 'formatted_cash_balance', 'formatted_interest_cash_balance', 'formatted_market_value', 'formatted_nav', 'margin_ratio', 'status']
    readonly_fields = ['cash_balance', 'market_value', 'nav', 'margin_ratio', 'excess_equity', 'user_created', 'initial_margin_requirement', 'net_cash_flow', 'net_trading_value', 'status','cash_t2','cash_t1','excess_equity', 'interest_cash_balance' ]
    search_fields = ['name',]
    def save_model(self, request, obj, form, change):
        # Lưu người dùng đang đăng nhập vào trường user nếu đang tạo cart mới
        if not change:  # Kiểm tra xem có phải là tạo mới hay không
            obj.user_created = request.user
        else:
            obj.user_modified = request.user.username
        obj.save()

    def formatted_number(self, value):
        # Format number with commas as thousand separators and no decimal places
        return '{:,.0f}'.format(value)

    def formatted_cash_balance(self, obj):
        return self.formatted_number(obj.cash_balance)

    def formatted_interest_cash_balance(self, obj):
        return self.formatted_number(obj.interest_cash_balance)

    def formatted_market_value(self, obj):
        return self.formatted_number(obj.market_value)

    def formatted_nav(self, obj):
        return self.formatted_number(obj.nav)

    def formatted_margin_ratio(self, obj):
        return self.formatted_number(obj.margin_ratio)

    # Add other formatted_* methods for other numeric fields

    
    formatted_cash_balance.short_description = 'Số dư tiền'
    formatted_interest_cash_balance.short_description = 'Số dư tính lãi'
    formatted_market_value.short_description = 'Giá trị thị trường'
    formatted_nav.short_description = 'Tài sản ròng'
    formatted_margin_ratio.short_description = 'Tỷ lệ kí quỹ'


admin.site.register(Account,AccountAdmin)

class StockListMarginAdmin(admin.ModelAdmin):
    model= StockListMargin
    list_display = ['stock','initial_margin_requirement','ranking','exchanges','created_at','modified_at','user_created']
    search_fields = ['stock',]
    def save_model(self, request, obj, form, change):
        # Lưu người dùng đang đăng nhập vào trường user nếu đang tạo cart mới
        if not change:  # Kiểm tra xem có phải là tạo mới hay không
            obj.user_created = request.user
        else:
            obj.user_modified = request.user.username
        obj.save()


admin.site.register(StockListMargin,StockListMarginAdmin)

class TransactionAdmin(admin.ModelAdmin):
    model= Transaction
    list_display_links = ['stock',]
    list_display = ['account','date','stock','position','formatted_price','formatted_qty','formatted_net_total_value','created_at','user_created','transaction_fee','tax']
    readonly_fields = ['user_created','user_modified','transaction_fee','tax','total_value','net_total_value']
    search_fields = ['account__name','stock__stock']
    def save_model(self, request, obj, form, change):
        # Lưu người dùng đang đăng nhập vào trường user nếu đang tạo cart mới
        if not change:  # Kiểm tra xem có phải là tạo mới hay không
            obj.user_created = request.user
        else:
            obj.user_modified = request.user.username
        obj.save()

    def formatted_number(self, value):
        # Format number with commas as thousand separators and no decimal places
        return '{:,.0f}'.format(value)
    
    def formatted_price(self, obj):
        return self.formatted_number(obj.price)
    
    def formatted_qty(self, obj):
        return self.formatted_number(obj.qty)
    
    def formatted_net_total_value(self, obj):
        return self.formatted_number(obj.net_total_value)

    # Add other formatted_* methods for other numeric fields

    
    formatted_price.short_description = 'Giá'
    formatted_qty.short_description = 'Khối lượng'
    formatted_net_total_value.short_description = 'Giá trị giao dịch ròng'

admin.site.register(Transaction,TransactionAdmin)

class PortfolioAdmin(admin.ModelAdmin):
    model= Portfolio
    list_display = ['account','stock','market_price','avg_price','on_hold','receiving_t1','receiving_t2','profit','percent_profit','sum_stock']
    readonly_fields = ['account','stock','market_price','avg_price','on_hold','receiving_t1','receiving_t2','profit','percent_profit', 'sum_stock']
    search_fields = ['stock','account__name']
    def get_queryset(self, request):
        # Chỉ trả về các bản ghi có sum_stock > 0
        return super().get_queryset(request).filter(sum_stock__gt=0)


admin.site.register(Portfolio,PortfolioAdmin)

class ExpenseStatementAdmin(admin.ModelAdmin):
    model = ExpenseStatement
    list_display = ['account', 'date', 'type', 'formatted_amount', 'description']
    search_fields = ['account__name']

    def formatted_amount(self, obj):
        return '{:,.0f}'.format(obj.amount)

    formatted_amount.short_description = 'Số tiền'

admin.site.register(ExpenseStatement, ExpenseStatementAdmin)

class CashTransferAdmin(admin.ModelAdmin):
    model = CashTransfer
    list_display = ['account', 'date', 'formatted_amount', 'user_created', 'user_modified', 'created_at']
    readonly_fields = ['user_created', 'user_modified']
    search_fields = ['account__name']

    def formatted_amount(self, obj):
        return '{:,.0f}'.format(obj.amount)

    formatted_amount.short_description = 'Số tiền'
    
    def save_model(self, request, obj, form, change):
        # Lưu người dùng đang đăng nhập vào trường user nếu đang tạo cart mới
        if not change:  # Kiểm tra xem có phải là tạo mới hay không
            obj.user_created = request.user
        else:
            obj.user_modified = request.user.username
        obj.save()

admin.site.register(CashTransfer,CashTransferAdmin)