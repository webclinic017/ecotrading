from django.db import models
from django.db.models.signals import post_save, post_delete,pre_save, pre_delete
from django.contrib.auth.models import User
from django.dispatch import receiver
from datetime import datetime, timedelta
from portfolio.models import DateNotTrading

from django.utils import timezone

# Create your models here.
class Account (models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name= 'Tên')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name = 'Ngày tạo' )
    modified_at = models.DateTimeField(auto_now=True, verbose_name = 'Ngày chỉnh sửa' )
    description = models.TextField(max_length=255, blank=True, verbose_name= 'Mô tả')
    referrer = models.CharField(max_length=50,blank=True, null=True, verbose_name= 'Người giới thiệu' )
    interest_fee = models.FloatField(default=0.15,verbose_name= 'Lãi suất')
    transaction_fee = models.FloatField(default=0.0015, verbose_name= 'Phí giao dịch')
    tax = models.FloatField(default=0.001, verbose_name= 'Thuế')
    # bot = models.ForeignKey(BotTelegram,on_delete=models.CASCADE, verbose_name= 'Bot' )
    net_cash_flow= models.FloatField(default=0,verbose_name= 'Nạp rút tiền ròng')
    net_trading_value= models.FloatField(default=0,verbose_name= 'Giao dịch ròng')
    cash_balance  = models.FloatField(default=0,verbose_name= 'Sơ dư tiền')
    market_value = models.FloatField(default=0,verbose_name= 'Giá trị thị trường')
    nav = models.FloatField(default=0,verbose_name= 'Tài sản ròng')
    initial_margin_requirement= models.FloatField(default=0,verbose_name= 'Kí quy ban đầu')
    margin_ratio = models.FloatField(default=0,verbose_name= 'Tỷ lệ margin')
    excess_equity= models.FloatField(default=0,verbose_name= 'Dư kí quỹ')
    user_created = models.ForeignKey(User,on_delete=models.CASCADE,related_name='user',null=True, blank= True,verbose_name="Người tạo")
    user_modified = models.CharField(max_length=150, blank=True, null=True,verbose_name="Người chỉnh sửa")



    class Meta:
         verbose_name = 'Tài khoản'
         verbose_name_plural = 'Tài khoản'

    def __str__(self):
        return self.name
    

   
    # @property
    # def portfolio(self):
    #     return qty_stock_on_account(self.pk)[0]
    # @property
    # def str_portfolio(self):
    #     return qty_stock_on_account(self.pk)[1]

    
    # @property
    # def net_cash_flow(self):
    #     item = CashTrasfer.objects.filter(account_id =self.pk)
    #     total = sum(i.amount for i in item )
    #     return total

    # @property
    # def net_cash_available(self):
    #     item = Transaction.objects.filter(account_id = self.pk)
    #     total_trading = sum(i.total_value for i in item if i.status_raw == 'matched')
    #     # cần cộng thêm giá trị deal mua đang chờ khớp
    #     pending = sum(i.total_value for i in item if i.status_raw != 'matched' and i.position =='buy')
    #     net_cash_available = self.net_cash_flow - total_trading -pending
    #     return net_cash_available
    
    # @property
    # def market_value(self):
    #     port = self.portfolio
    #     market_value = sum(item['qty_total']*item['market_price']*1000 for item in port)
    #     return market_value
    

    # @property
    # def total_profit(self):
    #     order_list = Transaction.objects.filter(account_id = self.pk,status_raw = 'matched' )
    #     total_trading = sum(i.total_value for i in order_list)
    #     net_cash_available = self.net_cash_flow - total_trading
    #     total = net_cash_available+ self.market_value -self.net_cash_flow 
    #     return total
    # @property
    # def close_deal(self):
    #     close_deal= cal_profit_deal_close(self.pk )
    #     return close_deal
    # @property
    # def total_profit_close(self):
    #     total_profit_close = sum(i['profit'] for i in self.close_deal[0])
    #     return total_profit_close

    # @property
    # def total_profit_open(self):
    #     total_profit_open = sum(i['profit'] for i in self.portfolio)
    #     return total_profit_open

