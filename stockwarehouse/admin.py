from django.contrib import admin
from .models import *

# Register your models here.

class AccountAdmin(admin.ModelAdmin):
    model= Account
    list_display = ['name','cash_balance','market_value','nav','margin_ratio','excess_equity','user_created']
    readonly_fields=['cash_balance','market_value','nav','margin_ratio','excess_equity','user_created','initial_margin_requirement','net_cash_flow','net_trading_value']
    search_fields = ['name',]
    def save_model(self, request, obj, form, change):
        # Lưu người dùng đang đăng nhập vào trường user nếu đang tạo cart mới
        if not change:  # Kiểm tra xem có phải là tạo mới hay không
            obj.user_created = request.user
        else:
            obj.user_modified = request.user.username
        obj.save()


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
    list_display = ['account','date','stock','position','price','qty','net_total_value','created_at','user_created','transaction_fee','tax']
    readonly_fields = ['user_created','user_modified','transaction_fee','tax','net_total_value']
    search_fields = ['account','stock',]
    def save_model(self, request, obj, form, change):
        # Lưu người dùng đang đăng nhập vào trường user nếu đang tạo cart mới
        if not change:  # Kiểm tra xem có phải là tạo mới hay không
            obj.user_created = request.user
        else:
            obj.user_modified = request.user.username
        obj.save()

admin.site.register(Transaction,TransactionAdmin)

class PortfolioAdmin(admin.ModelAdmin):
    model= Portfolio
    list_display = ['account','stock','market_price','avg_price','on_hold','receiving_t1','receiving_t2','profit','percent_profit']
    search_fields = ['stock',]


admin.site.register(Portfolio,PortfolioAdmin)

class ExpenseStatementAdmin(admin.ModelAdmin):
    model= ExpenseStatement
    list_display = ['account','date','type','amount','description']
    search_fields = ['account',]


admin.site.register(ExpenseStatement,ExpenseStatementAdmin)

class CashTransferAdmin(admin.ModelAdmin):
    model= CashTransfer
    list_display = ['account','date','amount','user_created','user_modified','created_at']
    readonly_fields = ['user_created','user_modified']
    search_fields = ['ticker',]
    def save_model(self, request, obj, form, change):
        # Lưu người dùng đang đăng nhập vào trường user nếu đang tạo cart mới
        if not change:  # Kiểm tra xem có phải là tạo mới hay không
            obj.user_created = request.user
        else:
            obj.user_modified = request.user.username
        obj.save()

admin.site.register(CashTransfer,CashTransferAdmin)