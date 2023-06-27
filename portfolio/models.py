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

#lấy toàn bộ giá cổ phiếu
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
    count = 0
    for i in range (0,len(a)):
        ticker=a[i]['sym']
        open=float(a[i]['ope'])
        low_price=float(a[i]['low'])
        high_price = float(a[i]['hig'])
        close=float(a[i]['mat'])
        volume=float(a[i]['tmv'].replace(',', '') )*10
        StockPrice.objects.create(
            ticker=ticker,
            date= date_time.date(),
            low =  low_price,
            high = high_price,
            open = open,
            close = close,
            volume= volume,
            date_time=date_time )


#lấy toàn bộ giá cổ phiếu
def get_info_stock_price_filter():
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
    count = 0
    for i in range (0,len(a)):
        ticker=a[i]['sym']
        open=float(a[i]['ope'])
        low_price=float(a[i]['low'])
        high_price = float(a[i]['hig'])
        close=float(a[i]['mat'])
        volume=float(a[i]['tmv'].replace(',', '') )*10
        created = StockPriceFilter.objects.update_or_create(
                ticker=ticker,
                date= date_time.date(),
            defaults={
            'low': low_price,
            'high': high_price,
            'open':open,
            'close': close,
            'volume': volume,
            'date_time':date_time, 
                        } )
        if created:
            count = count + 1
    if count >0:
        mindate = StockPriceFilter.objects.all().order_by('date').first().date
        maxdate=  StockPriceFilter.objects.all().order_by('-date').first().date
        len_date = (maxdate -mindate).days
        delete = 0
        if len_date >201:
            delete = StockPriceFilter.objects.filter(date=mindate).delete()
    return f"Tạo mới tổng {count} cổ phiếu, và xóa {delete[0]} cổ phiếu cũ " 

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
        open=float(a[i]['ope'])
        low_price=float(a[i]['low'])
        high_price = float(a[i]['hig'])
        close=float(a[i]['mat'])
        volume=float(a[i]['tmv'].replace(',', '') )*10
        StockPriceFilter.objects.update_or_create(
                ticker=ticker,
                date= date_time.date(),
            defaults={
           'low': low_price,
            'high': high_price,
            'open':open,
            'close': close,
            'volume': volume,
            'date_time':date_time
                        } )
    return StockPriceFilter.objects.all().order_by('-date')[:10]

# tìm thời điểm mốc ban đầu, thời điểm mua lần đầu
def avg_price(pk,stock,end_date):
    item = Transaction.objects.filter(account_id=pk, stock = stock, status_raw = 'matched', time_matched_raw__lte= end_date) 
    total_buy = sum(i.qty for i in item if i.position =='buy' )
    total_sell =sum(i.qty for i in item if i.position =='sell' )
    total_value = sum(i.total_value for i in item if i.position =='buy' )
    date_list =list(item.filter(position ='sell').values_list('time_matched_raw', flat=True).distinct()) 
    avg_price = None
    date_find=None
   
    #kiểm tra có bán hay không, trường hợp đã có bán
    if total_sell >0:
        date_list.sort(reverse=True) 
        
        # kiểm tra ngày gần nhất bán hết và mua lại
        for date in date_list: 
            new_item = item.filter(time_received_stock__lte =date)
            check_total_buy = 0
            check_total_sell =0
            for i in new_item:
                if i.position == 'buy':
                    check_total_buy += i.qty 
                else:
                    check_total_sell +=i.qty
            if check_total_buy == check_total_sell:
                date_find = i.time_matched
                break 
        if date_find:
            cal_item = item.filter(position='buy',time_matched_raw__gt= date_find )
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

#xác định danh mục cổ phiếu đã về
def qty_stock_available(pk,stock):
    end_date = datetime.now()
    item = Transaction.objects.filter(account_id=pk,status_raw='matched', stock = stock, time_received_stock__lte=end_date) 
    total_buy = item.filter(position='buy').aggregate(Sum('qty'))['qty__sum'] or 0
    total_sell = item.filter(position='sell').aggregate(Sum('qty'))['qty__sum'] or 0
    return total_buy -total_sell

