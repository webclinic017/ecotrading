from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_save
from portfolio.models import *

# Create your models here.

class StrategyTrading(models.Model):
    name = models.CharField(max_length=100, verbose_name = 'Tên' )
    modified_date = models.DateTimeField(auto_now=True, verbose_name = 'Ngày tạo')
    risk = models.FloatField(default=0.03, verbose_name = 'Rủi ro lệnh')
    description = models.CharField(max_length=200, null=True, verbose_name = 'Mô tả')
    nav = models.FloatField(default=10000000, verbose_name = 'Vốn đầu tư')
    commission = models.FloatField(default=0.0015, verbose_name = 'Phí giao dịch')
    period= models.IntegerField(default=20, verbose_name = 'Chu kì đầu tư')

    def __str__(self):
        return str(self.name) +str('_')+str(self.risk)
    class Meta:
        verbose_name = 'Chiến lược giao dịch'
        verbose_name_plural = 'Chiến lược giao dịch'
    


class Signaldaily(models.Model):
    ticker = models.CharField(max_length=10, verbose_name = 'Cổ phiếu')
    date = models.DateField(verbose_name = 'Ngày cho tín hiệu')
    close = models.FloatField(default=0, verbose_name = 'Giá thị trường')
    milestone = models.FloatField(default=0, verbose_name = 'Mốc an toàn')
    signal = models.CharField(max_length=10, verbose_name = 'Tín hiệu')
    ratio_cutloss = models.FloatField(default=0, verbose_name = 'Tỷ lệ cắt lỗ tối ưu')
    strategy = models.ForeignKey(StrategyTrading,on_delete=models.CASCADE, null=True, blank=True, verbose_name = 'Chiến lược')
    modified_date = models.DateTimeField(auto_now=True, verbose_name = 'Ngày tạo')
    
    class Meta:
        verbose_name = 'Tín hiệu giao dịch'
        verbose_name_plural = 'Tín hiệu giao dịch'
    
    

    def __str__(self):
        return str(self.ticker) + str(self.strategy)
    

    
    
    
    
           

