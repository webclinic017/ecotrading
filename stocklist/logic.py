import math
import re
import numpy as np
from datetime import datetime, timedelta
import pandas as pd
from portfolio.models import *
from telegram import Bot
from django.db.models import F
from stocklist.models import  *
import talib
import numpy as np
import requests
from bs4 import BeautifulSoup
from stocklist.divergences import *
from django.db.models import Avg


risk =0.03

def save_fa_valuation():
    fa = StockFundamentalData.objects.all()
    for self in fa:
        stock = StockPriceFilter.objects.filter(ticker = self.ticker).order_by('-date_time').first()
        if stock:
            self.market_price = stock.close
        if self.bvps and self.market_price :
            self.p_b = round(self.market_price*1000/self.bvps,2)
            #dept từ 0-1: 80-100 điểm, 1-5: 50-80 điểm, 5-10: 20 - 50, trên 10: 20
            if self.p_b > 0 and self.p_b <=1 :
                rating_pb = 100 - (self.p_b-0) /(1-0)*(100-80)
            elif self.p_b >1 and self.p_b<=10:
                rating_pb = 80 - (self.p_b-1) /(10-1)*(80-50)
            elif self.p_b >10:
                rating_pb = 40
            else:
                rating_pb = 0
        else:
            rating_pb = 0
        if self.eps and self.market_price:
            self.p_e = round(self.market_price*1000/self.eps,2)
            #dept từ 0-1: 80-100 điểm, 1-5: 50-80 điểm, 5-10: 20 - 50, trên 10: 20
            if self.p_e > 0 and self.p_e <=1 :
                rating_pe = 100 - (self.p_e-0) /(1-0)*(100-80)
            elif self.p_e >1 and self.p_e<=10:
                rating_pe = 80 - (self.p_e-1) /(10-1)*(80-50)
            elif self.p_e >10:
                rating_pe = 40
            else:
                rating_pe = 0
        else:
            rating_pe = 0
        self.valuation_rating  = round(rating_pb*0.5+rating_pe*0.5,2)
        self.fundamental_rating = round(self.growth_rating*0.5 + self.valuation_rating*0.3 + self.stable_rating*0.2,2)
        self.save()


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

def calculate_sma(group):
    return group['close'].rolling(window=group['param_sma']).mean()

def accumulation_model(ticker, period=5):
    stock_prices = StockPriceFilter.objects.filter(ticker =ticker).values()
    df = pd.DataFrame(stock_prices) 
    df = df.sort_values(by='date', ascending=True).reset_index(drop=True)
    # Tính toán đường trung bình động với số điểm dữ liệu window
    df['sma'] = talib.EMA(df['close'], timeperiod=period)
    #Tính toán độ dốc của đường trung bình động
    df['gradients'] = np.gradient(df['sma'])
    df = df.sort_values(by='date', ascending=False).reset_index(drop=True)
    gradients = df['gradients'].to_numpy()
    # Xác định mô hình tích lũy
    len_sideway =[]
    for item in gradients[1:]:
        sideway=True
        if item >0.1 or item <-0.1:
            sideway= False
            break
        else:
            len_sideway.append(item)
    return len(len_sideway)


def accumulation_model_df(df):
    df = df.sort_values(by=['ticker', 'date'], ascending=True).reset_index(drop=True)
    df['ema'] = df.groupby('ticker')['close'].transform(lambda x: talib.EMA(x, timeperiod=5))
    ema_counts = df.groupby("ticker")["ema"].count()
    tickers_with_4_ema_rows = ema_counts[ema_counts <= 4].index.tolist()
    df= df[~df['ticker'].isin(tickers_with_4_ema_rows)]
    df['gradients'] = df.groupby('ticker')['ema'].transform(lambda x: np.gradient(x))
    df['len_sideway'] = 0
    threshold = 0.1
    current_ticker = None
    current_count = 0
    for index, row in df.iterrows():
        if current_ticker != row['ticker']:
            current_ticker = row['ticker']
            current_count = 0  
            limit_count = 0
        if abs(row['gradients']) > threshold:
            limit_count += 1
        else:            
            current_count += 1
        if limit_count > 2:
            current_count = 0
            limit_count = 0
        df.at[index, 'len_sideway'] = current_count
    return df

