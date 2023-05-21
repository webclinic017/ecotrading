import numpy as np
from datetime import datetime, timedelta
import pandas as pd
from portfolio.models import *
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
    df = df.groupby('ticker', group_keys=False).apply(lambda x: x.sort_values('date', ascending=False).head(num_raw) if num_raw is not None else x.sort_values('date', ascending=False))
    df['res'] = df.groupby('ticker')['high'].transform(lambda x: x[::-1].rolling(window=period).max()[::-1])
    df['sup'] = df.groupby('ticker')['low'].transform(lambda x: x[::-1].rolling(window=period).min()[::-1])
    df['mavol'] = df.groupby('ticker')['volume'].transform(lambda x: x[::-1].rolling(window=period).mean()[::-1])
    df = df.groupby('ticker').apply(add_test_value)
    df['tsi'].fillna(method='ffill', inplace=True)
    df['pre_close'] = df.groupby('ticker')['close'].shift(-1)
    buy = (df['close'] > df['tsi']) & (df['volume'] > df['mavol']*2) & (df['mavol'] > 100000) & (df['high']/df['close']-1 < 0.015) & (df['close']/df['pre_close']-1 > 0.03)
    sell = (df['close'] < df['tsi']) & (df['volume'] > df['mavol']*2) & (df['mavol'] > 100000) & (df['low']/df['close']-1 < 0.015) & (df['close']/df['pre_close']-1 < 0.03)
    df['signal'] = np.where(buy, 1, np.where(sell, -1, 0))
    return df

# def breakout_strategy(df, period, num_raw=None):
#     if num_raw is not None:
#         df = df.groupby('ticker').apply(lambda x: x.sort_values('date', ascending=False).head(num_raw)).reset_index(drop=True)
#     else:
#         df = df.groupby('ticker').apply(lambda x: x.sort_values('date', ascending=False)).reset_index(drop=True)
#     df['res'] = df.groupby('ticker')['high'].apply(lambda x: x[::-1].rolling(window=period).max()[::-1]) 
#     df['sup'] = df.groupby('ticker')['low'].apply(lambda x: x[::-1].rolling(window=period).min()[::-1]) 
#     df['mavol'] = df.groupby('ticker')['volume'].apply(lambda x: x[::-1].rolling(window=period).mean()[::-1]) 
#     df = df.groupby('ticker').apply(add_test_value).reset_index(drop=True)
#     df['tsi'].fillna(method='ffill', inplace=True)
#     df['pre_close'] = df.groupby('ticker')['close'].shift(-1)
#     buy =  (df['close'] > df['tsi']) & (df['volume'] > df['mavol']*2) & (df['mavol']>100000  ) & (df['high']/df['close']-1<0.015) & (df['close']/df['pre_close']-1 >0.03)
#     sell =  (df['close'] < df['tsi']) & (df['volume'] > df['mavol']*2)& (df['mavol']>100000  ) & (df['low']/df['close']-1<0.015) & (df['close']/df['pre_close']-1 <0.03)
#     df['signal'] = np.where(buy,1,np.where(sell,-1,0))
#     return df


def filter_stock_daily():
    get_info_stock_price_filter()
    date_filter = datetime.today().date() 
    stock_prices = StockPriceFilter.objects.all().values()
    df = pd.DataFrame(stock_prices)  
    df = breakout_strategy(df, 20, 25)
    df['milestone'] = np.where(df['signal']== 1,df['res'],np.where(df['signal']== -1,df['sup'],0))
    df_signal = df.loc[(df['signal'] !=0)&(df['close']>3), ['ticker', 'date', 'signal','milestone']].sort_values('date', ascending=True).drop_duplicates(subset=['ticker']).reset_index(drop=True)
    stocks_to_create = []
    stocks_to_update = []
    for index, row in df_signal.iterrows():
        ticker = row['ticker']
        date = row['date']
        if row['signal']  == 1:
            signal = 'buy'
        else:
            signal = 'sell'
        strategy = 'breakout'
        milestone = row['milestone']
        stock = Signaldaily.objects.filter(ticker=ticker, date=date,strategy=strategy ).first()
        if stock is None:
            stocks_to_create.append(Signaldaily(ticker=ticker, date=date, signal=signal,strategy=strategy,milestone = milestone))
        else:
            stock.signal = signal
            stock.milestone = milestone
            stocks_to_update.append(stock)
    Signaldaily.objects.bulk_create(stocks_to_create)
    Signaldaily.objects.bulk_update(stocks_to_update, ['signal','milestone'])  
    buy_today = df_signal.loc[(df_signal['date']==date_filter)& (df_signal['signal']==1)].reset_index(drop=True)
    bot = Bot(token='5881451311:AAEJYKo0ttHU0_Ztv3oGuf-rfFrGgajjtEk')
    group_id = '-967306064'
    list_stock = buy_today['ticker'].tolist()
    # if list_stock:
    #     bot.send_message(
    #             chat_id=group_id, 
    #             text=f"Danh sách cổ phiếu có tín hiệu breakout ngày {date_filter} là: {'; '.join(list_stock)}" )  
    # else:
    #     bot.send_message(
    #             chat_id=group_id, 
    #             text=f"Không có cổ phiếu thỏa mãn tiêu chí breakout được lọc trong ngày {date_filter} ")  
    return buy_today           




