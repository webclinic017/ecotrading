from django.db import models
from django.db.models.signals import post_save, post_delete,pre_save, pre_delete
from django.contrib.auth.models import User
from django.dispatch import receiver
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup
from portfolio.models import DateNotTrading, StockPriceFilter

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
    cash_t1 = models.FloatField(default=0,verbose_name= 'Sơ dư tiền T1')
    cash_t2= models.FloatField(default=0,verbose_name= 'Sơ dư tiền T2')
    interest_cash_balance= models.FloatField(default=0,verbose_name= 'Sơ dư tiền tính lãi')

    
    class Meta:
         verbose_name = 'Tài khoản'
         verbose_name_plural = 'Tài khoản'

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        self.cash_balance = self.net_cash_flow + self.net_trading_value #- lãi vay 
        stock_mapping = {obj.stock: obj.initial_margin_requirement  for obj in StockListMargin.objects.all()}
        port = Portfolio.objects.filter(account =self.pk)
        sum_initial_margin = 0
        self.margin_ratio = 0
        market_value = 0
        if port:
            for item in port:
                initial_margin = stock_mapping.get(item.stock, 0)*item.sum_stock*item.avg_price/100
                sum_initial_margin +=initial_margin
                value = item.sum_stock*item.market_price
                market_value += value
                self.market_value = market_value
        self.nav = self.market_value + self.cash_balance
        self.initial_margin_requirement = sum_initial_margin
        self.excess_equity = self.nav - self.initial_margin_requirement
        if sum_initial_margin >0:
            self.margin_ratio = (self.nav/self.initial_margin_requirement)*100
        super(Account, self).save(*args, **kwargs)
    

   
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
    total_value= models.FloatField(default=0, verbose_name= 'Giá trị giao dịch')
    net_total_value = models.FloatField(default=0, verbose_name= 'Giá trị giao dịch ròng')
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
        self.total_value = self.price*self.qty
        self.transaction_fee = self.total_value*self.account.transaction_fee
        if self.position == 'buy':
            self.tax =0
            self.net_total_value = -self.total_value-self.transaction_fee-self.tax
        else:
            self.tax = self.total_value*self.account.tax
            self.net_total_value = self.total_value-self.transaction_fee-self.tax
        
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
    sum_stock =models.IntegerField(default=0,null=True,blank=True,verbose_name = 'Tổng cổ phiếu')
    class Meta:
         verbose_name = 'Danh mục '
         verbose_name_plural = 'Danh mục '

    def __str__(self):
        return self.stock
    
    def save(self, *args, **kwargs):
        self.sum_stock = self.receiving_t2+ self.receiving_t1+self.on_hold
        self.profit =0
        self.percent_profit = 0
        if self.sum_stock >0:
            self.market_price = round(get_stock_market_price(str(self.stock)),0)
            self.avg_price = round(cal_avg_price(self.account.pk,self.stock)*1000,0)
            self.profit = round((self.market_price - self.avg_price)*self.sum_stock,0)
            self.percent_profit = round((self.market_price/self.avg_price-1)*100,2)
            
            
        super(Portfolio, self).save(*args, **kwargs)

        
    

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

def cal_avg_price(pk,stock):
    item = Transaction.objects.filter(account_id=pk, stock__stock = stock ) 
    total_buy = sum(i.qty for i in item if i.position =='buy' )
    total_sell =sum(i.qty for i in item if i.position =='sell' )
    total_value = sum(i.total_value for i in item if i.position =='buy' )
    date_list =list(item.filter(position ='sell').values_list('date', flat=True).distinct()) 
    avg_price = 0
    date_find=None

    #kiểm tra có bán hay không, trường hợp đã có bán
    if total_sell >0:
        date_list.sort(reverse=True) 
        
        # kiểm tra ngày gần nhất bán hết và mua lại
        for date_check in date_list: 
            new_item = item.filter(date__lte =date_check)
            check_total_buy = 0
            check_total_sell =0
            for i in new_item:
                if i.position == 'buy':
                    check_total_buy += i.qty 
                else:
                    check_total_sell +=i.qty
            if check_total_buy == check_total_sell:
                date_find = i.date
                break 
        if date_find:
            cal_item = item.filter(position='buy',date__gt= date_find )
            for i in cal_item:
                if i.position =='buy':
                    total_buy += i.qty 
                    total_value +=i.total_value
                    avg_price = total_value/total_buy/1000
                    
        else:
            avg_price = total_value/total_buy/1000
    # Nếu có mua nhưng chưa bán lệnh nào
    elif total_buy >0:
        avg_price = total_value/total_buy/1000
    return avg_price



