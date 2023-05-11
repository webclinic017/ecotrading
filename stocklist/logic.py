import numpy as np
import talib
from datetime import datetime
import backtrader as bt
import backtrader.feeds as btfeed
import pandas as pd
import matplotlib.pyplot as plt
import backtrader.analyzers as btanalyzers
from portfolio.models import StockPrice

date_fiter = datetime.today().strftime('%Y-%m-%d')

def breakout_strategy(df, period):
    df['res'] = talib.MAX(df['close'], timeperiod=period)
    df['sup'] = talib.MIN(df['close'], timeperiod=period)
    df['tsl'] = np.where((df['close'] > df['res'].shift(1)), df['sup'], 
        np.where((df['close'] < df['sup'].shift(1)), df['res'],np.nan))
    df['tsl'].fillna(method='ffill', inplace=True)
    df['mavol'] = talib.SMA(df['volume'], timeperiod=period)
    return df
def filter_breakout(df, condition):
    df['tsl_cross'] = condition.astype(int)
    df['first_signal'] = (df['tsl_cross'] - df['tsl_cross'].shift(1)).fillna(0).astype(bool)
    filtered_df = df[df['first_signal']]
    list =[]
    if len(filtered_df) >0:
        list = list(filtered_df['Ticker'])
    return list
    
stock_prices = StockPrice.objects.all().order_by('ticker','-date')
data = list(stock_prices.values())
df = pd.DataFrame(data)  
df =    breakout_strategy(df, 20)

condition = ((df['date'] > '2023-04-01') & (df['close'] > df['tsl']) & (df['volume'] > df['mavol']*1.5))
list = filter_breakout(df, condition)
print(list)






def custom_date_parser(date_string):
     return pd.to_datetime(date_string, format='%Y-%m-%d')

df = pd.read_csv('test.csv', parse_dates=['date'], date_parser=custom_date_parser)








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