class StockListMargin(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name = 'Ngày tạo' )
    modified_at = models.DateTimeField(auto_now=True, verbose_name = 'Ngày chỉnh sửa' )
    stock = models.CharField(max_length=8,verbose_name = 'Cổ phiếu')
    initial_margin_requirement= models.FloatField(verbose_name= 'Kí quy ban đầu')
    ranking =models.IntegerField(verbose_name='Loại')
    exchanges = models.CharField(max_length=10, verbose_name= 'Sàn giao dịch')
    user_created = models.ForeignKey(User,on_delete=models.CASCADE,null=True, blank= True,                   verbose_name="Người tạo")
    user_modified = models.CharField(max_length=150, blank=True, null=True,
                             verbose_name="Người chỉnh sửa")
    class Meta:
         verbose_name = 'Danh mục cho vay'
         verbose_name_plural = 'Danh mục cho vay'

    def __str__(self):
        return str(self.stock)

class CashTransfer(models.Model):
    account = models.ForeignKey(Account,on_delete=models.CASCADE,verbose_name = 'Tài khoản' )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name = 'Ngày tạo' )
    modified_at = models.DateTimeField(auto_now=True, verbose_name = 'Ngày chỉnh sửa' )
    date = models.DateField( default=timezone.now,verbose_name = 'Ngày nộp tiền' )
    amount = models.FloatField(verbose_name = 'Số tiền')
    description = models.TextField(max_length=255, blank=True,verbose_name = 'Mô tả')
    user_created = models.ForeignKey(User,on_delete=models.CASCADE,null=True, blank= True,                   verbose_name="Người tạo")
    user_modified = models.CharField(max_length=150, blank=True, null=True,
                             verbose_name="Người chỉnh sửa")
    class Meta:
         verbose_name = 'Giao dịch tiền'
         verbose_name_plural = 'Giao dịch tiền'
    
    def __str__(self):
        return str(self.amount) 

class Transaction (models.Model):
    POSITION_CHOICES = [
        ('buy', 'Buy'),
        ('sell', 'Sell'),
    ]
    account = models.ForeignKey(Account,on_delete=models.CASCADE, null=False, blank=False, verbose_name = 'Tài khoản' )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name = 'Ngày tạo' )
    date = models.DateField( default=timezone.now,verbose_name = 'Ngày giao dịch' )
    modified_at = models.DateTimeField(auto_now=True, verbose_name = 'Ngày chỉnh sửa' )
    stock = models.ForeignKey(StockListMargin,on_delete=models.CASCADE, null=False, blank=False, verbose_name = 'Cổ phiếu')
    position = models.CharField(max_length=4, choices=POSITION_CHOICES, null=False, blank=False,verbose_name = 'Mua/Bán')
    price = models.FloatField(verbose_name = 'Giá')
    qty = models.IntegerField(verbose_name = 'Khối lượng')
    transaction_fee = models.FloatField( verbose_name= 'Phí giao dịch')
    tax = models.FloatField(default=0,verbose_name= 'Thuế')
    net_total_value = models.FloatField(default=0, verbose_name= 'Giá trị giao dịch')
    user_created = models.ForeignKey(User,on_delete=models.CASCADE,null=True, blank= True,                   verbose_name="Người tạo")
    user_modified = models.CharField(max_length=150, blank=True, null=True,
                             verbose_name="Người chỉnh sửa")
    

    class Meta:
         verbose_name = 'Sổ lệnh '
         verbose_name_plural = 'Sổ lệnh '

    def __str__(self):
        return self.stock.stock
    
    # def clean(self):
    #     if not self.account:
    #         raise ValidationError({'account': 'Vui lòng nhập tài khoản'})
    #     if self.position:
    #         if self.position == 'buy':
    #             if self.qty:
    #                 item = Transaction.objects.filter(account_id=self.account.pk).exclude(pk=self.pk)
    #                 total_trading = sum(i.total_value for i in item if i.status_raw == 'matched')
    #                 # cần cộng thêm giá trị deal mua đang chờ khớp
    #                 pending = sum(i.total_value for i in item if i.status_raw != 'matched' and i.position =='buy')
    #                 net_cash_available = self.account.net_cash_flow - total_trading -pending
    #                 if self.total_value > net_cash_available :
    #                     raise ValidationError({'qty': f'Không đủ sức mua, số lượng tối đa {net_cash_available:,.0f} cp'})
    #             else:
    #                 if not self.qty:
    #                     raise ValidationError({'qty': 'Vui lòng nhập số lượng hoặc giá cắt lỗ'})      
    #         elif self.position == 'sell':
    #             if not self.qty:
    #                 raise ValidationError({'qty': 'Vui lòng nhập số lượng'})
    #             else:
    #                 port = self.account.portfolio
    #                 qty_sell_pending = Transaction.objects.filter(account_id=self.account.pk,
    #                         status_raw = 'pending', position = 'sell').exclude(pk=self.pk).aggregate(Sum('qty'))['qty__sum'] or 0
    #                 item = next((item for item in port if item['stock'] == self.stock), None)
    #                 if not item:
    #                     raise ValidationError({'qty': 'Không có cổ phiếu để bán'})
    #                 max_sellable_qty = item['qty_sellable'] - qty_sell_pending
    #                 if self.qty > max_sellable_qty:
    #                     raise ValidationError({'qty': f'Không đủ cổ phiếu bán, tổng cổ phiếu khả dụng là {max_sellable_qty}'})
    #     else:
    #             raise ValidationError({'position': 'Vui lòng chọn "mua" hoặc "bán"'})
        
        
    def save(self, *args, **kwargs):
        total_value = self.price*self.qty
        self.transaction_fee = total_value*self.account.transaction_fee
        if self.position == 'buy':
            self.tax =0
        else:
            self.tax = total_value*self.account.tax
        self.net_total_value = total_value+self.transaction_fee+self.tax
        super(Transaction, self).save(*args, **kwargs)
        
     

    # @property
    # def str_total_value(self):
    #     if self.position =='buy':
    #         total = self.total_value
    #     else:
    #         total = -self.total_value
    #     return '{:,.0f}'.format(total)
    
    

    
    # @property
    # def date_stock_on_account(self):
    #     if self.status_raw == 'matched':
    #         time =self.time_received_stock
    #     else:
    #         time =None
    #     return time
    