#Xác định danh mục cổ phiếu đã mua, bao gồm chờ về
def qty_stock_on_account(pk):
    port_raw = []
    port_str = []
    order = Transaction.objects.filter(account_id=pk,status_raw='matched') 
    new_order =  order.values('stock').annotate(
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
                avgprice = avg_price(pk,stock,end_date)
                qty_sellable =qty_stock_available(pk,stock)
                qty_receiving = qty_total -qty_sellable
                item_sell = Transaction.objects.filter(account_id = pk,position ='sell', stock =stock )
                qty_sell_pending = sum(i.qty for i in item_sell if i.status =='pending')
                market_price = StockPriceFilter.objects.filter(ticker = stock).order_by('-date').first().close     
                profit = qty_total*(market_price-avgprice)*1000
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
                                        'avg_price':round(avgprice,2), 
                                        'market_price':round(market_price,2),
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
        if DateNotTrading.objects.filter(date=date_time).exists() or weekday == 6 or weekday == 5 :  # Nếu là một ngày trong danh sách không giao dịch
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
    item = Transaction.objects.filter(account_id=pk, position ='sell',status_raw = 'matched' )
    deal_close = []
    str_deal_close = []
    for i in item:
            new_end_date = i.time_matched_raw -timedelta(minutes=1)
            avgprice = round(avg_price(pk,i.stock,new_end_date),2)
            profit = i.qty*(i.matched_price -avgprice )*1000
            ratio_profit = (i.matched_price/avgprice-1)*100
            deal_close.append({'stock':i.stock,'date':i.time_matched,'qty': i.qty,
                               'price':i.matched_price,'avg_price':avgprice,
                               'profit':profit,'ratio_profit':ratio_profit})
            str_deal_close.append({'stock':i.stock,'date':i.time_matched,'qty': '{:,.0f}'.format(i.qty),
                               'price':i.matched_price,'avg_price':avgprice,
                               'profit':'{:,.0f}'.format(profit),'ratio_profit':str(round(ratio_profit,2))+str('%')})
    return deal_close, str_deal_close

def check_status_order(pk):
        item = Transaction.objects.get(pk=pk)
        date = define_date(item.created_at, item.modified_at)
        status = 'pending'
        time = None
        time_received_stock = None
        if item.position == 'buy':
            stock_price = StockPriceFilter.objects.filter(
                ticker=item.stock,
                date_time__gte=date,
                close__lte=item.price,
                volume__gte=item.qty*2).order_by('date_time')
            if stock_price:
                status = 'matched'
                time = stock_price.first().date_time
                time_received_stock = difine_date_stock_on_account(time)
        else:
            stock_price = StockPriceFilter.objects.filter(
                ticker=item.stock,
                date_time__gte=date,
                close__gte=item.price,
                volume__gte=item.qty*2).order_by('date_time')
            if stock_price:
                status = 'matched'
                time = stock_price.first().date_time
                time_received_stock = time  
        if status == 'matched':
            item.status_raw = status
            item.time_matched_raw = time
            item.time_received_stock = time_received_stock
            item.matched_price = stock_price.first().close
            item.save()
        return status, time, time_received_stock

# tính giá trung bình danh mục


class BotTelegram (models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name= 'Tên')
    token = models.CharField(max_length=100, unique=True, verbose_name= 'Token')
    description = models.TextField(max_length=255, blank=True, verbose_name= 'Mô tả')
    owner = models.ForeignKey(User,on_delete=models.CASCADE, verbose_name= 'Chủ bot')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name = 'Ngày tạo' )
    modified_at = models.DateTimeField(auto_now=True, verbose_name = 'Ngày chỉnh sửa' )
    class Meta:
         verbose_name = 'Bot Telegram'
         verbose_name_plural = 'Bot Telegram'
    def __str__(self):
        return self.name

