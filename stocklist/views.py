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
from backtrader.observer import Observer
from statistics import mean




def custom_date_parser(date_string):
      return pd.to_datetime(date_string, format='%Y-%m-%d')

def difine_stock_date_to_sell(buy_date):
    buy_weekday = buy_date.weekday()
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
        buy_weekday = buy_date.weekday()  # Cập nhật lại ngày trong tuần sau khi thay đổi time
        
    return buy_date





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
            size = cash* (self.params.percents / 100) / data.open 
        else:
            size = position.size

        if self.p.retint:
            size = math.floor(int(size))
        return size

class breakout(bt.SignalStrategy):
    params = (
        ('multiply_volumn', 2),
        ('rate_of_increase', 0.03),
        ('change_day', 0.015),
        ('risk', 0.03),
    )
    def __init__(self, ticker):
        #khai báo biến
        self.ticker = ticker
        self.trailing_sl = None  # Biến đồng hồ để lưu giá trị stop loss
        #điều kiện buy
        self.buy_price1 = self.data.close > self.data.tsi
        self.buy_vol = self.data.volume > self.data.mavol*self.params.multiply_volumn
        self.buy_minvol =self.data.mavol > 100000
        self.buy_price2 = self.data.high/self.data.close-1 < self.params.change_day
        self.buy_price3 = self.data.close/self.data.pre_close-1 > self.params.rate_of_increase
        #plot view
        tsi = bt.indicators.SimpleMovingAverage(self.data.tsi, period=1)
        tsi.plotinfo.plotname = 'tsi'
    
    def next(self):
        if not self.position:
            if self.buy_price1 == True and self.buy_vol==True and self.buy_minvol==True and self.buy_price2 == True and self.buy_price3 ==True:
                self.buy()
                self.nav= self.broker.getcash()
                self.R = self.nav*self.params.risk
                self.buy_price = self.data.open[1]
                self.qty = self.sizer.getsizing(data=self.data, isbuy=True)
                self.buy_date =datetime.fromordinal(int(self.data.datetime[1]))
                self.trailing_offset= self.R/self.qty
                self.trailing_sl = round(self.buy_price - self.trailing_offset,2)  # Đặt stop loss ban đầu
                self.trailing_tp = round(self.buy_price + self.trailing_offset*2,2)   
        else:
            # Kiểm tra giá hiện tại có vượt quá trailing_sl không
            if self.data.close > self.trailing_tp:
                self.trailing_sl = self.trailing_tp
                self.trailing_tp = self.trailing_tp+self.trailing_offset
            if self.data.close < self.trailing_sl:
                    self.date_sell =datetime.fromordinal(int(self.data.datetime[1]))
                    if self.date_sell >= difine_stock_date_to_sell(self.buy_date):
                        self.close()  
                        self.sell_price =self.data.open[1]
                        data = {
                            'nav': round(self.nav,2),
                            'date_buy':self.buy_date,
                            'buy_price':self.buy_price,
                            'qty': math.floor(int(self.qty)),
                            'date_sell':self.date_sell,
                            'sell_price': self.sell_price,
                            'ratio_pln': round((self.sell_price-self.buy_price)*self.qty*100/self.nav,2),
                            'len_days': (self.date_sell-self.buy_date).days,
                            'stop_loss':round(self.trailing_sl,2),
                            'take_profit': round(self.trailing_tp,2),
                            'strategy': 'breakout'
                        }
                        obj, created = TransactionBacktest.objects.update_or_create(ticker=self.ticker,date_buy = self.buy_date,strategy='breakout', defaults=data)
                        
        return        
                    
    # #giao dịch sẽ lấy giá open của phiên liền sau đó (không phải giá đóng cửa)
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
        
       


