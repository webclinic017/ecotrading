from django.db import models
from django.contrib.auth.models import User
from django.db.models import Max, Min
from datetime import datetime, timedelta, time
from django.db.models.signals import pre_save
from django.core.exceptions import PermissionDenied
from django.db.models import Sum, Q, F, IntegerField
from django.db.models.functions import Coalesce
import requests
from bs4 import BeautifulSoup
import json
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.dispatch import receiver





#lấy giá cổ phiếu
def get_all_info_stock_price():
    boardname = ['HOSE','HNX','UPCOM']
    linkstocklist='https://price.tpbs.com.vn/api/StockBoardApi/getStockList'
    linkstockquote ='https://price.tpbs.com.vn/api/SymbolApi/getStockQuote'
    stock_list =[]
    for i in boardname:
        r1= requests.post(linkstocklist,json =  {"boardName":i})
        k=json.loads(r1.text)
        list =json.loads(k['content'])
        stock_list= stock_list+list
    r = requests.post(linkstockquote,json = {"stocklist" : stock_list})
    b= json.loads(r.text)
    a = json.loads(b['content'])
    result = []
    date_time = datetime.now()
    date_time = difine_time_craw_stock_price(date_time)
    for i in range (0,len(a)):
        ticker=a[i]['sym']
        low_price=float(a[i]['low'])
        high_price = float(a[i]['hig'])
        match_price=float(round(float(a[i]['mat'])*1000,0))
        volume=float(a[i]['tmv'].replace(',', '') )*10
        StockPrice.objects.update_or_create(
                ticker=ticker,
                date= date_time.date(),
            defaults={
            'low_price': low_price,
            'high_price': high_price,
            'match_price': match_price,
            'volume': volume,
            'date_time':date_time
                        } )
    return StockPrice.objects.all()

def get_list_stock_price():
    list_stock = list(Transaction.objects.values_list('stock', flat=True).distinct())
    number =len(list_stock)
    linkstockquote ='https://price.tpbs.com.vn/api/SymbolApi/getStockQuote'
    r = requests.post(linkstockquote,json = {"stocklist" : list_stock })
    b= json.loads(r.text)
    a = json.loads(b['content'])
    date_time = datetime.now()
    date_time = difine_time_craw_stock_price(date_time)
    for i in range (0,len(a)):
        ticker=a[i]['sym']
        low_price=float(a[i]['low'])
        high_price = float(a[i]['hig'])
        match_price=float(round(float(a[i]['mat'])*1000,0))
        volume=float(a[i]['tmv'].replace(',', '') )*10
        StockPrice.objects.update_or_create(
                ticker=ticker,
                date= date_time.date(),
            defaults={
            'low_price': low_price,
            'high_price': high_price,
            'match_price': match_price,
            'volume': volume,
            'date_time':date_time
                        } )
    return StockPrice.objects.all().order_by('-date_time')[:number]

# tìm thời điểm mốc ban đầu, thời điểm mua lần đầu
def avg_price(pk,stock,start_date,end_date):
    start_date = end_date - timedelta(days = 10*365)
    item = Transaction.objects.filter(account_id=pk, stock = stock) 
    total_buy = 0
    total_sell =0
    total_value =0
    date_list =[]
    avg_price = None
    date_find=None
    for order in item:
        if order.status == 'matched' and order.time_matched >=start_date and order.time_matched <= end_date:
            if order.position =='buy':
                total_buy +=order.qty
                total_value += order.total_value
            else:
                total_sell +=order.qty
                date_list.append(order.time_matched)
    #kiểm tra có bán hay không, trường hợp đã có bán
    if total_sell >0:
        date_list.sort(reverse=True) 
        # kiểm tra ngày gần nhất bán hết và mua lại
        for date in date_list: 
            total_buy = 0
            total_sell =0     
            for i in item: 
                if i.status == 'matched' and i.date_stock_on_account >=start_date and i.date_stock_on_account <= date:
                    if i.position =='buy':
                        total_buy += i.qty 
                    else:
                        total_sell += i.qty
                if total_buy == total_sell:
                    date_find = i.time_matched
                    break 
        if date_find:
            total_buy = 0
            total_sell =0 
            total_value =0
            for i in item: 
                if i.status == 'matched' and i.position=='buy' and i.time_matched > date_find and i.time_matched < end_date:
                    total_value +=i.total_value
                    total_buy +=i.qty
                    avg_price = total_value/total_buy
        else:
            avg_price = total_value/total_buy
    # Nếu có mua nhưng chưa bán lệnh nào
    elif total_buy >0:
        avg_price = total_value/total_buy 
    return avg_price

