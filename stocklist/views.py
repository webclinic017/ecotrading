import math
import numpy as np
import talib
from datetime import datetime, timedelta
import backtrader as bt
import backtrader.feeds as btfeed
import pandas as pd
import matplotlib.pyplot as plt
import backtrader.analyzers as btanalyzers
from stocklist.logic import *
from django.shortcuts import render
import os
from backtrader.observer import Observer





def custom_date_parser(date_string):
      return pd.to_datetime(date_string, format='%Y-%m-%d')

def difine_stock_date_to_sell(input_date1, input_date2):
    buy_date = input_date1 + timedelta(days=1)
    sell_date = input_date2 + timedelta(days=1)
    buy_weekday = buy_date.weekday()
    sell_weekday = sell_date.weekday()
    if buy_weekday ==4: # nếu là thứ 6
        buy_date = buy_date + timedelta(days=4)
    else: #các ngày còn lại trong tuần
        buy_date = buy_date + timedelta(days=2)
    buy_weekday = buy_date.weekday()
    while True: #check có trùng ngày lễ không
        if buy_weekday == 5 or buy_weekday == 6 or DateNotTrading.objects.filter(date=buy_date).exists()  :  # Nếu là thứ 7, chủ nhật, lễ
                buy_date = buy_date + timedelta(days=1)  # cộng 1 ngày
        else:
            break
        if sell_weekday == 5 or sell_weekday == 6 or DateNotTrading.objects.filter(date=sell_date).exists()  :
            sell_date = sell_date + timedelta(days=1)  # cộng 1 ngày
        else:
            break
        buy_weekday = buy_date.weekday()  # Cập nhật lại ngày trong tuần sau khi thay đổi time
        sell_weekday = sell_date.weekday()
    return sell_date >= buy_date





# df = pd.read_csv('test.csv', parse_dates=['date'], date_parser=custom_date_parser)
# test chiến lược

class PandasData(btfeed.PandasData):
    lines = ('tsi', 'mavol','pre_close' )  
    params = (
        ('datetime', 'date_time'),
        ('open', 'open'),
        ('high', 'high'),
        ('low', 'low'),
        ('close', 'close'),
        ('volume', 'volume'),
        ('tsi', 'tsi'),
        ('mavol', 'mavol'),
        ('pre_close', 'pre_close'),

    )


class breakout(bt.SignalStrategy):
    params = (
        ('multiply_volumn', 2),
        ('rate_of_increase', 0.03),
        ('change_day', 0.015),
        ('risk', 0.03),
    )
    def __init__(self):
        self.buy_price1 = self.data.close > self.data.tsi
        self.buy_vol = self.data.volume > self.data.mavol*self.params.multiply_volumn
        self.buy_minvol =self.data.mavol > 100000
        self.buy_price2 = self.data.high/self.data.close-1 < self.params.change_day
        self.buy_price3 = self.data.close/self.data.pre_close-1 > self.params.rate_of_increase
        tsi = bt.indicators.SimpleMovingAverage(self.data.tsi, period=1)
        tsi.plotinfo.plotname = 'tsi'
        self.nav= self.broker.getvalue()
        self.trailing_sl = None  # Biến đồng hồ để lưu giá trị stop loss
    def next(self):
        if not self.position:
            if self.buy_price1 == True and self.buy_vol==True and self.buy_minvol==True and self.buy_price2 == True and self.buy_price3 ==True:
                self.buy_date = self.data.datetime.datetime()
                self.buy()
                buy_size = math.floor(self.nav*0.9/(self.data.open))
                self.trailing_offset= self.nav*self.params.risk/buy_size
                self.trailing_sl = round(self.data.open - self.trailing_offset,2)  # Đặt stop loss ban đầu
                self.trailing_tp = round(self.data.open + self.trailing_offset*2,2)
                
        else:
            # Kiểm tra giá hiện tại có vượt quá trailing_sl không
            if self.data.close > self.trailing_tp:
                self.trailing_sl = self.trailing_tp
                self.trailing_tp = self.trailing_tp+self.trailing_offset
            if self.data.close < self.trailing_sl and difine_stock_date_to_sell(self.buy_date,self.data.datetime.datetime())==True: 
                self.close()  

    # # giao dịch sẽ lấy giá open của phiên liền sau đó (không phải giá đóng cửa)
    # def notify_trade(self, trade):
    #     date_open = self.data.datetime.datetime().strftime('%Y-%m-%d')
    #     date_close = self.data.datetime.datetime().strftime('%Y-%m-%d')
    #     if trade.justopened:
    #         print('----TRADE OPENED----')
    #         print('Date: {}'.format(date_open))
    #         print('Price: {}'.format(trade.price))# cũng là print('Price: {}'.format(self.data.open[0]))
    #         print('Size: {}'.format(trade.size))
    #     elif trade.isclosed:
    #         print('----TRADE CLOSED----')
    #         print('Date: {}'.format(date_close))
    #         print('Price: {}'.format(self.data.open[0]))
    #         print('Profit, Gross {}, Net {}'.format(
    #                                             round(trade.pnl,2),
    #                                             round(trade.pnlcomm,2)))
    #     else:
    #         return
        
       