def run_backtest(period, nav, commission):
    stock_test = OverviewBreakoutBacktest.objects.values('ticker').order_by('ticker')
    list_bug =[]
    for item in stock_test:
        ticker = item['ticker']
        print('------đang chạy:', ticker)
        try:
            stock_prices = StockPrice.objects.filter(ticker=ticker).values()
            df = pd.DataFrame(stock_prices)
            df = breakout_strategy(df, period)
            df = df.drop(['id','res','sup'], axis=1) 
            df = df.sort_values('date', ascending=True).reset_index(drop=True)  # Sửa 'stock' thành biến stock để sử dụng giá trị stock được truyền vào hàm
            data = PandasData(dataname=df)
            # Tạo một phiên giao dịch Backtrader mới
            cerebro = bt.Cerebro()
            # Thêm dữ liệu và chiến lược vào cerebro
            cerebro.adddata(data)
            cerebro.addobserver(bt.observers.DrawDown)
            cerebro.addstrategy(breakout,ticker)
            
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
            port_value = round(cerebro.broker.getvalue(), 0)
            ratio_pln = (port_value - nav) / nav
            drawdown = result.analyzers.drawdown.get_analysis()['drawdown']
            overview = result.analyzers.overviews.get_analysis()
            sharpe_ratio = result.analyzers.sharpe_ratio.get_analysis()['sharperatio']
            total_closed_test = overview.total.get('closed')
            
            list_trade = TransactionBacktest.objects.filter(ticker =ticker, strategy = 'breakout')
            if total_closed_test and sharpe_ratio and total_closed_test > 0:
                overview_data = {
                    'nav': nav,  # vốn ban đầu
                    'commission': commission,  # phí giao dịch
                    'ratio_pln': round(ratio_pln*100, 3),  # tỷ suất lợi nhuận
                    'drawdown': round(drawdown, 3),  # Tìm hiểu
                    'sharpe_ratio': round(sharpe_ratio, 3),  # tìm hiểu
                    'total_trades': overview.total.get('total'),  # tổng số deal
                    'total_open_trades': overview.total.get('open'),  # deal đang mở, chưa chốt
                    'total_closed_trades': overview.total.get('closed'),  # đang đã đóng
                    'win_trade_ratio':round(overview.won.get('total')*100/overview.total.get('total'),2),
                    # Chuỗi giao dịch liên tiếp
                    'won_current_streak': overview.streak.won.get('current'),
                    'won_longest_streak': overview.streak.won.get('longest'),
                    'lost_current_streak': overview.streak.lost.get('current'),
                    'lost_longest_streak': overview.streak.lost.get('longest'),
                    # Thống kê % lợi nhuận
                    'gross_average_pnl': round(overview.pnl.gross.get('average') / nav, 2),
                    # 'net_total_pnl': #bị trùng 'ratio_pln'
                    'net_average_pnl': round(mean(i.ratio_pln for i in list_trade),3),         
                    # Thống kê giao dịch thắng
                    'won_total_trades': overview.won.get('total'),
                    'won_total_pnl': round(sum(i.ratio_pln for i in list_trade if i.ratio_pln>0 ), 2),
                    'won_average_pnl': round(mean(i.ratio_pln for i in list_trade if i.ratio_pln>0 ), 2),
                    'won_max_pnl': max(i.ratio_pln for i in list_trade if i.ratio_pln>0 ),
                    'lost_total_trades': overview.lost.get('total'),
                    'lost_total_pnl': round(sum(i.ratio_pln for i in list_trade if i.ratio_pln<0 ), 2),
                    'lost_average_pnl': round(mean(i.ratio_pln for i in list_trade if i.ratio_pln<0 ), 2),
                    'lost_max_pnl': min(i.ratio_pln for i in list_trade if i.ratio_pln<0 ),
                    #thống kê giao dịch long (mua)
                        # 'total_long_trades': overview.long.get('total'),
                        # 'total_long_pnl': round(overview.long.pnl.get('total') / nav, 2),
                        # 'total_long_average_pnl': round(overview.long.pnl.get('average') / nav, 2),
                        # 'won_long_trades': overview.long.won,
                        # 'won_long_total_pnl': round(overview.long.pnl.won.get('total') / nav, 2),
                        # 'won_long_average_pnl': round(overview.long.pnl.won.get('average') / nav, 2),
                        # 'won_long_max_pnl': round(overview.long.pnl.won.get('max') / nav, 2),
                        # 'lost_long_trades': overview.long.lost,
                        # 'lost_long_total_pnl': round(overview.long.pnl.lost.get('total') / nav, 2),
                        # 'lost_long_average_pnl': round(overview.long.pnl.lost.get('average') / nav, 2),
                        # 'lost_long_max_pnl': round(overview.long.pnl.lost.get('max') / nav, 2),
                    #thống kê giao dịch short (bán khống)
                        # 'total_short_trades': overview.short.get('total'),
                        # 'total_short_pnl': overview.short.pnl.get('total'),
                        # 'total_short_average_pnl': round(overview.short.pnl.get('average') / nav, 2),
                        # 'won_short_total_pnl': round(overview.short.pnl.won.get('total'), 2),
                        # 'won_short_average_pnl': round(overview.short.pnl.won.get('average') / nav, 2),
                        # 'won_short_max_pnl': round(overview.short.pnl.won.get('max') / nav, 2),
                        # 'lost_short_total_pnl': round(overview.short.pnl.lost.get('total') / nav, 2),
                        # 'lost_short_average_pnl': round(overview.short.pnl.lost.get('average') / nav, 2),
                        # 'lost_short_max_pnl': round(overview.short.pnl.lost.get('max') / nav, 2),
                        # 'lost_short_trades': overview.short.lost,
                        # 'won_short_trades': overview.short.won,
                    #thống kê số ngày nắm giữ của giao dịch
                    'total_trades_length': overview.len.get('total'),
                    'average_trades_per_day': round(overview.len.get('average'), 2),
                    'max_trades_per_day': overview.len.get('max'),
                    'min_trades_per_day': overview.len.get('min'),
                    'total_won_trades_length': overview.len.won.get('total'),
                    'average_won_trades_per_day': round(overview.len.won.get('average'),2),
                    'max_won_trades_per_day': overview.len.won.get('max'),
                    'min_won_trades_per_day': overview.len.won.get('min'),
                    'total_lost_trades_length': overview.len.lost.get('total'),
                    'average_lost_trades_per_day': round(overview.len.lost.get('average'),2),
                    'max_lost_trades_per_day': overview.len.lost.get('max'),
                    'min_lost_trades_per_day': overview.len.lost.get('min'),
                }
                obj, created = OverviewBreakoutBacktest.objects.update_or_create(ticker=ticker, defaults=overview_data)
                print('Đã tạo thông số trade')
        except Exception as e:
            print(f"Có lỗi với cổ phiếu {ticker}: {str(e)}")
            list_bug.append({ticker:str(e)})
        detail_stock = OverviewBreakoutBacktest.objects.filter(total_trades__gt=0)
        strategy ='breakout'
        total = {
            'ratio_pln':mean(i.ratio_pln for i in detail_stock),
            'drawdown':mean(i.drawdown for i in detail_stock),
            'sharpe_ratio':mean(i.sharpe_ratio for i in detail_stock),
            'total_trades': sum(i.total_trades for i in detail_stock),
            'total_open_trades' : sum(i.total_open_trades for i in detail_stock),
            'win_trade_ratio': mean(i.win_trade_ratio for i in detail_stock),
            'total_closed_trades': sum(i.total_closed_trades for i in detail_stock),
            'won_total_trades' :sum(i.won_total_trades for i in detail_stock),
            'won_total_pnl' :sum(i.won_total_pnl for i in detail_stock),
            'won_average_pnl' :mean(i.won_average_pnl for i in detail_stock),
            'won_max_pnl' : max(i.won_max_pnl for i in detail_stock),
            'lost_total_trades' : sum(i.lost_total_trades for i in detail_stock),
            'lost_total_pnl' : sum(i.lost_total_pnl for i in detail_stock),
            'lost_average_pnl' :mean(i.lost_average_pnl for i in detail_stock),
            'lost_max_pnl' : min(i.lost_max_pnl for i in detail_stock),
            'total_trades_length' : mean(i.total_trades_length for i in detail_stock),
            'average_trades_per_day': mean(i.average_trades_per_day for i in detail_stock),
            'max_trades_per_day' :max(i.max_trades_per_day for i in detail_stock),
            'min_trades_per_day' :  min(i.min_trades_per_day for i in detail_stock),
            'total_won_trades_length' : mean(i.total_won_trades_length for i in detail_stock),
            'average_won_trades_per_day' :mean(i.average_won_trades_per_day for i in detail_stock),
            'max_won_trades_per_day' : max(i.max_won_trades_per_day for i in detail_stock),
            'min_won_trades_per_day' : min(i.min_won_trades_per_day for i in detail_stock),
            'total_lost_trades_length' :mean(i.total_lost_trades_length for i in detail_stock),
            'average_lost_trades_per_day' :mean(i.average_lost_trades_per_day for i in detail_stock),
            'max_lost_trades_per_day': max(i.max_lost_trades_per_day for i in detail_stock),
            'min_lost_trades_per_day' : min(i.min_lost_trades_per_day for i in detail_stock),
        }
        obj, created = RatingStrategy.objects.update_or_create(strategy=strategy, defaults=total)
        print('Đã tạo tổng kết chiến lược')
    return list_bug




    # render(request, 'myapp/backtest_result.html', 
                    #   {'summary': summary, 
                    #    'trades': trades,
                    #     'chart_path': chart_path})