class OverviewBacktest(models.Model):
    ticker = models.CharField(max_length=15,  verbose_name = 'Cổ phiếu')
    strategy = models.ForeignKey(StrategyTrading,on_delete=models.CASCADE, null=True, blank=True,  verbose_name = 'Chiến lược')
    ratio_pln= models.FloatField(default=0 , verbose_name = 'Tỷ lệ lợi nhuận')
    drawdown= models.FloatField(null=True , verbose_name = 'Drawdown')
    sharpe_ratio= models.FloatField(null=True , verbose_name = 'Tỷ lệ Sharpe')
    total_trades = models.IntegerField(null=True , verbose_name = 'Tổng giao dịch')
    total_open_trades = models.IntegerField(null=True , verbose_name = 'Giao dịch đang mở')
    win_trade_ratio = models.FloatField(null=True , verbose_name = 'Tỷ lệ thắng')
    total_closed_trades = models.IntegerField(null=True,  verbose_name = 'Tổng giao dịch đóng')
    won_current_streak = models.IntegerField(null=True )
    won_longest_streak = models.IntegerField(null=True)
    lost_current_streak = models.IntegerField(null=True)
    lost_longest_streak = models.IntegerField(null=True )
    gross_average_pnl = models.FloatField(null=True , verbose_name = 'Lợi nhuận gộp')
    # net_average_pnl = models.FloatField(null=True)
    won_total_trades = models.IntegerField(null=True , verbose_name = 'Tổng GD thắng')
    won_total_pnl = models.FloatField(null=True , verbose_name = 'Tổng LN thắng')
    won_average_pnl = models.FloatField(null=True , verbose_name = 'TB LN thắng')
    won_max_pnl = models.FloatField(null=True , verbose_name = 'LN thắng tối đa')
    lost_total_trades = models.IntegerField(null=True , verbose_name = 'Tổng GD thua' )
    lost_total_pnl = models.FloatField(null=True, verbose_name = 'Tổng LN thua')
    lost_average_pnl = models.FloatField(null=True, verbose_name = 'TB LN thua')
    lost_max_pnl = models.FloatField(null=True , verbose_name = 'LN thua tối đa')
    # total_long_trades = models.IntegerField(null=True)
    # total_long_pnl = models.FloatField(null=True)
    # total_long_average_pnl = models.FloatField(null=True)
    # won_long_trades = models.IntegerField(null=True)
    # won_long_total_pnl = models.FloatField(null=True)
    # won_long_average_pnl = models.FloatField(null=True)
    # won_long_max_pnl = models.FloatField(null=True)
    # lost_long_trades = models.IntegerField(null=True)
    # lost_long_total_pnl = models.FloatField(null=True)
    # lost_long_average_pnl = models.FloatField(null=True)
    # lost_long_max_pnl = models.FloatField(null=True)
    # total_short_trades = models.IntegerField(null=True)
    # total_short_pnl = models.FloatField(null=True)
    # total_short_average_pnl = models.FloatField(null=True)
    # won_short_trades = models.IntegerField(null=True)
    # won_short_total_pnl = models.FloatField(null=True)
    # won_short_average_pnl = models.FloatField(null=True)
    # won_short_max_pnl = models.FloatField(null=True)
    # lost_short_trades = models.IntegerField(null=True)
    # lost_short_total_pnl = models.FloatField(null=True)
    # lost_short_average_pnl = models.FloatField(null=True)
    # lost_short_max_pnl = models.FloatField(null=True)
    total_trades_length = models.IntegerField(null=True , verbose_name = 'Tổng ngày GD')
    average_trades_per_day = models.FloatField(null=True , verbose_name = 'TB ngày nắm giữ')
    max_trades_per_day = models.IntegerField(null=True , verbose_name = 'Ngày nắm giữ tối đa')
    min_trades_per_day = models.IntegerField(null=True, verbose_name = 'Ngày nắm giữ tối thiểu')
    total_won_trades_length = models.IntegerField(null=True , verbose_name = 'Tổng ngày GD thắng')
    average_won_trades_per_day = models.FloatField(null=True, verbose_name = 'TB ngày nắm giữ GD thắng')
    max_won_trades_per_day = models.IntegerField(null=True, verbose_name = 'Ngày nắm giữ tối đa GD thắng')
    min_won_trades_per_day = models.IntegerField(null=True, verbose_name = 'Ngày nắm giữ tối thiểu GD thắng')
    total_lost_trades_length = models.IntegerField(null=True,verbose_name = 'Tổng ngày GD thua')
    average_lost_trades_per_day = models.FloatField(null=True,verbose_name = 'TB ngày nắm giữ GD thua')
    max_lost_trades_per_day = models.IntegerField(null=True, verbose_name = 'Ngày nắm giữ tối đa GD thua')
    min_lost_trades_per_day = models.IntegerField(null=True, verbose_name = 'Ngày nắm giữ tối thiểu GD thua')
    modified_date = models.DateTimeField(auto_now=True, verbose_name = 'Ngày tạo')
    
    class Meta:
        verbose_name = 'Kết quả kiểm định'
        verbose_name_plural = 'Kết quả kiểm định'

    def __str__(self):
        return self.ticker
    
class TransactionBacktest(models.Model):
    ticker = models.CharField(max_length=15, verbose_name = 'Cổ phiếu')
    strategy = models.ForeignKey(StrategyTrading,on_delete=models.CASCADE, null=True, blank=True, verbose_name = 'Chiến lược')
    nav =  models.FloatField( verbose_name = 'Vốn')
    date_buy = models.DateField( verbose_name = 'Ngày mua')
    qty =models.IntegerField(verbose_name = 'Số lượng')
    date_sell = models.DateField(verbose_name = 'Ngày bán')
    buy_price = models.FloatField(verbose_name = 'Giá mua')
    sell_price = models.FloatField(verbose_name = 'Giá bán')
    ratio_pln= models.FloatField(verbose_name = 'Tỷ lệ LN')
    len_days = models.FloatField(verbose_name = 'Ngày nắm giữ')
    stop_loss = models.FloatField(verbose_name = 'Giá mục tiêu cắt lỗ')
    take_profit = models.FloatField(verbose_name = 'Giá mục tiêu chốt lời')
    strategy = models.CharField(max_length=50,verbose_name = 'Chiến lược')
    modified_date = models.DateTimeField(auto_now=True ,verbose_name = 'Ngày tạo')

    class Meta:
        verbose_name = 'Chi tiết giao dịch kiểm định'
        verbose_name_plural = 'Chi tiết giao dịch kiểm định'

    def __str__(self):
        return self.ticker
    
