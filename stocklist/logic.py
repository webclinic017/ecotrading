import numpy as np
from datetime import datetime, timedelta
import pandas as pd
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
    df = df.drop(['res', 'sup'], axis=1)
    condition = ((df['date'] == date_fiter) & (df['close'] > df['tsl']) & (df['volume'] > df['mavol']*2)& (df['mavol']>100000))
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
    bot = Bot(token='5881451311:AAEJYKo0ttHU0_Ztv3oGuf-rfFrGgajjtEk')
    for ticker, group in df.groupby('ticker'):
        ticker_group = group.head(3)[['buy_signal_num']]
        diff = ticker_group.diff().fillna(0)
        if (diff > 0).any().values[0]:
            ticker_list.append(ticker)
    if len(ticker_list)>0:
        bot.send_message(
                chat_id='-870288807', 
                text=f"Danh sách cổ phiếu có tín hiệu breakout ngày {date_fiter} là: {'; '.join(ticker_list)}")  
    else:
        bot.send_message(
                chat_id='-870288807', 
                text=f"Không có cổ phiếu thỏa mãn tiêu chí breakout được lọc trong ngày {date_fiter} ")  
    return ticker_list           



