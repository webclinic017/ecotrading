import math
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
    df = df.drop(df[(df['open'] == 0) & (df['close'] == 0)& (df['volume'] == 0)].index)
    df = df.groupby('ticker', group_keys=False).apply(lambda x: x.sort_values('date', ascending=False).head(num_raw) if num_raw is not None else x.sort_values('date', ascending=False))
    df['res'] = df.groupby('ticker')['high'].transform(lambda x: x[::-1].rolling(window=period).max()[::-1])
    df['sup'] = df.groupby('ticker')['low'].transform(lambda x: x[::-1].rolling(window=period).min()[::-1])
    df['mavol'] = df.groupby('ticker')['volume'].transform(lambda x: x[::-1].rolling(window=period).mean()[::-1])
    df = df.groupby('ticker', group_keys=False).apply(add_test_value)
    df['tsi'].fillna(method='ffill', inplace=True)
    df['pre_close'] = df.groupby('ticker')['close'].shift(-1)
    return df

def breakout_strategy_otm(df, period, num_raw=None):
    df = df.drop(df[(df['open'] == 0) & (df['close'] == 0)& (df['volume'] == 0)].index)
    df = df.groupby('ticker', group_keys=False).apply(lambda x: x.sort_values('date', ascending=False).head(num_raw) if num_raw is not None else x.sort_values('date', ascending=False))
    df['res'] = df.groupby('ticker')['high'].transform(lambda x: x[::-1].rolling(window=period).max()[::-1])
    df['sup'] = df.groupby('ticker')['low'].transform(lambda x: x[::-1].rolling(window=period).min()[::-1])
    df['mavol'] = df.groupby('ticker')['volume'].transform(lambda x: x[::-1].rolling(window=period).mean()[::-1])
    df = df.groupby('ticker', group_keys=False).apply(add_test_value)
    df['tsi'].fillna(method='ffill', inplace=True)
    df['pre_close'] = df.groupby('ticker')['close'].shift(-1)
    backtest =OverviewBreakoutBacktest.objects.values('ticker', 'param_multiply_volumn','param_change_day','param_rate_of_increase')
    df_param = pd.DataFrame(backtest)
    df['param_multiply_volumn'] = df['ticker'].map(df_param.set_index('ticker')['param_multiply_volumn'])
    df['param_change_day'] = df['ticker'].map(df_param.set_index('ticker')['param_change_day'])
    df['param_rate_of_increase'] = df['ticker'].map(df_param.set_index('ticker')['param_rate_of_increase'])
    buy = (df['close'] > df['tsi']) & (df['volume'] > df['mavol']*df['param_multiply_volumn']) & (df['mavol'] > 100000) & (df['high']/df['close']-1 < df['param_rate_of_increase']) & (df['close']/df['pre_close']-1 > df['param_change_day'])
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
    # get_info_stock_price_filter()
    date_filter = datetime.today().date() 
    stock_prices = StockPriceFilter.objects.all().values()
    # lọc ra top cổ phiếu có vol>100k
    df = pd.DataFrame(stock_prices)  
    df['mean_vol'] = df.groupby('ticker')['volume'].transform('mean')
    df =df.loc[df['mean_vol']>100000].reset_index(drop=True)
    df = df.drop(['id', 'mean_vol'], axis=1)
    # chuyển đổi df theo chiến lược
    df = breakout_strategy_otm(df, 20, 25)
    df['milestone'] = np.where(df['signal']== 1,df['res'],np.where(df['signal']== -1,df['sup'],0))
    df_signal = df.loc[(df['signal'] !=0)&(df['close']>3), ['ticker', 'date', 'signal','milestone']].sort_values('date', ascending=True).drop_duplicates(subset=['ticker']).reset_index(drop=True)
    signal_today = df_signal.loc[df_signal['date']==date_filter].reset_index(drop=True)
    account = Account.objects.get(name ='Bot_Breakout')
    bot = Bot(token='5881451311:AAEJYKo0ttHU0_Ztv3oGuf-rfFrGgajjtEk')
    group_id = '-967306064'

    if len(signal_today) > 0:
        for index, row in signal_today.iterrows():
            ticker = row['ticker']
            date = row['date']
            if row['signal'] ==1:
                signal = 'buy'
            else:
                signal = 'sell'
            milestone = row['milestone']
            
            lated_signal = Signaldaily.objects.filter(ticker=ticker,strategy='breakout' ).order_by('-date').first()
            #check nếu không có tín hiệu nào trước đó hoặc tín hiệu đã có nhưng ngược với tín hiệu hiện tại 
            if lated_signal is None or lated_signal.signal !=signal:
                created_signal = Signaldaily.objects.create(
                    ticker = ticker,
                    date=date, 
                    signal=signal,
                    strategy = 'breakout',
                    milestone=milestone)
                
            # tạo lệnh mua tự động
            if  signal== 'buy':
                close_price = StockPriceFilter.objects.filter(ticker = ticker).order_by('-date').first().close
                risk = account.ratio_risk
                nav = account.net_cash_flow +account.total_profit_close
                R = risk*nav  
                price= round((close_price*(1+0.002))/1000,0)
                qty= math.floor(nav*0.2/price)
                cut_loss_price  =  round((price - R/qty)/1000,2)
                take_profit_price = round((price + 2*R/qty)/1000,2)
                try:
                    created_transation = Transaction.objects.create(
                        account= account,
                        stock= ticker,
                        position='buy',
                        price= price,
                        qty=qty,
                        cut_loss_price =cut_loss_price,
                        take_profit_price=take_profit_price,
                        description = 'Auto trade' )
                except Exception as e:
                    # chat_id = account.bot.chat_id
                    bot = Bot(token=account.bot.token)
                    bot.send_message(
                    chat_id='-870288807', 
                    text=f"Tự động giao dịch {ticker} theo chiến lược breakout thất bại, lỗi {e}   ")    
            # gửi tín hiệu vào telegram
                back_test= OverviewBreakoutBacktest.objects.filter(ticker=ticker).first()
                if back_test:
                    bot.send_message(
                    chat_id=group_id, 
                    text=f"Tín hiệu mua {ticker}, lịch sử backtest với tổng số deal {back_test.total_trades} có lợi nhuận {back_test.ratio_pln}%, tỷ lệ thắng là {back_test.win_trade_ratio}% " )  
    else:
        bot.send_message(
                    chat_id=group_id, 
                    text=f"Không có cổ phiếu thỏa mãn tiêu chí breakout được lọc trong ngày {date_filter} ")  
    return          