class RatingStrategy(models.Model):
    strategy = models.ForeignKey(StrategyTrading,on_delete=models.CASCADE, null=True, blank=True,verbose_name = 'Chiến lược')
    description = models.CharField(max_length=200, null=True,verbose_name = 'Mô tả')
    ratio_pln= models.FloatField(verbose_name = 'Tỷ lệ LN')
    drawdown= models.FloatField(null=True, verbose_name = 'Drawdown')
    sharpe_ratio= models.FloatField(null=True, verbose_name = 'Tỷ lệ Sharpe')
    total_trades = models.IntegerField(null=True, verbose_name = 'Tổng giao dịch')
    total_open_trades = models.IntegerField(null=True, verbose_name = 'Tổng GD đang mở')
    win_trade_ratio = models.FloatField(null=True, verbose_name = 'Tỷ lệ thắng')
    total_closed_trades = models.IntegerField(null=True, verbose_name = 'Tổng GD đã đóng')
    # net_average_pnl = models.FloatField(null=True, verbose_name = 'Tỷ lệ LN')
    won_total_trades = models.IntegerField(null=True, verbose_name = 'Tổng GD thắng')
    won_total_pnl = models.FloatField(null=True, verbose_name = 'Tổng LN GD thắng')
    won_average_pnl = models.FloatField(null=True,verbose_name = 'TB LN GD thắng')
    won_max_pnl = models.FloatField(null=True, verbose_name = 'LN tối đa GD thắng')
    lost_total_trades = models.IntegerField(null=True, verbose_name = 'Tổng GD thua')
    lost_total_pnl = models.FloatField(null=True, verbose_name = 'Tổng LN GD thua')
    lost_average_pnl = models.FloatField(null=True, verbose_name = 'TB LN GD thua')
    lost_max_pnl = models.FloatField(null=True, verbose_name = 'Giao dịch thua tối đa')
    total_trades_length = models.IntegerField(null=True, verbose_name = 'Tổng ngày GD')
    average_trades_per_day = models.FloatField(null=True, verbose_name = 'TB ngày nắm giữ')
    max_trades_per_day = models.IntegerField(null=True, verbose_name = 'Ngày nắm giữ tối đa')
    min_trades_per_day = models.IntegerField(null=True, verbose_name = 'Ngày nắm giữ tối thiểu')
    total_won_trades_length = models.IntegerField(null=True, verbose_name = 'Tổng ngày nắm giữ GD thắng')
    average_won_trades_per_day = models.FloatField(null=True, verbose_name = 'TB ngày nắm giữ GD thắng')
    max_won_trades_per_day = models.IntegerField(null=True, verbose_name = 'Ngày nắm giữ GD thắng tối đa')
    min_won_trades_per_day = models.IntegerField(null=True, verbose_name = 'Ngày nắm giữ GD thua tối đa')
    total_lost_trades_length = models.IntegerField(null=True,verbose_name = 'Tổng ngày nắm giữ GD thua')
    average_lost_trades_per_day = models.FloatField(null=True, verbose_name = 'TB ngày nắm giữ GD thua')
    max_lost_trades_per_day = models.IntegerField(null=True, verbose_name = 'Ngày nắm giữ tối đa GD thua')
    min_lost_trades_per_day = models.IntegerField(null=True, verbose_name = 'Ngày nắm giữ tối thiểu GD thua')
    modified_date = models.DateTimeField(auto_now=True,  verbose_name = 'Ngày tạo')

    class Meta:
        verbose_name = 'Đánh giá chiến lược'
        verbose_name_plural = 'Đánh giá chiến lược'
    
    def __str__(self):
        return self.strategy
    
class ParamsOptimize(models.Model):  
    ticker = models.CharField(max_length=15,  verbose_name = 'Cổ phiếu' )  
    strategy = models.ForeignKey(StrategyTrading,on_delete=models.CASCADE, null=True, blank=True,verbose_name = 'Chiến lược' )
    multiply_volumn = models.FloatField(default=2, verbose_name = 'Cấp nhân khối lượng')
    rate_of_increase = models.FloatField(default=0.03 , verbose_name = 'Biến động tăng')
    change_day = models.FloatField(default=0.015, verbose_name = 'Tỷ lệ nến')
    ratio_cutloss= models.FloatField(default=0.05 , verbose_name = 'Tỷ lệ cắt lỗ')
    sma = models.FloatField(default=20 , verbose_name = 'Trung bình giá')

    def __str__(self):
        return self.ticker
    
    class Meta:
        verbose_name = 'Thông số tối ưu'
        verbose_name_plural = 'Thông số tối ưu'