def run_backtest_one_stock(ticker,period, nav, commission):
    stock_prices = StockPrice.objects.filter(ticker = ticker).values()
    df = pd.DataFrame(stock_prices)
    df = breakout_strategy(df, period)
    df = df.drop(['id','res','sup'], axis=1) 
    df = df.sort_values('date', ascending=True).reset_index(drop=True)  # Sửa 'stock' thành biến stock để sử dụng giá trị stock được truyền vào hàm
    data = PandasData(dataname=df)
    # Tạo một phiên giao dịch Backtrader mới
    cerebro = bt.Cerebro()
    # Thêm dữ liệu và chiến lược vào cerebro
    cerebro.adddata(data)
    cerebro.addobserver(bt.observers.DrawDown)
    cerebro.addstrategy(breakout,ticker)
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
    # lấy ngày mua
    buy_date = result.buy_date
   
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
    print('Overview:', overview)
    # cerebro.plot(style='candlestick')  # Thêm style='candlestick' để hiển thị biểu đồ dạng nến
    # Tạo biểu đồ
        
        # Lưu biểu đồ vào một tệp hình ảnh
        # chart_path = os.path.join('stocklist/static', 'chart.png')
        # plt.savefig(chart_path)
        # Trích xuất thông tin kết quả backtest
        # trade_analysis = result[0]
        # Render template và trả về kết quả backtest    
    return 