def breakout_strategy(df, period, num_raw=None):
    df = df.drop(df[(df['open'] == 0) & (df['close'] == 0)& (df['volume'] == 0)].index)
    df = accumulation_model_df(df)
    df = df.groupby('ticker', group_keys=False).apply(lambda x: x.sort_values('date', ascending=False).head(num_raw) if num_raw is not None else x.sort_values('date', ascending=False))
    df['res'] = df.groupby('ticker')['high'].transform(lambda x: x[::-1].rolling(window=period).max()[::-1])
    df['sup'] = df.groupby('ticker')['low'].transform(lambda x: x[::-1].rolling(window=period).min()[::-1])
    df['mavol'] = df.groupby('ticker')['volume'].transform(lambda x: x[::-1].rolling(window=period).mean()[::-1])
    df['sma'] = df.groupby('ticker')['close'].transform(lambda x: x[::-1].rolling(window=period).mean()[::-1])
    df = df.groupby('ticker', group_keys=False).apply(add_test_value)
    df['tsi'].fillna(method='ffill', inplace=True)
    df['pre_close'] = df.groupby('ticker')['close'].shift(-1)
    df['len_sideway'] = df.groupby('ticker')['len_sideway'].shift(-1)
    return df

def breakout_strategy_otmed(df, risk):
    strategy= StrategyTrading.objects.filter(name = 'Breakout ver 0.2', risk = risk).first()
    period = strategy.period
    num_raw =period + 5
    backtest = ParamsOptimize.objects.filter(strategy = strategy).values('ticker','param1','param2','param3','param4','param5','param6')
    df_param = pd.DataFrame(backtest)
    df['mean_vol'] = df.groupby('ticker')['volume'].transform('mean')
    df =df.loc[df['mean_vol']>50000].reset_index(drop=True)
    df = df.drop(['id', 'mean_vol'], axis=1)
    df['param_sma'] = df['ticker'].map(df_param.set_index('ticker')['param5'])
    df = df.drop(df[(df['open'] == 0) & (df['close'] == 0) & (df['volume'] == 0) | pd.isna(df['param_sma'])].index)
    df = accumulation_model_df(df)
    df = df.groupby('ticker', group_keys=False).apply(lambda x: x.sort_values('date', ascending=False).head(num_raw) if num_raw is not None else x.sort_values('date', ascending=False))
    df =df.reset_index(drop =True)
    df['param_multiply_volumn'] = df['ticker'].map(df_param.set_index('ticker')['param1'])
    df['param_change_day'] = df['ticker'].map(df_param.set_index('ticker')['param3'])
    df['param_rate_of_increase'] = df['ticker'].map(df_param.set_index('ticker')['param2'])
    df['param_ratio_cutloss'] = df['ticker'].map(df_param.set_index('ticker')['param4'])
    df['param_len_sideway'] = df['ticker'].map(df_param.set_index('ticker')['param6'])
    df['res'] = df.groupby('ticker')['high'].transform(lambda x: x[::-1].rolling(window=period).max()[::-1])
    df['sup'] = df.groupby('ticker')['low'].transform(lambda x: x[::-1].rolling(window=period).min()[::-1])
    df['mavol'] = df.groupby('ticker')['volume'].transform(lambda x: x[::-1].rolling(window=period).mean()[::-1])
    df['pre_close'] = df.groupby('ticker')['close'].shift(-1)
    df['sma'] = df.groupby('ticker').apply(
        lambda x: x['close'][::-1].rolling(window=x['param_sma'].astype(int).values[0]).mean()[::-1]).reset_index(drop=True)
    df = df.groupby('ticker', group_keys=False).apply(add_test_value)
    df['tsi'].fillna(method='ffill', inplace=True)
    buy = (df['close'] > 5) & (df['close'] > df['sma']) & (df['close'] > df['tsi']) & (df['volume'] > df['mavol']*df['param_multiply_volumn']) &  (df['mavol'] > 100000) & (df['high']/df['close']-1 < df['param_rate_of_increase']) & (df['close']/df['pre_close']-1 > df['param_change_day']) &(df['len_sideway']> df['param_len_sideway'])
    # cut_loss = df['close'] <= df['close']*(1-df['param_ratio_cutloss'])
    df['signal'] = np.where(buy, 'buy', 'newtral')
    return df




