import numpy as np
import talib
from datetime import datetime, timedelta
import backtrader as bt
import backtrader.feeds as btfeed
import pandas as pd
import matplotlib.pyplot as plt
import backtrader.analyzers as btanalyzers
from logic import *


def custom_date_parser(date_string):
      return pd.to_datetime(date_string, format='%Y-%m-%d')

# df = pd.read_csv('test.csv', parse_dates=['date'], date_parser=custom_date_parser)
# test chiến lược

class PandasData(btfeed.PandasData):
    lines = ('tsl',) # thêm attribute 'tsl' vào lines
    params = (
        ('datetime', 'date'),
        ('open', 'open'),
        ('high', 'high'),
        ('low', 'low'),
        ('close', 'close'),
        ('volume', 'volume'),
        ('tsl', 'tsl'),
        ('signal','buy_breakout')
    )
stock_prices = StockPriceFilter.objects.all().values()
df = pd.DataFrame(stock_prices)  
df =  breakout_strategy(df, 20, 25)
data = PandasData(dataname=df)
cerebro = bt.Cerebro()
cerebro.adddata(data)

class SmaCross(bt.SignalStrategy):
    def __init__(self):
        self.buy_signal = self.data.buy_breakout
        sma = bt.indicators.SimpleMovingAverage(self.data.close, period=200)
        tsl = bt.indicators.SimpleMovingAverage(self.data.tsl, period=1)
        sma.plotinfo.plotname = 'mysma'
        tsl.plotinfo.plotname = 'mytsl'
    def next(self):
        if not self.position:
            if self.buy_signal ==True:
                self.buy()
        elif self.position:
            if self.buy_signal ==False:
                self.close()      
  

   

cerebro.addstrategy(SmaCross)
# Analyzer
cerebro.run()
cerebro.plot()


