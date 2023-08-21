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
    strategy= StrategyTrading.objects.filter(name = 'Breakout ver 0.1', risk = risk).first()
    period = strategy.period
    num_raw =period + 5
    backtest = ParamsOptimize.objects.filter(strategy = strategy).values('ticker','multiply_volumn','rate_of_increase','change_day','ratio_cutloss','sma')
    df_param = pd.DataFrame(backtest)
    df['mean_vol'] = df.groupby('ticker')['volume'].transform('mean')
    df =df.loc[df['mean_vol']>100000].reset_index(drop=True)
    df = df.drop(['id', 'mean_vol'], axis=1)
    df['param_sma'] = df['ticker'].map(df_param.set_index('ticker')['sma'])
    df = df.drop(df[(df['open'] == 0) & (df['close'] == 0) & (df['volume'] == 0) | pd.isna(df['param_sma'])].index)
    df = df.groupby('ticker', group_keys=False).apply(lambda x: x.sort_values('date', ascending=False).head(num_raw) if num_raw is not None else x.sort_values('date', ascending=False))
    df =df.reset_index(drop =True)
    df['param_multiply_volumn'] = df['ticker'].map(df_param.set_index('ticker')['multiply_volumn'])
    df['param_change_day'] = df['ticker'].map(df_param.set_index('ticker')['change_day'])
    df['param_rate_of_increase'] = df['ticker'].map(df_param.set_index('ticker')['rate_of_increase'])
    df['param_ratio_cutloss'] = df['ticker'].map(df_param.set_index('ticker')['ratio_cutloss'])
    
    df['res'] = df.groupby('ticker')['high'].transform(lambda x: x[::-1].rolling(window=period).max()[::-1])
    df['sup'] = df.groupby('ticker')['low'].transform(lambda x: x[::-1].rolling(window=period).min()[::-1])
    df['mavol'] = df.groupby('ticker')['volume'].transform(lambda x: x[::-1].rolling(window=period).mean()[::-1])
    df['pre_close'] = df.groupby('ticker')['close'].shift(-1)
    df['sma'] = df.groupby('ticker').apply(
        lambda x: x['close'][::-1].rolling(window=x['param_sma'].astype(int).values[0]).mean()[::-1]).reset_index(drop=True)
    df = df.groupby('ticker', group_keys=False).apply(add_test_value)
    df['tsi'].fillna(method='ffill', inplace=True)
    buy =(df['close'] > 5) & (df['close'] > df['sma']) & (df['close'] > df['tsi']) & (df['volume'] > df['mavol']*df['param_multiply_volumn']) & (df['mavol'] > 100000) & (df['high']/df['close']-1 < df['param_rate_of_increase']) & (df['close']/df['pre_close']-1 > df['param_change_day'])
    cut_loss = df['close'] <= df['close']*(1-df['param_ratio_cutloss'])
    df['signal'] = np.where(buy, 'buy', 'newtral')
    return df

    
    
def filter_stock_muanual( risk = 0.03):
    print('đang chạy')
    strategy= StrategyTrading.objects.filter(name = 'Breakout ver 0.1', risk = risk).first()
    now = datetime.today()
    date_filter = now.date()
    # Lấy ngày giờ gần nhất trong StockPriceFilter
    latest_update = StockPriceFilter.objects.all().order_by('-date').first().date_time
    # Tính khoảng thời gian giữa now và latest_update (tính bằng giây)
    time_difference = (now - latest_update).total_seconds()
    # Kiểm tra điều kiện để thực hiện hàm get_info_stock_price_filter()
    if 0 <= now.weekday() <= 4 and 9 <= now.hour <= 15 and time_difference > 900:
        get_info_stock_price_filter()
        print('tải data xong')
        save_fa_valuation()
    stock_prices = StockPriceFilter.objects.all().values()
    # lọc ra top cổ phiếu có vol>100k
    df = pd.DataFrame(stock_prices)  
    # chuyển đổi df theo chiến lược
    df = breakout_strategy_otmed(df, risk)
    df['milestone'] = np.where(df['signal']== 'buy',df['res'],0)
    df_signal = df.loc[(df['signal'] =='buy')&(df['close']>3), ['ticker','close', 'date', 'signal','milestone','param_ratio_cutloss']].sort_values('date', ascending=True).drop_duplicates(subset=['ticker']).reset_index(drop=True)
    signal_today = df_signal.loc[df_signal['date']==date_filter].reset_index(drop=True)
    bot = Bot(token='5881451311:AAEJYKo0ttHU0_Ztv3oGuf-rfFrGgajjtEk')
    buy_today =[]
    if len(signal_today) > 0:
        for index, row in signal_today.iterrows():
            data = {}
            data['ticker'] = row['ticker']
            data['close'] = row['close']
            data['date'] = row['date']
            data['signal'] = 'Mua mới'
            data['milestone'] = row['milestone']
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
                    data['accumulation'] = accumulation_model(ticker=data['ticker'], period=5)
                    if data['rating'] > 50 and data['fundamental']> 50:
                        buy_today.append(data)
    # tạo lệnh mua tự động
    buy_today.sort(key=lambda x: x['rating'], reverse=True)
    for ticker in buy_today:
           # gửi tín hiệu vào telegram
            bot.send_message(
                chat_id='-870288807', 
                text=f"Tín hiệu {ticker['signal']} cp {ticker['ticker']}, điểm tổng hợp là {ticker['rating']}, điểm cơ bản là {ticker['fundamental']}, tỷ lệ cắt lỗ tối ưu là {ticker['ratio_cutloss']}% " )   
    print('Cổ phiếu là:', buy_today)
    return buy_today
     

