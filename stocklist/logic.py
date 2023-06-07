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
    df['sma'] = df.groupby('ticker')['close'].transform(lambda x: x[::-1].rolling(window=period).mean()[::-1])
    df = df.groupby('ticker', group_keys=False).apply(add_test_value)
    df['tsi'].fillna(method='ffill', inplace=True)
    df['pre_close'] = df.groupby('ticker')['close'].shift(-1)
    return df

def breakout_strategy_otmed(df, period, num_raw=None):
    df = breakout_strategy(df, period, num_raw)  # Gọi hàm breakout_strategy từ trong hàm breakout_strategy_otm
    # Tiếp tục thêm các phần xử lý riêng cho hàm breakout_strategy_otm
    backtest = ParamsOptimize.objects.values('ticker','multiply_volumn','rate_of_increase','change_day','risk','ratio_cutloss','sma')
    df_param = pd.DataFrame(backtest)
    df['param_multiply_volumn'] = df['ticker'].map(df_param.set_index('ticker')['multiply_volumn'])
    df['param_change_day'] = df['ticker'].map(df_param.set_index('ticker')['change_day'])
    df['param_rate_of_increase'] = df['ticker'].map(df_param.set_index('ticker')['rate_of_increase'])
    df['param_ratio_cutloss'] = df['ticker'].map(df_param.set_index('ticker')['ratio_cutloss'])
    df['param_sma'] = df['ticker'].map(df_param.set_index('ticker')['sma'])
    buy =(df['close'] > df['sma'])& (df['close'] > df['tsi']) & (df['volume'] > df['mavol']*df['param_multiply_volumn']) & (df['mavol'] > 100000) & (df['high']/df['close']-1 < df['param_rate_of_increase']) & (df['close']/df['pre_close']-1 > df['param_change_day'])
    cut_loss = df['close'] <= df['close']*(1-df['param_ratio_cutloss'])
    df['signal'] = np.where(buy, 'buy', 'newtral')
    return df



def filter_stock_muanual():
    now = datetime.today()
    date_filter = now.date()
    # Lấy ngày giờ gần nhất trong StockPriceFilter
    latest_update = StockPriceFilter.objects.all().order_by('-date').first().date_time
    # Tính khoảng thời gian giữa now và latest_update (tính bằng giây)
    time_difference = (now - latest_update).total_seconds()
    # Kiểm tra điều kiện để thực hiện hàm get_info_stock_price_filter()
    if 0 <= now.weekday() <= 4 and 9 <= now.hour <= 15 and time_difference > 900:
        get_info_stock_price_filter()

    stock_prices = StockPriceFilter.objects.all().values()
    # lọc ra top cổ phiếu có vol>100k
    df = pd.DataFrame(stock_prices)  
    df['mean_vol'] = df.groupby('ticker')['volume'].transform('mean')
    df =df.loc[df['mean_vol']>100000].reset_index(drop=True)
    df = df.drop(['id', 'mean_vol'], axis=1)
    # chuyển đổi df theo chiến lược
    df = breakout_strategy_otmed(df, 20, 25)
    df['milestone'] = np.where(df['signal']== 'buy',df['res'],0)
    df_signal = df.loc[(df['signal'] =='buy')&(df['close']>3), ['ticker', 'date', 'signal','milestone','param_ratio_cutloss']].sort_values('date', ascending=True).drop_duplicates(subset=['ticker']).reset_index(drop=True)
    signal_today = df_signal.loc[df_signal['date']==date_filter].reset_index(drop=True)
    bot = Bot(token='5881451311:AAEJYKo0ttHU0_Ztv3oGuf-rfFrGgajjtEk')
    buy_today =[]
    if len(signal_today) > 0:
        for index, row in signal_today.iterrows():
            data = {}
            data['ticker'] = row['ticker']
            data['date'] = row['date']
            data['signal'] = 'buy'
            data['milestone'] = row['milestone']
            data['ratio_cutloss'] = row['param_ratio_cutloss']
            lated_signal = Signaldaily.objects.filter(ticker=data['ticker'],strategy='breakout' , date = date_filter).order_by('-date').first()
            #check nếu không có tín hiệu nào trước đó hoặc tín hiệu đã có nhưng ngược với tín hiệu hiện tại 
            if lated_signal is None:
                back_test= OverviewBacktest.objects.filter(ticker=data['ticker']).first()
                if back_test:
                    data['total_trades'] =back_test.total_trades
                    data['ratio_pln'] = back_test.ratio_pln
                    data['win_trade_ratio'] = back_test.win_trade_ratio
                    data['rating'] = data['ratio_pln']
                    if data['ratio_pln'] > 10 and data['win_trade_ratio']>40:
                        buy_today.append(data)

    # tạo lệnh mua tự động
    buy_today.sort(key=lambda x: x['rating'], reverse=True)
    for ticker in buy_today:
           # gửi tín hiệu vào telegram
            bot.send_message(
                chat_id='-870288807', 
                text=f"Tín hiệu mua {ticker['ticker']}, lịch sử backtest với tổng số deal {ticker['total_trades']} có lợi nhuận {ticker['ratio_pln']}%, tỷ lệ thắng là {ticker['win_trade_ratio']}% " )   
    return buy_today
     