#xác định danh mục cổ phiếu đã về
def qty_stock_available(pk,stock, start_date,end_date):
    end_date = datetime.now()
    start_date = end_date - timedelta(days = 10*365)
    item = Transaction.objects.filter(account_id=pk, stock = stock) 
    total_buy = 0
    total_sell =0
    for i in item:
        if i.status == 'matched' and i.date_stock_on_account >=start_date and i.date_stock_on_account <= end_date:
            if i.position == 'buy':
                total_buy += i.qty
            else:
                total_sell += i.qty
    return total_buy -total_sell

def filter_order_mathched(pk):
    item = Transaction.objects.filter(account_id=pk) 
    order_list = Transaction.objects.none()   
    for i in item:
        if i.status == 'matched':
            order_list |= Transaction.objects.filter(pk=i.pk)
    return order_list

#Xác định danh mục cổ phiếu đã mua, bao gồm chờ về
def qty_stock_on_account(pk):
    port_raw = []
    port_str = []
    order_list = filter_order_mathched(pk)
    if order_list:
        new_order = order_list.filter(account_id=pk).values('stock').annotate(
            total_buy_qty=Coalesce(Sum('qty', filter=Q(position='buy')), 0),
            total_sell_qty=Coalesce(Sum('qty', filter=Q(position='sell')), 0)
            ).annotate(
            qty=F('total_buy_qty') - F('total_sell_qty')
            ).exclude(qty=0).values('stock', 'qty')
        
        for i in new_order:
                stock = i['stock']
                qty_total = i['qty']
                end_date = datetime.now()
                start_date = end_date - timedelta(days = 10*365)
                avgprice = avg_price(pk,stock,start_date,end_date)
                qty_sellable =qty_stock_available(pk,stock, start_date,end_date)
                qty_receiving = qty_total -qty_sellable
                item_sell = Transaction.objects.filter(account_id = pk,position ='sell', stock =stock )
                qty_sell_pending = sum(i.qty for i in item_sell if i.status =='pending')
                market_price = StockPrice.objects.filter(ticker = stock).order_by('-date_time').first().match_price     
                profit = qty_total*(market_price-avgprice)
                ratio_profit = (market_price/avgprice-1)*100
                port_raw.append({'stock': stock,'qty_total':qty_total, 'qty_sellable': qty_sellable, 
                                        'qty_receiving': qty_receiving,'qty_sell_pending':qty_sell_pending,
                                        'avg_price':avgprice, 'market_price':market_price,
                                        'profit':profit,'ratio_profit':ratio_profit
                                        })
                port_str.append({'stock': stock,'qty_total':'{:,.0f}'.format(qty_total), 
                                        'qty_sellable': '{:,.0f}'.format(qty_sellable), 
                                        'qty_receiving': '{:,.0f}'.format(qty_receiving),
                                        'qty_sell_pending':'{:,.0f}'.format(qty_sell_pending),
                                        'avg_price':'{:,.0f}'.format(avgprice), 
                                        'market_price':'{:,.0f}'.format(market_price),
                                        'profit':'{:,.0f}'.format(profit),'ratio_profit':str(round(ratio_profit,2))+str('%')})
    return port_raw, port_str



#Tính ngày khớp lệnh
def difine_time_craw_stock_price(date_time):
    date_item = DateNotTrading.objects.filter(date__gte=date_time)
    weekday = date_time.weekday()
    old_time = date_time.time()
    date_time=date_time.date()
    if weekday == 6:  # Nếu là Chủ nhật
        date_time = date_time - timedelta(days=2)  # Giảm 2 ngày
    elif weekday == 5:  # Nếu là thứ 7
        date_time = date_time - timedelta(days=1)  # Giảm 1 ngày
    weekday = date_time.weekday()
    while True:
        if date_time in date_item or weekday == 6 or weekday == 5 :  # Nếu là một ngày trong danh sách không giao dịch
            date_time = date_time - timedelta(days=1)  # Giảm về ngày liền trước đó
        else:
            break
        weekday = date_time.weekday()  # Cập nhật lại ngày trong tuần sau khi thay đổi time
    if old_time < time(14, 45, 0) and old_time > time(9, 00, 0):
        new_time = old_time
    else:
        new_time = time(14, 45, 0)
    return datetime.combine(date_time, new_time)