def date_filter_breakout_strategy(df, risk, date_filter, strategy):
    df = breakout_strategy_otmed(df, risk)
    df['milestone'] = np.where(df['signal']== 'buy',df['res'],0)
    df_signal = df.loc[(df['signal'] =='buy')&(df['close']>3), ['ticker','close', 'date', 'signal','milestone','param_ratio_cutloss','len_sideway']].sort_values('date', ascending=True)
    signal_today = df_signal.loc[pd.to_datetime(df_signal['date']).dt.date==date_filter].reset_index(drop=True)
    buy_today =[]
    if len(signal_today) > 0:
        for index, row in signal_today.iterrows():
            data = {}
            data['strategy'] = strategy
            data['ticker'] = row['ticker']
            data['close'] = row['close']
            data['date'] = row['date']
            data['signal'] = 'Mua mới'
            data['milestone'] = row['milestone']
            data['ratio_cutloss'] = round(row['param_ratio_cutloss']*100,0)
            data['accumulation'] = row['len_sideway']
            signal_previous = Signaldaily.objects.filter(ticker=data['ticker'],strategy=strategy ,is_closed =False ).order_by('-date').first()
            if signal_previous:
                data['signal'] = 'Tăng tỷ trọng'
            lated_signal = Signaldaily.objects.filter(ticker=data['ticker'],strategy=strategy , date = date_filter).order_by('-date').first()
            #check nếu không có tín hiệu nào trước đó hoặc tín hiệu đã có nhưng ngược với tín hiệu hiện tại 
            if lated_signal is None:
                back_test= OverviewBacktest.objects.filter(ticker=data['ticker'],strategy=strategy).first()
                fa = StockFundamentalData.objects.filter(ticker =data['ticker'] ).first()
                if back_test:
                    data['rating'] = back_test.rating_total
                    data['fundamental'] = fa.fundamental_rating
                    if data['rating'] > 50 and data['fundamental']> 50:
                        buy_today.append(data)
    # tạo lệnh mua tự động
    buy_today.sort(key=lambda x: x['rating'], reverse=True)
    bot = Bot(token='5881451311:AAEJYKo0ttHU0_Ztv3oGuf-rfFrGgajjtEk')
    for index, row in signal_today.iterrows():
           # gửi tín hiệu vào telegram
            bot.send_message(
                chat_id='-870288807', 
                text=f"Tín hiệu {row['signal']} cp {row['ticker']}, chiến lược breakout" )   
    return buy_today

def tenisball_strategy(df):
    df = df.sort_values('date', ascending=True)
    df['Morning_Star'] = talib.CDLMORNINGSTAR(df['open'], df['high'], df['low'], df['close'])
    df['Bullish_Harami'] = talib.CDLHARAMI(df['open'], df['high'], df['low'], df['close'])
    df['Piercing_Line'] = talib.CDLPIERCING(df['open'], df['high'], df['low'], df['close'])
    df['Hammer'] = talib.CDLHAMMER(df['open'], df['high'], df['low'], df['close'])
    df['Bullish_Engulfing'] = talib.CDLENGULFING(df['open'], df['high'], df['low'], df['close'])
    df['Dragonfly_Doji'] = talib.CDLDRAGONFLYDOJI(df['open'], df['high'], df['low'], df['close'])
    df['Morning_Star_Doji'] = talib.CDLMORNINGDOJISTAR(df['open'], df['high'], df['low'], df['close'])
    df['Inverted_Hammer'] = talib.CDLINVERTEDHAMMER(df['open'], df['high'], df['low'], df['close'])
    df['pattern_rating']= df['Morning_Star']+df['Bullish_Harami'] +df['Piercing_Line']+df['Hammer']+df['Bullish_Engulfing']+df['Dragonfly_Doji']+df['Morning_Star_Doji']+df['Inverted_Hammer']
    df['ma200'] = df['close'].rolling(window=200).mean()
    df['mavol'] = df['volume'].rolling(window=200).mean()
    df['top'] = df['high'].rolling(window=5).max()
    df = df.sort_values('date', ascending=False)
    return df