class ChatGroupTelegram (models.Model):
    TYPE_CHOICES = [
        ('internal', 'internal'),
        ('external', 'external'),
    ]
    RANK_CHOICES = [
        ('1', '1'),
        ('2', '2'),
        ('3','3'),
    ]
    name = models.CharField(max_length=50, unique=True, verbose_name= 'Tên')
    token = models.ForeignKey(BotTelegram, on_delete=models.CASCADE,verbose_name= 'Token' )
    chat_id = models.CharField(max_length=50, unique=True)
    description = models.TextField(max_length=255, blank=True,verbose_name= 'Mô tả')
    type = models.CharField(max_length=20, choices= TYPE_CHOICES, null=False, blank=False,verbose_name= 'Loại')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name = 'Ngày tạo' )
    modified_at = models.DateTimeField(auto_now=True, verbose_name = 'Ngày chỉnh sửa' )
    rank  = models.CharField(max_length=20, choices= RANK_CHOICES, null=False, blank=False, verbose_name= 'Cấp')
    is_signal = models.BooleanField(default=True,verbose_name= 'Gửi tín hiệu')
    class Meta:
         verbose_name = 'Nhóm Telegram'
         verbose_name_plural = 'Nhóm Telegram'
    
    def __str__(self):
        return self.name


# Create your models here.
class Account (models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name= 'Tên')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name = 'Ngày tạo' )
    modified_at = models.DateTimeField(auto_now=True, verbose_name = 'Ngày chỉnh sửa' )
    description = models.TextField(max_length=255, blank=True, verbose_name= 'Mô tả')
    owner = models.ForeignKey(User,on_delete=models.CASCADE, verbose_name= 'Chủ TK' )
    ratio_risk = models.FloatField(default=0.03,verbose_name= 'Tỷ lệ rủi ro')
    transaction_fee = models.FloatField(default=0.0015, verbose_name= 'Phí giao dịch')
    tax = models.FloatField(default=0.001, verbose_name= 'Thuế')
    bot = models.ForeignKey(BotTelegram,on_delete=models.CASCADE, verbose_name= 'Bot' )
    

    

    class Meta:
         verbose_name = 'Tài khoản'
         verbose_name_plural = 'Tài khoản'

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
        item = Transaction.objects.filter(account_id = self.pk)
        total_trading = sum(i.total_value for i in item if i.status_raw == 'matched')
        # cần cộng thêm giá trị deal mua đang chờ khớp
        pending = sum(i.total_value for i in item if i.status_raw != 'matched' and i.position =='buy')
        net_cash_available = self.net_cash_flow - total_trading -pending
        return net_cash_available
    
    @property
    def market_value(self):
        port = self.portfolio
        market_value = sum(item['qty_total']*item['market_price']*1000 for item in port)
        return market_value
    

    @property
    def total_profit(self):
        order_list = Transaction.objects.filter(account_id = self.pk,status_raw = 'matched' )
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
    date = models.DateField()#auto_now_add=True)
    open = models.FloatField()
    high =models.FloatField()
    low = models.FloatField()
    close = models.FloatField()
    volume =models.FloatField()
    date_time = models.DateTimeField(default=datetime.now)
    
    def __str__(self):
        return str(self.ticker) +str("_")+ str(self.date)
    
class StockPriceFilter(models.Model):
    ticker = models.CharField(max_length=10)
    date = models.DateField()#auto_now_add=True)
    open = models.FloatField()
    high =models.FloatField()
    low = models.FloatField()
    close = models.FloatField()
    volume =models.FloatField()
    date_time = models.DateTimeField(null=True, blank=True)
    def __str__(self):
        return str(self.ticker) + str(self.date)


#lấy danh sách mã chứng khoán, top 500 thanh khoản
get_item = StockPrice.objects.all().order_by('-date_time','-volume')
LIST_STOCK = []
for item in get_item[:500]:
    get_stock = item.ticker
    LIST_STOCK.append((get_stock,get_stock))
    LIST_STOCK.sort()
    LIST_STOCK = list(set(LIST_STOCK))

 