class definesize(bt.Sizer):
    params = (
        ('percents', 90),
        ('retint', False),  # return an int size or rather the float value
    )

    def __init__(self):
        pass

    def _getsizing(self, comminfo, cash, data, isbuy):
        position = self.broker.getposition(data)
        if not position:
            size = cash / data.open * (self.params.percents / 100)
        else:
            size = position.size

        if self.p.retint:
            size = math.floor(int(size))
        return size




def run_backtest(period, nav, commission):
    stock_prices = StockPrice.objects.filter(volume__gt=100).values()
    df = pd.DataFrame(stock_prices)
    df = breakout_strategy(df, period)
    stock_test = list(set(LIST_STOCK))
    for item in stock_test:
        stock = item[0]
        print(stock)
        #chạy hàm for
        df_stock = df.loc[df['ticker'] == stock].sort_values('date', ascending=True).reset_index(drop=True)  # Sửa 'stock' thành biến stock để sử dụng giá trị stock được truyền vào hàm
        data = PandasData(dataname=df_stock)
        # Tạo một phiên giao dịch Backtrader mới
        cerebro = bt.Cerebro()
        # Thêm dữ liệu và chiến lược vào cerebro
        cerebro.adddata(data)
        cerebro.addobserver(bt.observers.DrawDown)
        cerebro.addstrategy(breakout)
        # Thiết lập thông số về kích thước vốn ban đầu và phí giao dịch
        cerebro.broker.setcash(nav)  # Số dư ban đầu
        cerebro.broker.setcommission(commission=commission)  # Phí giao dịch (0.15%)
        #add the sizer
        cerebro.addsizer(definesize)
        # Analyzer
        cerebro.addanalyzer(btanalyzers.TradeAnalyzer, _name='overviews')
        cerebro.addanalyzer(btanalyzers.SharpeRatio, _name='sharpe_ratio')
        cerebro.addanalyzer(btanalyzers.DrawDown, _name='drawdown')
        # Chạy backtest
        result = cerebro.run()
        result = result[0]
        #Get final portfolio Value
        port_value = round(cerebro.broker.getvalue(),0)
        pnl = port_value - nav
        ratio_pln = pnl/nav
        drawdown = result.analyzers.drawdown.get_analysis()['drawdown']
        overview = result.analyzers.overviews.get_analysis()
        sharpe_ratio = result.analyzers.sharpe_ratio.get_analysis()['sharperatio']
        total_closed_test = overview.total.get('closed')
        if total_closed_test and total_closed_test >0:
            overview_data = {
            'nav': nav,
            'commission': commission,
            'ratio_pln': round(ratio_pln, 3),
            'drawdown': round(drawdown, 3),
            'sharpe_ratio': sharpe_ratio,
            'total_trades': overview.total.get('total'),
            'total_open_trades': overview.total.get('open'),
            'total_closed_trades': overview.total.get('closed'),
            'won_current_streak': overview.streak.won.get('current'),
            'won_longest_streak': overview.streak.won.get('longest'),
            'lost_current_streak': overview.streak.lost.get('current'),
            'lost_longest_streak': overview.streak.lost.get('longest'),
            'gross_total_pnl': round(overview.pnl.gross.get('total'), 2),
            'gross_average_pnl': round(overview.pnl.gross.get('average'), 2),
            'net_total_pnl': round(overview.pnl.net.get('total'), 2),
            'net_average_pnl': round(overview.pnl.net.get('average'), 2),
            'won_total_trades': overview.won.get('total'),
            'won_total_pnl': round(overview.won.pnl.get('total'), 2),
            'won_average_pnl': round(overview.won.pnl.get('average'), 2),
            'won_max_pnl': round(overview.won.pnl.get('max'), 2),
            'lost_total_trades': overview.lost.get('total'),
            'lost_total_pnl': round(overview.lost.pnl.get('total'), 2),
            'lost_average_pnl': round(overview.lost.pnl.get('average'), 2),
            'lost_max_pnl': round(overview.lost.pnl.get('max'), 2),
            'total_long_trades': overview.long.get('total'),
            'total_long_pnl': round(overview.long.pnl.get('total'), 2),
            'total_long_average_pnl': round(overview.long.pnl.get('average'), 2),
            'won_long_trades': overview.long.won,
            'won_long_total_pnl': overview.long.pnl.won.get('total'),
            'won_long_average_pnl': overview.long.pnl.won.get('average'),
            'won_long_max_pnl': overview.long.pnl.won.get('max'),
            'lost_long_trades': overview.long.lost,
            'lost_long_total_pnl': round(overview.long.pnl.lost.get('total'), 2),
            'lost_long_average_pnl': round(overview.long.pnl.lost.get('average'), 2),
            'lost_long_max_pnl': round(overview.long.pnl.lost.get('max'), 2),
            'total_short_trades': overview.short.get('total'),
            'total_short_pnl': overview.short.pnl.get('total'),
            'total_short_average_pnl': overview.short.pnl.get('average'),
            'won_short_total_pnl': overview.short.pnl.won.get('total'),
            'won_short_average_pnl': overview.short.pnl.won.get('average'),
            'won_short_max_pnl': overview.short.pnl.won.get('max'),
            'lost_short_total_pnl': overview.short.pnl.lost.get('total'),
            'lost_short_average_pnl': overview.short.pnl.lost.get('average'),
            'lost_short_max_pnl': overview.short.pnl.lost.get('max'),
            'lost_short_trades': overview.short.lost,
            'won_short_trades': overview.short.won,
            'total_trades_length': overview.len.get('total'),
            'average_trades_per_day': overview.len.get('average'),
            'max_trades_per_day': overview.len.get('max'),
            'min_trades_per_day': overview.len.get('min'),
            'total_won_trades_length': overview.len.won.get('total'),
            'average_won_trades_per_day': overview.len.won.get('average'),
            'max_won_trades_per_day': overview.len.won.get('max'),
            'min_won_trades_per_day': overview.len.won.get('min'),
            'total_lost_trades_length': overview.len.lost.get('total'),
            'average_lost_trades_per_day': overview.len.lost.get('average'),
            'max_lost_trades_per_day': overview.len.lost.get('max'),
            'min_lost_trades_per_day': overview.len.lost.get('min'),
            }
            obj, created = OverviewBreakoutBacktest.objects.update_or_create(
            ticker=stock,  # Giá trị của trường ticker để tìm hoặc tạo mới
            defaults=overview_data,
            )
    return 

    # render(request, 'myapp/backtest_result.html', 
                    #   {'summary': summary, 
                    #    'trades': trades,
                    #     'chart_path': chart_path})