def filter_stock_daily():
    buy_today = filter_stock_muanual()
    date_filter = datetime.today().date() 
    account = Account.objects.get(name ='Bot_Breakout')
    external_room = ChatGroupTelegram.objects.filter(type = 'external',is_signal =True,rank ='1' )
    num_stock = len(buy_today)
    max_signal = min(num_stock, 5)
    max_trade =min(num_stock, 3)
    if max_trade ==0:
        for group in external_room:
            bot = Bot(token=group.token.token)
            try:
                bot.send_message(
                    chat_id=group.chat_id, #room Khách hàng
                    text=f"Không có cổ phiếu thỏa mãn tiêu chí breakout được lọc trong ngày {date_filter} ")  
            except:
                pass
    else:
        for ticker in buy_today[:max_trade]:
                close_price = StockPriceFilter.objects.filter(ticker = ticker['ticker']).order_by('-date').first().close
                risk = account.ratio_risk
                nav = account.net_cash_flow +account.total_profit_close
                R = risk*nav  
                price= round(close_price*(1+0.002),0)
                cut_loss_price  =  round(price - price*ticker['ratio_cutloss'],2)
                qty= math.floor(R/(price*ticker['ratio_cutloss']*1000))
                take_profit_price = round((price + 2*price*ticker['ratio_cutloss']),2)
                try:
                        created_transation = Transaction.objects.create(
                            account= account,
                            stock= ticker['ticker'],
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
                        chat_id='-870288807', #room nội bộ
                        text=f"Tự động giao dịch {ticker['ticker']} theo chiến lược breakout thất bại, lỗi {e}   ")    
        for ticker in buy_today[:max_signal]:
           # gửi tín hiệu vào telegram
            for group in external_room:
                bot = Bot(token=group.token.token)
                try:
                    bot.send_message(
                    chat_id=group.chat_id, 
                    text=f"Tín hiệu mua {ticker['ticker']}, lịch sử backtest với tổng số deal {ticker['total_trades']} có lợi nhuận {ticker['ratio_pln']}%, tỷ lệ thắng là {ticker['win_trade_ratio']}%, tỷ lệ cắt lỗ tối ưu là giảm {ticker['ratio_cutloss']*100}% " )   
                except:
                    pass
        for ticker in buy_today:
             Signaldaily.objects.create(
                ticker = ticker['ticker'],
                date = ticker['date'],
                milestone =ticker['milestone'],
                signal = ticker['signal'],
                ratio_cutloss = ticker['ratio_cutloss'],
                strategy = 'breakout'
             )
             
    return          