class Transaction (models.Model):
    
    POSITION_CHOICES = [
        ('buy', 'Buy'),
        ('sell', 'Sell'),
    ]
    account = models.ForeignKey(Account,on_delete=models.CASCADE, null=False, blank=False, verbose_name = 'Tài khoản' )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name = 'Ngày tạo' )
    modified_at = models.DateTimeField(auto_now=True, verbose_name = 'Ngày chỉnh sửa' )
    stock = models.CharField(max_length=8, choices=LIST_STOCK, null=False, blank=False,verbose_name = 'Cổ phiếu')
    position = models.CharField(max_length=4, choices=POSITION_CHOICES, null=False, blank=False,verbose_name = 'Mua/Bán')
    price = models.FloatField(verbose_name = 'Giá')
    qty = models.IntegerField(null=True,blank=True,verbose_name = 'Khối lượng')
    cut_loss_price = models.FloatField(null=True,blank=True,verbose_name = 'Giá cắt lỗ')
    buy_code = models.IntegerField(default=0,verbose_name = 'Mã mua')
    take_profit_price = models.FloatField(null=True,blank=True,verbose_name = 'Giá chốt lời')
    status_raw = models.CharField(max_length=10, null=True,blank=True)
    time_matched_raw = models.DateTimeField(null=True,blank=True)
    time_received_stock = models.DateTimeField(null=True,blank=True)
    description = models.TextField(max_length=200,null=True,blank=True,verbose_name = 'Mô tả')
    matched_price = models.FloatField(null=True, blank=True,verbose_name = 'Giá khớp lệnh')
 
    class Meta:
         verbose_name = 'Sổ lệnh '
         verbose_name_plural = 'Sổ lệnh '

    def __str__(self):
        return self.position + str("_") + self.stock
    
    def clean(self):
        if not self.account:
            raise ValidationError({'account': 'Vui lòng nhập tài khoản'})
        if self.cut_loss_price:
            if self.cut_loss_price < 0 or self.cut_loss_price >= self.price:
                raise ValidationError({'cut_loss_price': 'Giá cắt lỗ phải lớn hơn 0 và nhỏ hơn giá mua'})
        if self.take_profit_price:
            if self.cut_loss_price < 0 or self.take_profit_price <= self.price:
                raise ValidationError({'take_profit_price': 'Giá chốt lời phải lớn hơn 0 và lớn hơn giá mua'})                        
        # if not self.pk:  # đây là lần tạo mới record
        if self.position:
            if self.position == 'buy':
                if self.qty:
                    item = Transaction.objects.filter(account_id=self.account.pk).exclude(pk=self.pk)
                    total_trading = sum(i.total_value for i in item if i.status_raw == 'matched')
                    # cần cộng thêm giá trị deal mua đang chờ khớp
                    pending = sum(i.total_value for i in item if i.status_raw != 'matched' and i.position =='buy')
                    net_cash_available = self.account.net_cash_flow - total_trading -pending
                    if self.total_value > net_cash_available :
                        raise ValidationError({'qty': f'Không đủ sức mua, số lượng tối đa {net_cash_available:,.0f} cp'})
                else:
                    if not self.qty:
                        raise ValidationError({'qty': 'Vui lòng nhập số lượng hoặc giá cắt lỗ'})      
            elif self.position == 'sell':
                if not self.qty:
                    raise ValidationError({'qty': 'Vui lòng nhập số lượng'})
                else:
                    port = self.account.portfolio
                    qty_sell_pending = Transaction.objects.filter(account_id=self.account.pk,
                            status_raw = 'pending', position = 'sell').exclude(pk=self.pk).aggregate(Sum('qty'))['qty__sum'] or 0
                    item = next((item for item in port if item['stock'] == self.stock), None)
                    if not item:
                        raise ValidationError({'qty': 'Không có cổ phiếu để bán'})
                    max_sellable_qty = item['qty_sellable'] - qty_sell_pending
                    if self.qty > max_sellable_qty:
                        raise ValidationError({'qty': f'Không đủ cổ phiếu bán, tổng cổ phiếu khả dụng là {max_sellable_qty}'})
        else:
                raise ValidationError({'position': 'Vui lòng chọn "mua" hoặc "bán"'})
        
        
        # else:  # đây là lần chỉnh sửa record
        #     if self.position == 'buy':
        #         if self.qty:
        #             item = Transaction.objects.filter(account_id=self.account.pk).exclude(pk=self.pk)
        #             total_trading = sum(i.total_value for i in item if i.status_raw == 'matched')
        #             # cần cộng thêm giá trị deal mua đang chờ khớp
        #             pending = sum(i.total_value for i in item if i.status_raw != 'matched' and i.position =='buy')
        #             net_cash_available = self.account.net_cash_flow - total_trading -pending
        #             if self.total_value > net_cash_available :
        #                 raise ValidationError({'qty': f'Không đủ sức mua, số lượng tối đa {net_cash_available:,.0f} cp'})
        #         else:
        #             if not self.qty:
        #                 raise ValidationError({'qty': 'Vui lòng nhập số lượng hoặc giá cắt lỗ'})      
        #     else:
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

    

            

    def save(self, *args, **kwargs):
        if self.position == 'buy' and self.account.name != "Bot_Breakout":
                risk = self.account.ratio_risk
                nav = self.account.net_cash_flow +self.account.total_profit_close
                R = risk*nav
                if self.cut_loss_price ==None or self.cut_loss_price <0:
                    cut_loss_price  = self.price - R/(self.qty*1000)
                    if cut_loss_price >0:
                        self.cut_loss_price = round(cut_loss_price,0)
                        self.take_profit_price = round(self.price + 4*(self.price - self.cut_loss_price),2)
                    else:
                        self.cut_loss_price == None
                elif self.cut_loss_price and self.cut_loss_price >0:
                    if self.qty == 0 or self.qty ==None:
                        self.qty = R/((self.price -self.cut_loss_price)*1000)
                        self.take_profit_price = round(self.price + 4*(self.price - self.cut_loss_price),2)
                #chỉ check save khi buy
                try:
                    self.full_clean()
                except ValidationError as e:
                    raise ValidationError(f'Có lỗi  {e}')
                else:
                    # Lưu đối tượng nếu không có lỗi
                    super(Transaction, self).save(*args, **kwargs)
        else:
            # Lưu đối tượng nếu không có lỗi
            super(Transaction, self).save(*args, **kwargs)
        
        

    @property
    def total_value(self):
        if self.price and self.qty:
            if self.matched_price:
                price = self.matched_price
            else:
                price = self.price
            if self.position =='buy':
                total = price*self.qty*1000*(1+self.account.transaction_fee)
            else:
                total = -price*self.qty*1000*(1+self.account.transaction_fee +self.account.tax) 
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
        if self.status_raw:
            status = 'matched'
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
    