#Tính ngày cổ phiếu về tài khoản
def difine_date_stock_on_account(time_matched):
    weekday = time_matched.weekday()
    time_matched=time_matched.date()
    new_time = time(12, 00, 0) #thời gian hàng về 
    if weekday ==4: # nếu là thứ 6
        time_matched = time_matched + timedelta(days=4)
        weekday = time_matched.weekday()
    else: #các ngày còn lại trong tuần
        time_matched = time_matched + timedelta(days=2)
        weekday = time_matched.weekday()
    while True: #check có trùng ngày lễ không
        if weekday == 5 or weekday == 6 or DateNotTrading.objects.filter(date=time_matched).exists()  :  # Nếu là thứ 7, chủ nhật, lễ
                time_matched = time_matched + timedelta(days=1)  # cộng 1 ngày
        else:
            break
        weekday = time_matched.weekday()  # Cập nhật lại ngày trong tuần sau khi thay đổi time
    
    return  datetime.combine(time_matched, new_time)
    
    

# Tính thời gian sau cùng lệnh vào
def define_date(date1, date2):
    if date2:
        if date1>date2:
            return date1
        else:
            return date2
    else:
        return date1

def cal_profit_deal_close(pk):
    item = Transaction.objects.filter(account_id=pk,position ='sell' )
    deal_close = []
    str_deal_close = []
    for i in item:
        if i.status == 'matched':
            new_end_date = i.time_matched -timedelta(minutes=1)
            end_date = datetime.now()
            start_date = end_date - timedelta(days = 10*365)
            avgprice = avg_price(pk,i.stock,start_date,new_end_date)
            profit = i.qty*(i.price*1000 -avgprice )
            ratio_profit = (i.price*1000/avgprice-1)*100
            deal_close.append({'stock':i.stock,'date':i.time_matched,'qty': i.qty,
                               'price':i.price*1000,'avg_price':avgprice,
                               'profit':profit,'ratio_profit':ratio_profit})
            str_deal_close.append({'stock':i.stock,'date':i.time_matched,'qty': '{:,.0f}'.format(i.qty),
                               'price':'{:,.0f}'.format(i.price*1000),'avg_price':'{:,.0f}'.format(avgprice),
                               'profit':'{:,.0f}'.format(profit),'ratio_profit':str(round(ratio_profit,2))+str('%')})
    return deal_close, str_deal_close


def check_status_order(pk):
        self = Transaction.objects.get(pk=pk)
        date = define_date(self.created_at, self.modified_at)
        time = None
        time_received_stock =None
        if self.position == 'buy':
            stock_price = StockPrice.objects.filter(
                ticker=self.stock,
                date_time__gte=date,
                match_price__lte=self.price*1000,
                volume__gte=self.qty*5).order_by('date_time')
            if stock_price:
                status = 'matched'
                time = stock_price.first().date_time
                time_received_stock = difine_date_stock_on_account(time)
            else:
                status = 'pending'
        else:
            stock_price = StockPrice.objects.filter(
                ticker=self.stock,
                date_time__gte=date,
                match_price__gte=self.price*1000,
                volume__gte=self.qty*5).order_by('date_time')
            if stock_price:
                status = 'matched'
                time = stock_price.first().date_time
                time_received_stock = time
            else:
                status = 'pending'
                
        if status == 'matched':
            self.status_raw = status
            self.time_matched_raw = time
            self.time_received_stock = time_received_stock
            self.save()
        return status, time, time_received_stock

# tính giá trung bình danh mục



    
class BotTelegram (models.Model):
    name = models.CharField(max_length=50, unique=True)
    token = models.CharField(max_length=100, unique=True)
    chat_id = models.CharField(max_length=50, unique=True)
    description = models.TextField(max_length=255, blank=True)
    owner = models.ForeignKey(User,on_delete=models.CASCADE )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name = 'Ngày tạo' )
    modified_at = models.DateTimeField(auto_now=True, verbose_name = 'Ngày chỉnh sửa' )
    def __str__(self):
        return self.name