class ExpenseStatement(models.Model):
    POSITION_CHOICES = [
        ('interest', 'interest'),
        ('transaction_fee', 'transaction_fee'),
        ('tax', 'tax'),
    ]
    account = models.ForeignKey(Account,on_delete=models.CASCADE, null=False, blank=False, verbose_name = 'Tài khoản' )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name = 'Ngày tạo' )
    modified_at = models.DateTimeField(auto_now=True, verbose_name = 'Ngày chỉnh sửa' )
    date =models.DateField( verbose_name = 'Ngày' )
    type =models.CharField(max_length=50, choices=POSITION_CHOICES, null=False, blank=False,verbose_name = 'Loại phí')
    amount = models.FloatField (verbose_name='Số tiền')
    description = models.CharField(max_length=100,null=True, blank=True, verbose_name='Diễn giải')
    class Meta:
         verbose_name = 'Bảng kê chi phí '
         verbose_name_plural = 'Bảng kê chi phí '

    def __str__(self):
        return str(self.type) + str('_')+ str(self.date)

class Portfolio (models.Model):
    account = models.ForeignKey(Account,on_delete=models.CASCADE, null=False, blank=False, verbose_name = 'Tài khoản' )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name = 'Ngày tạo' )
    modified_at = models.DateTimeField(auto_now=True, verbose_name = 'Ngày chỉnh sửa' )
    stock = models.CharField(max_length=10, verbose_name = 'Cổ phiếu')
    avg_price = models.FloatField(default=0,verbose_name = 'Giá')
    on_hold = models.IntegerField(default=0,null=True,blank=True,verbose_name = 'Khả dụng')
    receiving_t2 = models.IntegerField(default=0,null=True,blank=True,verbose_name = 'Chờ về T2')
    receiving_t1 = models.IntegerField(default=0,null=True,blank=True,verbose_name = 'Chờ về T1')
    cash_divident = models.FloatField(default=0,null=True,blank=True,verbose_name = 'Cổ tức bằng tiền')
    stock_divident =models.IntegerField(default=0,null=True,blank=True,verbose_name = 'Cổ tức cổ phiếu')
    market_price = models.FloatField(default=0,null=True,blank=True,verbose_name = 'Giá thị trường')
    profit = models.FloatField(default=0,null=True,blank=True,verbose_name = 'Lợi nhuận')
    percent_profit = models.FloatField(default=0,null=True,blank=True,verbose_name = '%Lợi nhuận')
    class Meta:
         verbose_name = 'Danh mục '
         verbose_name_plural = 'Danh mục '

    def __str__(self):
        return self.stock
    

def difine_date_receive_stock_buy(check_date):
    t=0
    while t <= 2 and check_date < datetime.now().date():  
        check_date = check_date + timedelta(days=1)
        weekday = check_date.weekday() 
        check_in_dates =  DateNotTrading.objects.filter(date=check_date).exists()
        if check_in_dates or weekday == 5 or weekday == 6:
            pass
        else:
            t += 1
    return t