def get_stock_market_price(stock):
    linkbase= 'https://www.cophieu68.vn/quote/summary.php?id=' + stock 
    r =requests.get(linkbase)
    soup = BeautifulSoup(r.text,'html.parser')
    div_tag = soup.find('div', id='stockname_close')
    return float(div_tag.text)*1000

@receiver([post_save, post_delete], sender=Transaction)
@receiver([post_save, post_delete], sender=CashTransfer)
def save_field_account(sender, instance, **kwargs):
    created = kwargs.get('created', False)
    account = instance.account
    port = Portfolio.objects.filter(account = instance.account, sum_stock__gt=0)
    if not created:
        if sender == Transaction:
            transaction_items = Transaction.objects.filter(account=account)
            account.net_trading_value = sum(item.net_total_value for item in transaction_items)
            
            #sửa sao kê phí
            expense_transaction_fee = ExpenseStatement.objects.get(description=instance.pk,type = 'transaction_fee')
            expense_transaction_fee.account=instance.account
            expense_transaction_fee.date=instance.date
            expense_transaction_fee.amount = instance.transaction_fee
            expense_transaction_fee.save()
            #sửa danh mục
            porfolio = port.filter(stock =instance.stock).first()
            stock_transaction = transaction_items.filter(stock = instance.stock)
            sum_sell = sum(item.qty for item in stock_transaction if item.position =='sell')
            item_buy = stock_transaction.filter( position = 'buy')
            item_sell = stock_transaction.filter( position = 'sell')
            if porfolio:
                receiving_t2 =0
                receiving_t1=0
                on_hold =0
                cash_t2 = 0
                cash_t1 = 0
                cash_t0= 0
                
                for item in item_buy:
                    if difine_date_receive_stock_buy(item.date) == 0:
                            receiving_t2 += item.qty
                            cash_t2 += item.net_total_value 
                    elif difine_date_receive_stock_buy(item.date) == 1:
                            receiving_t1 += item.qty
                            cash_t1+= item.net_total_value 
                    else:
                            on_hold += item.qty- sum_sell
                            cash_t0 += item.net_total_value 
                
                for item in item_sell:
                    if difine_date_receive_stock_buy(item.date) == 0:
                        cash_t2 += item.net_total_value 
                    elif difine_date_receive_stock_buy(item.date) == 1:
                        cash_t1+= item.net_total_value 
                    else:
                        cash_t0 += item.net_total_value 

                porfolio.receiving_t2 = receiving_t2
                porfolio.receiving_t1 = receiving_t1
                porfolio.on_hold = on_hold
                # porfolio.avg_price = cal_avg_price(instance.account.pk,instance.stock.stock)*1000
                # porfolio.sum_stock = receiving_t2+ receiving_t1+on_hold
                # porfolio.market_price = get_stock_market_price(instance.stock.stock)
                # porfolio.profit = (porfolio.market_price - porfolio.avg_price)*porfolio.sum_stock
                # porfolio.percent_profit = round((porfolio.market_price/porfolio.avg_price-1)*100,2)
                account.cash_t2 = cash_t2
                account.cash_t1 = cash_t1
                account.interest_cash_balance += cash_t0  
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
            porfolio = port.filter(stock =instance.stock).first()
            if instance.position =='buy':
                account.net_trading_value =  account.net_trading_value +instance.net_total_value
                # tăng tiền số dư tính lãi
                account.interest_cash_balance += instance.net_total_value
                # tạo danh mục
                if porfolio:
                    # porfolio.avg_price=round((instance.qty*instance.price +porfolio.sum_stock*porfolio.avg_price)/(porfolio.sum_stock+instance.qty),0)  # Thay đổi giá trị nếu cần
                    porfolio.receiving_t2 = porfolio.receiving_t2 + instance.qty 
                    # porfolio.sum_stock = porfolio.sum_stock + instance.qty #+ porfolio.stock_divident
                    # porfolio.market_price = get_stock_market_price(instance.stock.stock)
                    # porfolio.profit = (porfolio.market_price - porfolio.avg_price)*porfolio.sum_stock
                    # porfolio.percent_profit = round((porfolio.market_price/porfolio.avg_price-1)*100,2)
                    porfolio.save()
                else: 
                    Portfolio.objects.create(
                    stock=instance.stock,
                    account= instance.account,
                    receiving_t2 = instance.qty ,
                    avg_price = instance.price ,
                    sum_stock = instance.qty,
                    market_price = get_stock_market_price(instance.stock.stock),
                    )
                
            else:
                account.net_trading_value += instance.net_total_value 
                # chuyển tiền bán vào tiền chờ về T2
                account.cash_t2 +=  instance.net_total_value
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
            account.net_cash_flow += + instance.amount
    # tính hiện trạng tài khoản
    # account.cash_balance = account.net_cash_flow + account.net_trading_value #- lãi vay 
    
    
    # stock_mapping = {obj.stock: obj.initial_margin_requirement  for obj in StockListMargin.objects.all()}
    # sum_initial_margin = 0
    # market_value = 0
    # for item in port:
    #     initial_margin = stock_mapping.get(item.stock, 0)*item.sum_stock*item.avg_price/100
    #     sum_initial_margin +=initial_margin
    #     value = item.sum_stock*item.market_price
    #     market_value += value

    # if port:
    #     account.market_value = market_value
    #     account.nav = account.market_value + account.cash_balance
    #     account.initial_margin_requirement = sum_initial_margin
    #     account.margin_ratio = (account.nav/account.initial_margin_requirement)*100
    #     account.excess_equity = account.nav - account.initial_margin_requirement
    account.save()