# Create your models here.
class Account (models.Model):
    name = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name = 'Ngày tạo' )
    modified_at = models.DateTimeField(auto_now=True, verbose_name = 'Ngày chỉnh sửa' )
    description = models.TextField(max_length=255, blank=True)
    owner = models.ForeignKey(User,on_delete=models.CASCADE )
    ratio_risk = models.FloatField(default=0.03)
    transaction_fee = models.FloatField(default=0.0015)
    tax = models.FloatField(default=0.001)
    bot = models.ForeignKey(BotTelegram,on_delete=models.CASCADE )
    

    


    # class Meta:
    #     verbose_name = 'Tài khoản'
    #     verbose_name_plural = 'Tài khoản'

    def __str__(self):
        return self.name
    @property
    def portfolio(self):
        return qty_stock_on_account(self.pk)[0]
    @property
    def str_portfolio(self):
        return qty_stock_on_account(self.pk)[1]

    
    @property
    def net_cash_flow(self):
        item = CashTrasfer.objects.filter(account_id =self.pk)
        total = sum(i.amount for i in item )
        return total
    @property
    def net_cash_available(self):
        order_list = filter_order_mathched(self.pk)
        total_trading = sum(i.total_value for i in order_list)
        # cần cộng thêm giá trị deal mua đang chờ khớp
        item = Transaction.objects.filter(account_id = self.pk,position ='buy')
        pending = sum(i.total_value for i in item if i.status =='pending')
        net_cash_available = self.net_cash_flow - total_trading -pending
        return net_cash_available
    
    @property
    def market_value(self):
        port = self.portfolio
        market_value = sum(item['qty_total']*item['market_price'] for item in port)
        return market_value
    

    @property
    def total_profit(self):
        order_list = filter_order_mathched(self.pk)
        total_trading = sum(i.total_value for i in order_list)
        net_cash_available = self.net_cash_flow - total_trading
        total = net_cash_available+ self.market_value -self.net_cash_flow 
        return total
    @property
    def close_deal(self):
        close_deal= cal_profit_deal_close(self.pk )
        return close_deal
    @property
    def total_profit_close(self):
        total_profit_close = sum(i['profit'] for i in self.close_deal[0])
        return total_profit_close

    @property
    def total_profit_open(self):
        total_profit_open = sum(i['profit'] for i in self.portfolio)
        return total_profit_open

class StockPrice(models.Model):
    ticker = models.CharField(max_length=10)
    low_price = models.FloatField()
    high_price =models.FloatField()
    match_price = models.FloatField()
    volume =models.FloatField()
    date = models.DateField(auto_now_add=True)
    date_time = models.DateTimeField(default=datetime.now)
    def __str__(self):
        return str(self.ticker) + str(self.match_price)


#lấy danh sách mã chứng khoán, top 500 thanh khoản
stock = StockPrice.objects.all().order_by('-date_time','-volume')
LIST_STOCK = []
for item in stock[:500]:
    stock = item.ticker
    LIST_STOCK.append((stock,stock))
    LIST_STOCK.sort()

 
 
