import numpy as np
from datetime import datetime, timedelta
import pandas as pd
from portfolio.models import StockPrice,StockPriceFilter, get_all_info_stock_price
from telegram import Bot
from django.db.models import F
from stocklist.models import  *
import talib


import numpy as np

def add_test_value(group):
    group['tsi'] = np.where(
        (group['close'] > group['res'].shift(-1)),
        group['sup'],
        np.where(
            (group['close'] < group['sup'].shift(-1)),
            group['res'],
            np.nan
        ))
    return group


def breakout_strategy(df, period, num_raw=None):
    if num_raw is not None:
        df = df.groupby('ticker').apply(lambda x: x.sort_values('date', ascending=False).head(num_raw)).reset_index(drop=True)
    else:
        df = df.groupby('ticker').apply(lambda x: x.sort_values('date', ascending=False)).reset_index(drop=True)
    df['res'] = df.groupby('ticker')['high'].apply(lambda x: x[::-1].rolling(window=period).max()[::-1]) 
    df['sup'] = df.groupby('ticker')['low'].apply(lambda x: x[::-1].rolling(window=period).min()[::-1]) 
    df['mavol'] = df.groupby('ticker')['volume'].apply(lambda x: x[::-1].rolling(window=period).mean()[::-1]) 
    df = df.groupby('ticker').apply(add_test_value).reset_index(drop=True)
    df['tsi'].fillna(method='ffill', inplace=True)
    buy =  (df['close'] > df['tsi']) & (df['volume'] > df['mavol']*2) & (df['mavol']>100000  )
    sell =  (df['close'] < df['tsi']) & (df['volume'] > df['mavol']*2)& (df['mavol']>100000  )
    df['signal'] = np.where(buy,'buy',np.where(sell,'sell',np.nan))
    return df


def filter_stock_daily():
    get_all_info_stock_price()
    date_filter = datetime.today().date()
    stock_prices = StockPriceFilter.objects.all().values()
    df = pd.DataFrame(stock_prices)  
    df = breakout_strategy(df, 20, 25)
    df_signal = df.loc[df['signal'] !='nan', ['ticker', 'date', 'signal']].sort_values('date', ascending=True).drop_duplicates(subset=['ticker']).reset_index(drop=True)
    df_signal['strategy'] = 'breakout'
    data = [Signaldaily(**vals) for vals in df_signal.to_dict('records')]
    Signaldaily.objects.bulk_create(data)
    buy_today = df_signal.loc[(df_signal['date']==date_filter)& (df_signal['signal']=='buy')].reset_index(drop=True)
    bot = Bot(token='5881451311:AAEJYKo0ttHU0_Ztv3oGuf-rfFrGgajjtEk')
    group_id = '-967306064'
    list_stock = buy_today['ticker'].tolist()
    if list_stock:
        bot.send_message(
                chat_id=group_id, 
                text=f"Danh sách cổ phiếu có tín hiệu breakout ngày {date_filter} là: {'; '.join(list_stock)}" )  
    else:
        bot.send_message(
                chat_id=group_id, 
                text=f"Không có cổ phiếu thỏa mãn tiêu chí breakout được lọc trong ngày {date_filter} ")  
    return buy_today           