def tenisball_strategy_otmed(df, risk):
    strategy= StrategyTrading.objects.filter(name = 'Tenisball_ver0.1', risk = risk).first()
    period = strategy.period
    backtest = ParamsOptimize.objects.filter(strategy = strategy).values('ticker','param1','param2','param3','param4')
    df_param = pd.DataFrame(backtest)
    df = df.sort_values('date', ascending=True)
    df = df.drop(['id','date_time'], axis=1)
    df['param_ma_backtest'] = df['ticker'].map(df_param.set_index('ticker')['param1'])
    df['param_ratio_backtest'] = df['ticker'].map(df_param.set_index('ticker')['param2'])
    df['param_ratio_cutloss'] = df['ticker'].map(df_param.set_index('ticker')['param3'])
    df['param_pattern_rating'] = df['ticker'].map(df_param.set_index('ticker')['param4'])
    df['Morning_Star'] = talib.CDLMORNINGSTAR(df['open'], df['high'], df['low'], df['close'])
    df['Bullish_Harami'] = talib.CDLHARAMI(df['open'], df['high'], df['low'], df['close'])
    df['Piercing_Line'] = talib.CDLPIERCING(df['open'], df['high'], df['low'], df['close'])
    df['Hammer'] = talib.CDLHAMMER(df['open'], df['high'], df['low'], df['close'])
    df['Bullish_Engulfing'] = talib.CDLENGULFING(df['open'], df['high'], df['low'], df['close'])
    df['Dragonfly_Doji'] = talib.CDLDRAGONFLYDOJI(df['open'], df['high'], df['low'], df['close'])
    df['Morning_Star_Doji'] = talib.CDLMORNINGDOJISTAR(df['open'], df['high'], df['low'], df['close'])
    df['Inverted_Hammer'] = talib.CDLINVERTEDHAMMER(df['open'], df['high'], df['low'], df['close'])
    df['pattern_rating']= df['Morning_Star']+df['Bullish_Harami'] +df['Piercing_Line']+df['Hammer']+df['Bullish_Engulfing']+df['Dragonfly_Doji']+df['Morning_Star_Doji']+df['Inverted_Hammer']
    df['ma200'] = df['close'].rolling(window=200).mean()
    df['top'] = df['high'].rolling(window=5).max()
    df['mavol'] = df['volume'].rolling(window=20).mean()
    buy_trend = df['close'] > df['ma200'] #done
    buy_decrease = df['close'] < df['top'] #done
    buy_minvol =df['mavol'] > 100000 #done
    buy_pattern= df['pattern_rating'] >= df['param_pattern_rating'] #done
    buy_backtest_ma = df['close'] >= df['param_ma_backtest'] *df['param_ratio_backtest'] #done
    # signal_df=df[(df['pattern_rating'] >= df['param_pattern_rating'])&(df['mavol']>100000)&(df['close']>df['ma200'])&(df['close'] < df['top'])&(df['close'] >= df['param_ma_backtest'] *df['param_ratio_backtest'])]
    buy =  buy_trend & buy_decrease & buy_minvol & buy_pattern & buy_backtest_ma
    # cut_loss = df['close'] <= df['close']*(1-df['param_ratio_cutloss'])
    df['signal'] = np.where(buy, 'buy', 'newtral')
    return df

    