class Transaction (models.Model):
    
    POSITION_CHOICES = [
        ('buy', 'Buy'),
        ('sell', 'Sell'),
    ]
    account = models.ForeignKey(Account,on_delete=models.CASCADE, null=False, blank=False )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name = 'Ngày tạo' )
    modified_at = models.DateTimeField(auto_now=True, verbose_name = 'Ngày chỉnh sửa' )
    stock = models.CharField(max_length=8, choices=LIST_STOCK, null=False, blank=False)
    position = models.CharField(max_length=4, choices=POSITION_CHOICES, null=False, blank=False)
    price = models.FloatField()
    qty = models.IntegerField(null=True,blank=True)
    cut_loss_price = models.FloatField(null=True,blank=True)
    buy_code = models.IntegerField(default=0)
    take_profit_price = models.FloatField(null=True,blank=True)
    status_raw = models.CharField(max_length=10, null=True,blank=True)
    time_matched_raw = models.DateTimeField(null=True,blank=True)
    time_received_stock = models.DateTimeField(null=True,blank=True)
 

    def __str__(self):
        return self.position + str("_") + self.stock
    
    # def clean(self):
    #     if not self.account:
    #         raise ValidationError({'account': 'Vui lòng nhập tài khoản'})

    #     if self.position == 'buy':
    #         if not self.cut_loss_price and not self.qty:
    #             raise ValidationError({'qty': 'Vui lòng nhập số lượng hoặc giá cắt lỗ'})
    #         elif self.cut_loss_price:
    #             if self.cut_loss_price < 0 or self.cut_loss_price >= self.price:
    #                 raise ValidationError({'cut_loss_price': 'Giá cắt lỗ phải lớn hơn 0 và nhỏ hơn giá mua'})
    #             elif self.qty:
    #                 max_qty = self.account.net_cash_available / (self.price * 1000)
    #                 if self.qty > max_qty:
    #                     raise ValidationError({'qty': f'Không đủ sức mua, số lượng tối đa {max_qty:,.0f} cp'})
    #         else:
    #             if not self.qty:
    #                 raise ValidationError({'qty': 'Vui lòng nhập số lượng'})

    #     elif self.position == 'sell':
    #         if not self.qty:
    #             raise ValidationError({'qty': 'Vui lòng nhập số lượng'})
    #         else:
    #             port = self.account.portfolio
    #             item = next((item for item in port if item['stock'] == self.stock), None)
    #             if not item:
    #                 raise ValidationError({'qty': 'Không có cổ phiếu để bán'})
    #             max_sellable_qty = item['qty_sellable'] - item['qty_sell_pending']
    #             if self.qty > max_sellable_qty:
    #                 raise ValidationError({'qty': f'Không đủ cổ phiếu bán, tổng cổ phiếu khả dụng là {max_sellable_qty}'})
    #     else:
    #         raise ValidationError({'position': 'Vui lòng chọn "mua" hoặc "bán"'})

    

            

    # def save(self, *args, **kwargs):
    #     if self.position == 'buy':
    #         risk = self.account.ratio_risk
    #         nav = self.account.net_cash_flow +self.account.total_profit_close
    #         R = risk*nav
    #         if self.cut_loss_price ==None or self.cut_loss_price <0:
    #             cut_loss_price  = self.price - R/(self.qty*1000)
    #             if cut_loss_price >0:
    #                 self.cut_loss_price = cut_loss_price
    #                 self.take_profit_price = round(self.price + 4*(self.price - self.cut_loss_price),2)
    #             else:
    #                 self.cut_loss_price == None
    #         elif self.cut_loss_price and self.cut_loss_price >0:
    #             if self.qty == 0 or self.qty ==None:
    #                 self.qty = R/((self.price -self.cut_loss_price)*1000)
    #                 self.take_profit_price = round(self.price + 4*(self.price - self.cut_loss_price),2)
        
    #     try:
    #         self.full_clean()
    #     except ValidationError as e:
    #         max_qty = round(self.account.net_cash_available/(self.price*1000),0)
    #         max_cutloss_price = round(self.price - R/(max_qty*1000),2)
    #         if max_cutloss_price <= 0:
    #             raise ValidationError('Không thể thực hiện giao dịch theo nguyên tắc quản trị vốn, bạn có thể nhập khối lượng để mua')
    #         else:
    #             raise ValidationError(f'Không đủ sức mua, có thể điều chỉnh số lượng tối đa {max_qty} cp, hoặc có thể giảm giá cắt lỗ nhỏ hơn {max_cutloss_price}'
    #                      )
    #     else:
    #         # Lưu đối tượng nếu không có lỗi
    #         super(Transaction, self).save(*args, **kwargs)
        
        

    @property
    def total_value(self):
        if self.price and self.qty:
            if self.position =='buy':
                total = self.price*self.qty*1000*(1+self.account.transaction_fee)
            else:
                total = -self.price*self.qty*1000*(1+self.account.transaction_fee +self.account.tax) 
        else:
            total =0                                                                                                                                                         
        return total
    @property
    def str_total_value(self):
        if self.position =='buy':
            total = self.total_value
        else:
            total = -self.total_value
        return '{:,.0f}'.format(total)
    
    @property
    def status(self):
        if self.status_raw == 'matched':
            return self.status_raw
        else:
            status = check_status_order(self.pk)[0]
            return status

    @property
    def time_matched(self):
        if self.status_raw == 'matched':
            time =  self.time_matched_raw
        else:
            time =None
        return time


    
    @property
    def date_stock_on_account(self):
        if self.status_raw == 'matched':
            time =self.time_received_stock
        else:
            time =None
        return time
        