@receiver(post_delete, sender=Transaction)
def delete_expense_statement(sender, instance, **kwargs):
    expense = ExpenseStatement.objects.filter(description=instance.pk)
    # porfolio = Portfolio.objects.filter(account=instance.account, stock =instance.stock).first()
    if expense:
        expense.delete()
   

@receiver (post_save, sender=StockPriceFilter)
def update_market_price_port(sender, instance, created, **kwargs):
    port = Portfolio.objects.filter(sum_stock__gt=0, stock =instance.stock)
    for item in port:
        if item.stock == instance.ticker:
            item.market_price = instance.close*1000
            # item.profit = (item.market_price - item.avg_price)*item.sum_stock
            # item.percent_profit = round((item.market_price/item.avg_price-1)*100,2)
            item.save()
            
            
            
                

           

            

    
        



#chạy 1 phút 1 lần
def update_market_price_for_port():
    port = Portfolio.objects.filter(sum_stock__gt=0)
    for item in port:
        item.market_price = get_stock_market_price(item.stock)
        # item.profit = (item.market_price - item.avg_price)*item.sum_stock
        # item.percent_profit = round((item.market_price/item.avg_price-1)*100,2)
        item.save()

def morning_check():
    #kiểm tra vào tính lãi suất
    account = Account.objects.filter(interest_cash_balance__lt=0)
    if account:
        for instance in account:
            ExpenseStatement.objects.create(
                account=instance,
                date=datetime.now().date(),
                type = 'interest',
                amount = instance.interest_fee * instance.interest_cash_balance/360,
                description = instance.pk
                )
    # chuyển tiền dồn lên 1 ngày
        account.interest_cash_balance += account.cash_t1
        account.cash_t1= account.cash_t2
        account.cash_t2 =0
        account.save()

def atternoon_check():
    port = Portfolio.objects.filter(sum_stock__gt=0)
    buy_today = Transaction.objects.filter(position ='buy',date = datetime.now().date())
    qty_buy_today = sum(item.qty for item in buy_today )
    if port:
        port.on_hold += port.receiving_t1
        port.receiving_t1 = port.receiving_t2
        port.receiving_t2 = qty_buy_today
        port.save()

    
    