def get_total_backtest():
    total = OverviewBreakoutBacktest.objects.filter(total_trades__gt=0)
    overview_data = {
                    'nav': nav,  # vốn ban đầu
                    'commission': commission,  # phí giao dịch
                    'ratio_pln': round(ratio_pln, 3),  # tỷ suất lợi nhuận
                    'drawdown': round(drawdown, 3),  # Tìm hiểu
                    'sharpe_ratio': round(sharpe_ratio, 3),  # tìm hiểu
                    'total_trades': overview.total.get('total'),  # tổng số deal
                    'win_trade_ratio':round(overview.won.get('total')/overview.total.get('total'),2),
                    'total_open_trades': overview.total.get('open'),  # deal đang mở, chưa chốt
                    'total_closed_trades': overview.total.get('closed'),  # đang đã đóng
                    # Chuỗi giao dịch liên tiếp
                    'won_current_streak': overview.streak.won.get('current'),
                    'won_longest_streak': overview.streak.won.get('longest'),
                    'lost_current_streak': overview.streak.lost.get('current'),
                    'lost_longest_streak': overview.streak.lost.get('longest'),
                    # Thống kê % lợi nhuận
                    'gross_total_pnl': round(overview.pnl.gross.get('total') / nav, 2),
                    'gross_average_pnl': round(overview.pnl.gross.get('average') / nav, 2),
                    'net_total_pnl': round(overview.pnl.net.get('total') / nav, 2),
                    'net_average_pnl': round(overview.pnl.net.get('average') / nav, 2),
                    # Thống kê giao dịch thắng
                    'won_total_trades': overview.won.get('total'),
                    'won_total_pnl': round(overview.won.pnl.get('total') / nav, 2),
                    'won_average_pnl': round(overview.won.pnl.get('average') / nav, 2),
                    'won_max_pnl': round(overview.won.pnl.get('max') / nav, 2),
                    'lost_total_trades': overview.lost.get('total'),
                    'lost_total_pnl': round(overview.lost.pnl.get('total') / nav, 2),
                    'lost_average_pnl': round(overview.lost.pnl.get('average') / nav, 2),
                    'lost_max_pnl': round(overview.lost.pnl.get('max') / nav, 2),
                    'total_long_trades': overview.long.get('total'),
                    'total_long_pnl': round(overview.long.pnl.get('total') / nav, 2),
                    'total_long_average_pnl': round(overview.long.pnl.get('average') / nav, 2),
                    'won_long_trades': overview.long.won,
                    'won_long_total_pnl': round(overview.long.pnl.won.get('total') / nav, 2),
                    'won_long_average_pnl': round(overview.long.pnl.won.get('average') / nav, 2),
                    'won_long_max_pnl': round(overview.long.pnl.won.get('max') / nav, 2),
                    'lost_long_trades': overview.long.lost,
                    'lost_long_total_pnl': round(overview.long.pnl.lost.get('total') / nav, 2),
                    'lost_long_average_pnl': round(overview.long.pnl.lost.get('average') / nav, 2),
                    'lost_long_max_pnl': round(overview.long.pnl.lost.get('max') / nav, 2),
                    'total_short_trades': overview.short.get('total'),
                    'total_short_pnl': overview.short.pnl.get('total'),
                    'total_short_average_pnl': round(overview.short.pnl.get('average') / nav, 2),
                    'won_short_total_pnl': round(overview.short.pnl.won.get('total'), 2),
                    'won_short_average_pnl': round(overview.short.pnl.won.get('average') / nav, 2),
                    'won_short_max_pnl': round(overview.short.pnl.won.get('max') / nav, 2),
                    'lost_short_total_pnl': round(overview.short.pnl.lost.get('total') / nav, 2),
                    'lost_short_average_pnl': round(overview.short.pnl.lost.get('average') / nav, 2),
                    'lost_short_max_pnl': round(overview.short.pnl.lost.get('max') / nav, 2),
                    'lost_short_trades': overview.short.lost,
                    'won_short_trades': overview.short.won,
                    'total_trades_length': overview.len.get('total'),
                    'average_trades_per_day': round(overview.len.get('average'), 2),
                    'max_trades_per_day': overview.len.get('max'),
                    'min_trades_per_day': overview.len.get('min'),
                    'total_won_trades_length': overview.len.won.get('total'),
                    'average_won_trades_per_day': round(overview.len.won.get('average'),2),
                    'max_won_trades_per_day': overview.len.won.get('max'),
                    'min_won_trades_per_day': overview.len.won.get('min'),
                    'total_lost_trades_length': overview.len.lost.get('total'),
                    'average_lost_trades_per_day': round(overview.len.lost.get('average'),2),
                    'max_lost_trades_per_day': overview.len.lost.get('max'),
                    'min_lost_trades_per_day': overview.len.lost.get('min'),
                }