def run_backtest_one_stock(stock,period, nav, commission):
    stock_prices = StockPriceFilter.objects.filter(volume__gt=100).values()
    df = pd.DataFrame(stock_prices)
    df = breakout_strategy(df, period)
    #chạy hàm for
    df_stock = df.loc[df['ticker'] == stock].sort_values('date', ascending=True).reset_index(drop=True)  # Sửa 'stock' thành biến stock để sử dụng giá trị stock được truyền vào hàm
    data = PandasData(dataname=df_stock)
    # Tạo một phiên giao dịch Backtrader mới
    cerebro = bt.Cerebro()
    # Thêm dữ liệu và chiến lược vào cerebro
    cerebro.adddata(data)
    cerebro.addobserver(bt.observers.DrawDown)
    cerebro.addstrategy(breakout)
    # Thiết lập thông số về kích thước vốn ban đầu và phí giao dịch
    cerebro.broker.setcash(nav)  # Số dư ban đầu
    cerebro.broker.setcommission(commission=commission)  # Phí giao dịch (0.15%)
    #add the sizer
    cerebro.addsizer(definesize)
    # Analyzer
    cerebro.addanalyzer(btanalyzers.TradeAnalyzer, _name='overviews')
    cerebro.addanalyzer(btanalyzers.SharpeRatio, _name='sharpe_ratio')
    cerebro.addanalyzer(btanalyzers.DrawDown, _name='drawdown')
    # Chạy backtest
    result = cerebro.run()
    result = result[0]
    #Get final portfolio Value
    port_value = round(cerebro.broker.getvalue(),0)
    pnl = port_value - nav
    ratio_pln = pnl/nav
    drawdown = result.analyzers.drawdown.get_analysis()['drawdown']
    overview = result.analyzers.overviews.get_analysis()
    sharpe_ratio = result.analyzers.sharpe_ratio.get_analysis()['sharperatio']
#Print out the final result
    print('----SUMMARY----')
    print('Final Portfolio Value: ${}'.format(port_value))
    print('P/L: ${}'.format(pnl))
    print('drawdown:', drawdown)
    # Tạo biểu đồ
        # cerebro.plot(style='candlestick')  # Thêm style='candlestick' để hiển thị biểu đồ dạng nến
        # Lưu biểu đồ vào một tệp hình ảnh
        # chart_path = os.path.join('stocklist/static', 'chart.png')
        # plt.savefig(chart_path)
        # Trích xuất thông tin kết quả backtest
        # trade_analysis = result[0]
        # Render template và trả về kết quả backtest    
    return overview