def date_filter_tenisball_strategy(df, risk, date_filter, strategy):
    df = tenisball_strategy_otmed(df, risk)
    df_signal = df.loc[(df['close']>3)&(df['signal']=='buy'), ['ticker','close', 'date','signal','param_ratio_cutloss']].sort_values('date', ascending=True)
    signal_today = df_signal.loc[pd.to_datetime(df_signal['date']).dt.date==date_filter].reset_index(drop=True)
    buy_today =[]
    if len(signal_today) > 0:
        for index, row in signal_today.iterrows():
            data = {}
            data['strategy'] = strategy
            data['accumulation'] = 0
            data['ticker'] = row['ticker']
            data['close'] = row['close']
            data['date'] = row['date']
            data['signal'] = 'Mua mới'
            data['ratio_cutloss'] = round(row['param_ratio_cutloss']*100,0)
            signal_previous = Signaldaily.objects.filter(ticker=data['ticker'],strategy=strategy ,is_closed =False ).order_by('-date').first()
            if signal_previous:
                data['signal'] = 'Tăng tỷ trọng'
            lated_signal = Signaldaily.objects.filter(ticker=data['ticker'],strategy=strategy , date = date_filter).order_by('-date').first()
            #check nếu không có tín hiệu nào trước đó hoặc tín hiệu đã có nhưng ngược với tín hiệu hiện tại 
            if lated_signal is None:
                back_test= OverviewBacktest.objects.filter(ticker=data['ticker'],strategy=strategy).first()
                fa = StockFundamentalData.objects.filter(ticker =data['ticker'] ).first()
                if back_test:
                    data['rating'] = back_test.rating_total
                    data['fundamental'] = fa.fundamental_rating
                    if data['rating'] > 50 and data['fundamental']> 50:
                        buy_today.append(data)
    # tạo lệnh mua tự động
    buy_today.sort(key=lambda x: x['rating'], reverse=True)
    bot = Bot(token='5881451311:AAEJYKo0ttHU0_Ztv3oGuf-rfFrGgajjtEk')
    for index, row in signal_today.iterrows():
           # gửi tín hiệu vào telegram
            bot.send_message(
                chat_id='-870288807', 
                text=f"Tín hiệu {row['signal']} cp {row['ticker']}, chiến lược tenisball" )   
    return buy_today


def detect_divergences(P=20, order=5, K=2):
    bot = Bot(token='5881451311:AAEJYKo0ttHU0_Ztv3oGuf-rfFrGgajjtEk')
    stock_source = StockPriceFilter.objects.values('ticker').annotate(avg_volume=Avg('volume'))
    stock_test= [ticker for ticker in stock_source if ticker['avg_volume'] > 100000]
    mesage =''
    for item in stock_test:
        stock_prices = StockPriceFilter.objects.filter(ticker=item['ticker']).values()
        df = pd.DataFrame(stock_prices)
        data = df.drop(columns=['id','date_time','open','low','high','volume'])
        data =  data.sort_values('date').reset_index(drop=True)
        df = RSIDivergenceStrategy(data, P, order, K)
        date_filter = datetime.today().date()
        df_today = df[(pd.to_datetime(df['date']).dt.date == date_filter) & (df['signal'] !='')]
        if len(df_today)>0:
            df_today = df_today[['ticker','signal']].reset_index(drop =True)
            mesage += f"Cổ phiếu {df_today['ticker'][0]} có tín hiệu {df_today['signal'][0]}"
        bot.send_message(
                chat_id='-870288807', 
                text=mesage)
    return mesage




# phải trước đó là đỉnh hoặc đáy cùng loại

def filter_stock_muanual( risk):
    print('đang chạy')
    strategy_1='Breakout ver 0.2'
    strategy_2='Tenisball_ver0.1'
    strategy_breakout= StrategyTrading.objects.filter(name =strategy_1 , risk = risk).first()
    strategy_tenisball= StrategyTrading.objects.filter(name =strategy_2 , risk = risk).first()
    now = datetime.today()
    date_filter = now.date()
    # Lấy ngày giờ gần nhất trong StockPriceFilter
    latest_update = StockPriceFilter.objects.all().order_by('-date').first().date_time
    # Tính khoảng thời gian giữa now và latest_update (tính bằng giây)
    time_difference = (now - latest_update).total_seconds()
    close_section = datetime(now.year, now.month, now.day, 15, 0, 0)  # Tạo thời điểm 15:00:00 cùng ngày
    open_section = datetime(now.year, now.month, now.day, 9, 0, 0)  # Tạo thời điểm 15:00:00 cùng ngày
    # Kiểm tra điều kiện để thực hiện hàm get_info_stock_price_filter()
    if 0 <= now.weekday() <= 4 and open_section <= now <= close_section and time_difference > 900:
        get_info_stock_price_filter()
        print('tải data xong')
        save_fa_valuation()
    else:
        print('Không cần tải data')
    
    stock_prices = StockPriceFilter.objects.all().values()
    # lọc ra top cổ phiếu có vol>100k
    df = pd.DataFrame(stock_prices)  
    df['date']= pd.to_datetime(df['date']).dt.date
    # chuyển đổi df theo chiến lược
    breakout_buy_today = date_filter_breakout_strategy(df, risk, date_filter, strategy_breakout)
    tenisball_buy_today = date_filter_tenisball_strategy(df, risk, date_filter, strategy_tenisball)
    buy_today = breakout_buy_today+tenisball_buy_today
    print('Cổ phiếu là:', buy_today)
    return buy_today
     