def filter_stock_daily(risk=0.03):
    strategy = StrategyTrading.objects.filter(risk = risk, name ='Breakout ver 0.1').first()
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
                    text=f"Không có cổ phiếu thỏa mãn tiêu chí breakout được lọc trong ngày {date_filter} ")  
            except:
                pass
    else:
        for ticker in buy_today[:max_signal]:
            price = StockPriceFilter.objects.filter(ticker = ticker['ticker']).order_by('-date').first().close
            risk = account.ratio_risk
            nav = account.net_cash_flow +account.total_profit_close
            R = risk*nav  
            cut_loss_price = round(price*(100-ticker['ratio_cutloss'])/100,2)
            take_profit_price = round(price*(1+ticker['ratio_cutloss']/100*2),2)
            qty= math.floor(R/(price*ticker['ratio_cutloss']*1000))
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
                created = Signaldaily.objects.create(
                        ticker = ticker['ticker'],
                        close = ticker['close'],
                        date = ticker['date'],
                        milestone =ticker['milestone'],
                        signal = ticker['signal'],
                        ratio_cutloss = round(ticker['ratio_cutloss'],2),
                        strategy = strategy,
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
                            analysis = FundamentalAnalysis.objects.filter(ticker__ticker=ticker['ticker']).order_by('-modified_date').first()
                            if analysis and analysis.modified_date >= (datetime.now() - timedelta(days=6 * 30)):
                                response = f"Thông tin cổ phiếu {ticker['ticker']}:\n"
                                response += f"Ngày báo cáo {analysis.date}. P/E: {analysis.ticker.p_e}, P/B: {analysis.ticker.p_b}, Định giá {analysis.valuation}:\n"
                                response += f"{analysis.info}.\n"
                                response += f"Nguồn {analysis.source}"
                                bot.send_message(
                                chat_id=group.chat_id,
                                text=f"Tín hiệu {ticker['signal']} cp {ticker['ticker']}, tỷ lệ cắt lỗ tối ưu là {ticker['ratio_cutloss']}%,  điểm tổng hợp là {ticker['rating']}, điểm cơ bản là {ticker['fundamental']}, số ngày tích lũy trước tăng là {ticker['accumulation']}" )   
                                bot.send_message(
                                chat_id=group.chat_id,
                                text=response)   
                            else:
                                bot.send_message(
                                chat_id=group.chat_id,
                                text=f"Tín hiệu {ticker['signal']} cp {ticker['ticker']}, tỷ lệ cắt lỗ tối ưu là {ticker['ratio_cutloss']}%,  điểm tổng hợp là {ticker['rating']}, điểm cơ bản là {ticker['fundamental']}, số ngày tích lũy trước tăng là {ticker['accumulation']}" )   
                        except:
                            pass
            except Exception as e:
                        # chat_id = account.bot.chat_id
                        bot = Bot(token=account.bot.token)
                        bot.send_message(
                        chat_id='-870288807', #room nội bộ
                        text=f"Tự động giao dịch {ticker['ticker']} theo chiến lược breakout thất bại, lỗi {e}   ")        
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
        