# @receiver(post_save, sender=StockPrice)
# def create_sell_transaction(sender, instance, created, **kwargs):
#     if not created:
#         # Get the latest buy Transactions for this stock
#         buys_cutloss = Transaction.objects.filter(
#             stock=instance.ticker, 
#             position='buy', 
#             cut_loss_price__gte=instance.match_price/10000,   
#         )
#         buys_take_profit = Transaction.objects.filter(
#              stock=instance.ticker, 
#              position='buy', 
#              take_profit_price__lte =instance.match_price/10000,  
#              take_profit_price__gt=0 
#         )
#         sells = Transaction.objects.filter(stock=instance.ticker, position='sell').values_list('buy_code', flat=True)
#         # Check if the cut_loss_price is greater than the match_price
#         if buys_cutloss: 
#             for buy in buys_cutloss:
#                 account = Account.objects.get(pk=buy.account.pk)
#                 port = account.portfolio
#                 for item in port:
#                     if item['stock'] == buy.stock:
#                         new_qty_saleable = item['qty_sellable'] - item['qty_sell_pending']
#                         if buy.time_matched and buy.date_stock_on_account <= instance.date_time and buy.qty <=new_qty_saleable and buy.pk not in sells:
#                             sell = Transaction.objects.create(
#                                 account=buy.account,
#                                 stock=buy.stock,
#                                 position='sell',
#                                 price=buy.cut_loss_price,
#                                 qty=buy.qty,
#                                 cut_loss_price=0,
#                                 buy_code=buy.pk)
#         elif buys_take_profit:
#             for buy in buys_take_profit:
#                 account = Account.objects.get(pk=buy.account.pk)
#                 port = account.portfolio
#                 for item in port:
#                     if item['stock'] == buy.stock:
#                         new_qty_saleable = item['qty_sellable'] - item['qty_sell_pending']
#                         if buy.time_matched and buy.date_stock_on_account <= instance.date_time and buy.qty <= new_qty_saleable and buy.pk not in sells:
#                             sell = Transaction.objects.create(
#                                 account=buy.account,
#                                 stock=buy.stock,
#                                 position='sell',
#                                 price=buy.take_profit_price,
#                                 qty=buy.qty,
#                                 buy_code=buy.pk)
  

@receiver(post_save, sender=StockPrice)
def create_sell_transaction(sender, instance, created, **kwargs):
    if created:
        return

    buys_cutloss = Transaction.objects.filter(
        stock=instance.ticker, 
        position='buy', 
        cut_loss_price__gte=instance.match_price/10000,   
    )

    buys_take_profit = Transaction.objects.filter(
        stock=instance.ticker, 
        position='buy', 
        take_profit_price__lte=instance.match_price/10000,   
        take_profit_price__gt=0

    )

    sells = Transaction.objects.filter(stock=instance.ticker, position='sell').values_list('buy_code', flat=True)

    for buy in buys_cutloss | buys_take_profit:
        if buy.pk in sells:
            continue

        account = Account.objects.get(pk=buy.account.pk)
        port = account.portfolio
        item = next((i for i in port if i['stock'] == buy.stock), None)

        if not item:
            continue

        new_qty_saleable = item['qty_sellable'] - item['qty_sell_pending']
  
        if not buy.time_matched or buy.date_stock_on_account > instance.date_time or buy.qty > new_qty_saleable:
            continue

        sell = Transaction.objects.create(
            account=buy.account,
            stock=buy.stock,
            position='sell',
            price=buy.cut_loss_price if buy.position == 'buy' else buy.take_profit_price,
            qty=buy.qty,
            cut_loss_price=0 if buy.position == 'buy' else buy.cut_loss_price,
            buy_code=buy.pk
        )

            
from telegram import Bot
@receiver(post_save, sender=Transaction)
def send_telegram_message(sender, instance, created, **kwargs):
    if created:
        account = Account.objects.get(pk = instance.account.pk)
        bot_token = account.bot.token
        chat_id = account.bot.chat_id
        bot = Bot(token=bot_token)
        if instance.position =='sell':
            bot.send_message(
                chat_id=chat_id, 
                text=f"Có lệnh {instance.position} {instance.stock} giá {instance.price}  ")                  


# from telegram import Bot
# @receiver(post_save, sender=Transaction)
# def send_telegram_group(sender, instance, created, **kwargs):
#     if created:
#         account = Account.objects.get(pk = instance.account.pk)
#         bot_token = account.bot.token
#         group_id = account.bot.chat_id
#         bot = Bot(token=bot_token)
#     if instance.position =='sell':
#         message = 'Hello, group!'
#         bot.send_message(chat_id=group_id, text=message)
# #-870288807

    



                
        

        
        



    

class CashTrasfer(models.Model):
    account = models.ForeignKey(Account,on_delete=models.CASCADE )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name = 'Ngày tạo' )
    modified_at = models.DateTimeField(auto_now=True, verbose_name = 'Ngày chỉnh sửa' )
    amount = models.FloatField()
    description = models.TextField(max_length=255, blank=True)
    def __str__(self):
        return str(self.amount) 




class DateNotTrading(models.Model):
    date = models.DateField(unique=False)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name = 'Ngày tạo' )
    modified_at = models.DateTimeField(auto_now=True, verbose_name = 'Ngày chỉnh sửa' )
    description = models.TextField(max_length=255, blank=True)
    def __str__(self):
        return str(self.date) 