def filter_stock_daily(risk=0.03):
    buy_today = filter_stock_muanual(risk)
    date_filter = datetime.today().date() 
    account = Account.objects.get(name ='Bot_Breakout')
    external_room = ChatGroupTelegram.objects.filter(type = 'external',is_signal =True,rank ='1' )
    num_stock = len(buy_today)
    max_signal = min(num_stock, 5)
    if max_signal ==0:
        for group in external_room:
            bot = Bot(token=group.token.token)
            try:
                bot.send_message(
                    chat_id=group.chat_id, #room Khách hàng
                    text=f"Không có cổ phiếu thỏa mãn tiêu chí được lọc trong ngày {date_filter} ")  
            except:
                pass
    else:
        for ticker in buy_today[:max_signal]:
            price = StockPriceFilter.objects.filter(ticker = ticker['ticker']).order_by('-date').first().close
            # risk = account.ratio_risk
            # nav = account.net_cash_flow +account.total_profit_close
            # R = risk*nav  
            cut_loss_price = round(price*(100-ticker['ratio_cutloss'])/100,2)
            take_profit_price = round(price*(1+ticker['ratio_cutloss']/100*2),2)
            # qty= math.floor(R/(price*ticker['ratio_cutloss']*1000))
            analysis = FundamentalAnalysis.objects.filter(ticker__ticker=ticker['ticker']).order_by('-modified_date').first()
            response = ''
            if ticker['strategy'] =='tenisball':
                response +=f"Tín hiệu {ticker['signal']} cp {ticker['ticker']} theo chiến lược {ticker['strategy']} , tỷ lệ cắt lỗ tối ưu là {ticker['ratio_cutloss']}%,  điểm tổng hợp là {ticker['rating']}, điểm cơ bản là {ticker['fundamental']}"
                ticker['milestone'] =0
            else:
                response +=f"Tín hiệu {ticker['signal']} cp {ticker['ticker']} theo chiến lược {ticker['strategy']}, tỷ lệ cắt lỗ tối ưu là {ticker['ratio_cutloss']}%,  điểm tổng hợp là {ticker['rating']}, điểm cơ bản là {ticker['fundamental']}, số ngày tích lũy trước tăng là {ticker['accumulation']}"
            if analysis and analysis.modified_date >= (datetime.now() - timedelta(days=6 * 30)):
                response +=f"Thông tin cổ phiếu {ticker['ticker']}:\n"
                response += f"Ngày báo cáo {analysis.date}. P/E: {analysis.ticker.p_e}, P/B: {analysis.ticker.p_b}, Định giá {analysis.valuation}:\n"
                response += f"{analysis.info}.\n"
                response += f"Nguồn {analysis.source}"
            try:
                # created_transation = Transaction.objects.create(
                #             account= account,
                #             stock= ticker['ticker'],
                #             position='buy',
                #             price= price,
                #             qty=qty,
                #             cut_loss_price =cut_loss_price,
                #             take_profit_price=take_profit_price,
                #             description = 'Auto trade' )     
                created = Signaldaily.objects.create(
                        ticker = ticker['ticker'],
                        close = ticker['close'],
                        date = ticker['date'],
                        milestone =ticker['milestone'],
                        signal = ticker['signal'],
                        ratio_cutloss = round(ticker['ratio_cutloss'],2),
                        strategy = ticker['strategy'],
                        take_profit_price = take_profit_price,
                        cutloss_price =cut_loss_price,
                        exit_price = cut_loss_price,
                        rating_total = ticker['rating'],
                        rating_fundamental = ticker['fundamental'] ,
                        accumulation = ticker['accumulation']
                    )
                for group in external_room:
                        bot = Bot(token=group.token.token)
                        try:
                            bot.send_message(
                                chat_id=group.chat_id,
                                text= response)    
                        except:
                            pass
            except Exception as e:
                        # chat_id = account.bot.chat_id
                        bot = Bot(token=account.bot.token)
                        bot.send_message(
                        chat_id='-870288807', #room nội bộ
                        text=f"Không gửi được tín hiệu {ticker['ticker']}, lỗi {e}   ")        
    detect_divergences(P=20, order=5, K=2)
    return 