@receiver([post_save, post_delete], sender=Transaction)
@receiver([post_save, post_delete], sender=CashTransfer)
def save_field_account(sender, instance, **kwargs):
    created = kwargs.get('created', False)
    account = instance.account
    if not created:
        if sender == Transaction:
            transaction_items = Transaction.objects.filter(account=account)
            total_trading_buy = sum(item.net_total_value for item in transaction_items if item.position == 'buy')
            total_trading_sell = sum(item.net_total_value for item in transaction_items if item.position == 'sell')
            account.net_trading_value = total_trading_sell - total_trading_buy
            #sửa sao kê phí
            expense_transaction_fee = ExpenseStatement.objects.get(description=instance.pk,type = 'transaction_fee')
            expense_transaction_fee.account=instance.account
            expense_transaction_fee.date=instance.date
            expense_transaction_fee.amount = instance.transaction_fee
            expense_transaction_fee.save()
            #sửa danh mục
            porfolio = Portfolio.objects.filter(account=instance.account, stock =instance.stock).first()
            stock_transaction = transaction_items.filter(stock = instance.stock)
            sum_sell = sum(item.qty for item in stock_transaction if item.position =='sell')
            item_buy = stock_transaction.filter( position = 'buy')
            receiving_t2 =0
            receiving_t1=0
            on_hold =0
            for item in item_buy:
                    if difine_date_receive_stock_buy(item.date) == 0:
                        receiving_t2 += item.qty
                    elif difine_date_receive_stock_buy(item.date) == 1:
                        receiving_t1 += item.qty
                    else:
                        on_hold += item.qty- sum_sell
            porfolio.receiving_t2 = receiving_t2
            porfolio.receiving_t1 = receiving_t1
            porfolio.on_hold = on_hold
            porfolio.save()
            # sửa sao kê thuế
            if instance.position=='sell':
                expense_tax = ExpenseStatement.objects.get(description=instance.pk,type = 'tax')
                expense_tax.account=instance.account
                expense_tax.date=instance.date
                expense_tax.amount = instance.tax
                expense_tax.save()
                
            
        
            
        elif sender == CashTransfer:
            cash_items = CashTransfer.objects.filter(account=account)
            account.net_cash_flow = sum(item.amount for item in cash_items)
            
    else:
        if sender == Transaction:
            #tạo sao kê phí giao dịch
            ExpenseStatement.objects.create(
                account=instance.account,
                date=instance.date,
                type = 'transaction_fee',
                amount = instance.transaction_fee,
                description = instance.pk
                )
            porfolio = Portfolio.objects.filter(account=instance.account, stock =instance.stock).first()
            if instance.position =='buy':
                account.net_trading_value =  account.net_trading_value -instance.net_total_value
                # tạo danh mục
                if porfolio:
                    sum_qty = porfolio.on_hold + porfolio.receiving_t2 + porfolio.receiving_t1 #+ porfolio.stock_divident
                    porfolio.receiving_t2 = porfolio.receiving_t2 + instance.qty 
                    porfolio.avg_price=round((instance.qty*instance.price +sum_qty*porfolio.avg_price)/(sum_qty+instance.qty),0)  # Thay đổi giá trị nếu cần
                    
                    
                else: 
                    Portfolio.objects.create(
                    stock=instance.stock,
                    account= instance.account,
                    receiving_t2 = instance.qty ,
                    avg_price = instance.price ,
    
                    )
                
            else:
                account.net_trading_value = instance.net_total_value + account.net_trading_value
                # tạo sao kê thuế
                ExpenseStatement.objects.create(
                account=instance.account,
                date=instance.date,
                type = 'tax',
                amount = instance.tax,
                description = instance.pk
                )
                # điều chỉnh danh mục
                porfolio.on_hold = porfolio.on_hold -instance.qty
            porfolio.save()

        elif sender == CashTransfer:
            account.net_cash_flow = account.net_cash_flow + instance.amount
    account.cash_balance = account.net_cash_flow + account.net_trading_value #- lãi vay 
    
    account.save()


@receiver(post_delete, sender=Transaction)
def delete_expense_statement(sender, instance, **kwargs):
    expense = ExpenseStatement.objects.filter(description=instance.pk)
    # porfolio = Portfolio.objects.filter(account=instance.account, stock =instance.stock).first()
    if expense:
        expense.delete()
    # if porfolio:
    #     if instance.date =
    #     porfolio.receiving_t2
    #     porfolio.receiving_t1
    #     porfolio.on_hold
    #     avg_price

    