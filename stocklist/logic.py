import numpy as np
import talib
from datetime import datetime, timedelta
import backtrader as bt
import backtrader.feeds as btfeed
import pandas as pd
import matplotlib.pyplot as plt
import backtrader.analyzers as btanalyzers
from portfolio.models import StockPrice,StockPriceFilter, get_all_info_stock_price
from telegram import Bot
from django.db.models import F


def breakout_strategy(df, period, num_raw):
    date_fiter = datetime.today().date()
    df = df.groupby('ticker').head(num_raw)
    df['res'] = df.groupby("ticker")["close"].rolling(window=period, min_periods=1).max().reset_index(level=0, drop=True)
    df['sup'] = df.groupby("ticker")["close"].rolling(window=period, min_periods=1).min().reset_index(level=0, drop=True)
    df['tsl'] = np.where((df['close'] > df['res'].shift(1)), df['sup'], 
        np.where((df['close'] < df['sup'].shift(1)), df['res'],np.nan))
    df['tsl'].fillna(method='ffill', inplace=True)
    df['mavol'] = df.groupby('ticker')['volume'].rolling(window=period, min_periods=1).mean().values
    df = df.drop(['res', 'sup', 'date_time'], axis=1)
    condition = ((df['date'] == date_fiter) & (df['close'] > df['tsl']) & (df['volume'] > df['mavol']*2)& (df['mavol']>200000))
    df['buy_breakout'] = condition
    return df


def filter_stock_daily():
    get_all_info_stock_price()
    date_fiter = datetime.today().date()
    stock_prices = StockPriceFilter.objects.all().values()
    df = pd.DataFrame(stock_prices)  
    df = breakout_strategy(df, 20, 25)
    df['buy_signal_num'] = df['buy_breakout'].astype(int)
    ticker_list = []
    for ticker, group in df.groupby('ticker'):
        ticker_group = group.head(3)[['buy_signal_num']]
        diff = ticker_group.diff().fillna(0)
        if (diff > 0).any().values[0]:
            ticker_list.append(ticker)
    if len(ticker_list)>0:
        bot = Bot(token='5881451311:AAEJYKo0ttHU0_Ztv3oGuf-rfFrGgajjtEk')
        bot.send_message(
                chat_id='-870288807', 
                text=f"Danh sách cổ phiếu có tín hiệu breakout ngày {date_fiter} là: {'; '.join(result)}")      
    return ticker_list           






# def custom_date_parser(date_string):
#      return pd.to_datetime(date_string, format='%Y-%m-%d')

# # df = pd.read_csv('test.csv', parse_dates=['date'], date_parser=custom_date_parser)








# test chiến lược

# class PandasData(btfeed.PandasData):
#     lines = ('tsl',) # thêm attribute 'tsl' vào lines
#     params = (
#         ('datetime', 'Date'),
#         ('open', 'Open'),
#         ('high', 'High'),
#         ('low', 'Low'),
#         ('close', 'Close'),
#         ('volume', 'Volume'),
#         ('openinterest', 'Open Interest'),
#         ('tsl', 'tsl'),
#     )

# data = PandasData(dataname=df)
# cerebro = bt.Cerebro()
# cerebro.adddata(data)

# class SmaCross(bt.SignalStrategy):
#     def __init__(self):
#         self.buy_signal = bt.indicators.CrossOver(self.data.close, self.data.tsl)
#         sma = bt.indicators.SimpleMovingAverage(self.data.close, period=200)
#         tsl = bt.indicators.SimpleMovingAverage(self.data.tsl, period=10)
#         sma.plotinfo.plotname = 'mysma'
#         tsl.plotinfo.plotname = 'mytsl'
#     def next(self):
#         if not self.position:
#             if self.buy_signal > 0:
#                 self.buy()
#         elif self.position:
#             if self.buy_signal < 0:
#                 self.close()      
  

   

# cerebro.addstrategy(SmaCross)
# # Analyzer
# cerebro.addanalyzer(btanalyzers.SharpeRatio, _name='mysharpe')

# thestrats = cerebro.run()
# thestrat = thestrats[0]

# print('Sharpe Ratio:', thestrat.analyzers.mysharpe.get_analysis())
# cerebro.run()
# cerebro.plot()