def save_event_stock(stock):
    list_event =[]
    linkbase= 'https://www.stockbiz.vn/MarketCalendar.aspx?Symbol='+ stock
    r = requests.get(linkbase)
    soup = BeautifulSoup(r.text,'html.parser')
    table = soup.find('table', class_='dataTable')  # Tìm bảng chứa thông tin
    if table:
        rows = table.find_all('tr')  # Lấy tất cả các dòng trong bảng (loại bỏ dòng tiêu đề)
        cash_value= 0
        stock_value=0
        stock_option_value=0
        price_option_value=0
        dividend_type = 'order'
        for row in rows[1:]:  # Bắt đầu từ vị trí thứ hai (loại bỏ dòng tiêu đề)
            dividend  = {}
            columns = row.find_all('td')  # Lấy tất cả các cột trong dòng
            if len(columns) >= 3:  # Kiểm tra số lượng cột
                dividend['ex_rights_date'] = columns[0].get_text(strip=True)
                dividend['event'] = columns[4].get_text(strip=True)
                list_event.append(dividend)
                event = dividend['event'].lower()
                ex_rights_date = datetime.strptime(dividend['ex_rights_date'], '%d/%m/%Y').date()
                if ex_rights_date == datetime.now().date():
                    if 'tiền' in event:
                        dividend_type = 'cash'
                        cash = re.findall(r'\d+', event)  # Tìm tất cả các giá trị số trong chuỗi
                        if cash:
                            value1 = int(cash[-1])/1000  # Lấy giá trị số đầu tiên
                            cash_value += value1
                    elif 'cổ phiếu' in event and 'phát hành' not in event:
                        dividend_type = 'stock'
                        stock_values = re.findall(r'\d+', event)
                        if stock_values:
                            value2 = int(stock_values[-1])/int(stock_values[-2])
                            stock_value += value2
                    elif 'cổ phiếu' in event and 'giá' in event and 'tỷ lệ' in event:
                        dividend_type = 'option'
                        option = re.findall(r'\d+', event)
                        if option:
                                stock_option_value = int(option[-2])/int(option[-3])
                                price_option_value = int(option[-1])
        if dividend_type == 'order':
            pass
        else:
            DividendManage.objects.update_or_create(
                        ticker= stock,  # Thay thế 'Your_Ticker_Value' bằng giá trị ticker thực tế
                        date_apply=ex_rights_date,
                        defaults={
                            'type': dividend_type,
                            'cash': cash_value,
                            'stock': stock_value,
                            'price_option': price_option_value,
                            'stock_option':stock_option_value
                        }
                    )
    return list_event

def check_dividend():
    signal = Signaldaily.objects.filter(is_closed = False)
    for stock in signal:
        dividend = save_event_stock(stock.ticker)
    dividend_today = DividendManage.objects.filter(date_apply =datetime.now().date() )
    for i in dividend_today:
        i.save()
        
    
def check_update_analysis_and_send_notifications():
    # Lọc các bản ghi có modified_date max trong cùng ticker
    filtered_records = []
    # Lấy danh sách các ticker và modified_date max
    latest_records = FundamentalAnalysis.objects.values('ticker').annotate(max_modified_date=Max('modified_date'))
    for record in latest_records:
        ticker = record['ticker']
        max_modified_date = record['max_modified_date']
        ticker_records = FundamentalAnalysis.objects.filter(ticker=ticker, modified_date=max_modified_date)
        filtered_records.extend(ticker_records)
    # Lọc các record có modified_date max có ngày nhỏ hơn ngày hiện tại - 90 ngày
    current_date = datetime.now()
    threshold_date = current_date - timedelta(days=90)
    records_to_notify = [record for record in filtered_records if record.modified_date <= threshold_date]
    for record in records_to_notify:
        bot = Bot(token='5881451311:AAEJYKo0ttHU0_Ztv3oGuf-rfFrGgajjtEk')
        bot.send_message(
                chat_id='-870288807', 
                text=f"Cổ phiếu {record.ticker} đã quá 3 tháng chưa có cập nhật thông tin mới, hãy cập nhật ngay nhé Vũ/Thạch ơi!!!" )   