class DividendManage(models.Model):
    DIVIDEND_CHOICES = [
        ('cash', 'cash'),
        ('stock', 'stock'),
        ('option','option')
    ]
    ticker =  models.CharField(max_length=8, choices=LIST_STOCK, null=False, blank=False,verbose_name = 'Cổ phiếu')
    type = models.CharField(max_length=20, choices=DIVIDEND_CHOICES, null=False, blank=False)
    date_apply = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True, verbose_name = 'Ngày tạo' )
    modified_at = models.DateTimeField(auto_now=True, verbose_name = 'Ngày chỉnh sửa' )
    cash = models.FloatField(null= False, blank=False, default=0)
    stock = models.FloatField(null= False, blank=False, default=0)
    price_option = models.FloatField(null= False, blank=False, default=0)
    stock_option = models.FloatField(null= False, blank=False, default=0)
    
    def __str__(self):
        return str(self.ticker) +str("_")+ str(self.date_apply)
        





# @receiver(post_save, sender=StockPrice)
# def create_sell_transaction(sender, instance, created, **kwargs):
#     if not created:
#         # Get the latest buy Transactions for this stock
#         buys_cutloss = Transaction.objects.filter(
#             stock=instance.ticker, 
#             position='buy', 
#             cut_loss_price__gte=instance.close,   
#         )
#         buys_take_profit = Transaction.objects.filter(
#              stock=instance.ticker, 
#              position='buy', 
#              take_profit_price__lte =instance.close,  
#              take_profit_price__gt=0 
#         )
#         sells = Transaction.objects.filter(stock=instance.ticker, position='sell').values_list('buy_code', flat=True)
#         # Check if the cut_loss_price is greater than the close
#         if buys_cutloss: 
#             for buy in buys_cutloss:
#                 account = Account.objects.get(pk=buy.account.pk)
#                 port = account.portfolio
#                 for item in port:
#                     if item['stock'] == buy.stock:
#                         new_qty_saleable = item['qty_sellable'] - item['qty_sell_pending']
#                         if buy.time_matched and buy.time_received_stock <= instance.date_time and buy.qty <=new_qty_saleable and buy.pk not in sells:
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
#                         if buy.time_matched and buy.time_received_stock <= instance.date_time and buy.qty <= new_qty_saleable and buy.pk not in sells:
#                             sell = Transaction.objects.create(
#                                 account=buy.account,
#                                 stock=buy.stock,
#                                 position='sell',
#                                 price=buy.take_profit_price,
#                                 qty=buy.qty,
#                                 buy_code=buy.pk)
  

@receiver(post_save, sender=StockPriceFilter)
def create_sell_transaction(sender, instance, created, **kwargs):
    if created:
        return
    buys_cutloss = None
    buys_take_profit = None
    
    buys_cutloss = Transaction.objects.filter(
        stock=instance.ticker, 
        position='buy', 
        status_raw = 'matched',
        cut_loss_price__gte = instance.close, 
    )

    buys_take_profit = Transaction.objects.filter(
        stock=instance.ticker, 
        position='buy',
        status_raw = 'matched', 
        take_profit_price__lte = instance.close,   
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
  
        if not buy.time_matched_raw or buy.time_received_stock > instance.date_time or buy.qty > new_qty_saleable:
            continue
        
        if buys_cutloss:
            price_sell =buy.cut_loss_price
        elif buys_take_profit:
            price_sell = buy.take_profit_price

        sell = Transaction.objects.create(
            account=buy.account,
            stock=buy.stock,
            position='sell',
            price=price_sell,
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
        bot = Bot(token=bot_token)
        if instance.account.name =='Bot_Breakout':
            bot.send_message(
                chat_id='-870288807', 
                text=f"Tài khoản {instance.account} có lệnh {instance.position} {instance.stock} giá {instance.price}  ")                  

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
    account = models.ForeignKey(Account,on_delete=models.CASCADE,verbose_name = 'Tài khoản' )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name = 'Ngày tạo' )
    modified_at = models.DateTimeField(auto_now=True, verbose_name = 'Ngày chỉnh sửa' )
    amount = models.FloatField(verbose_name = 'Số tiền')
    description = models.TextField(max_length=255, blank=True,verbose_name = 'Mô tả')
    class Meta:
         verbose_name = 'Giao dịch tiền'
         verbose_name_plural = 'Giao dịch tiền'
    
    def __str__(self):
        return str(self.amount) 



class DateNotTrading(models.Model):
    date = models.DateField(unique=False)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name = 'Ngày tạo' )
    modified_at = models.DateTimeField(auto_now=True, verbose_name = 'Ngày chỉnh sửa' )
    description = models.TextField(max_length=255, blank=True)
    def __str__(self):
        return str(self.date) 



