import os
import re
import pandas as pd
from portfolio.models import SectorPrice, SectorListName
from posgress import *
import datetime
from telegram import Bot
from portfolio.models import ChatGroupTelegram, DateNotTrading
from bs4 import BeautifulSoup
import requests

def list_stock_by_sector(name,df_stock_sector,df_transaction):
    df_stock = df_stock_sector[df_stock_sector['name']==name]
    merged_df = df_stock.merge(df_transaction, left_on='stock', right_on='ticker', how='left')[['stock', 'value']]
    merged_df = merged_df.sort_values(by='value', ascending=False)
    final_df =merged_df[merged_df['value']>0]
    top_3_stocks = final_df.head(3)['stock'].to_list()
    return top_3_stocks

def print_text(message,list_sector,df_stock_sector,df_transaction):
    list_stock = [list_stock_by_sector(sector,df_stock_sector,df_transaction) for sector in list_sector]
    # Duyệt qua từng sector và danh sách stock tương ứng
    for sector, stocks in zip(list_sector, list_stock):
        stock_string = ", ".join(stocks)
        message += f" {sector} ({stock_string}),"
    # Loại bỏ dấu phẩy cuối cùng và in ra biến message
    message = message.rstrip(",") + "." + "\n"
    return message




def difine_previous_trading_date(date):
    while True:
        date = date - datetime.timedelta(days=1)
        weekday = date.weekday()
        check_in_dates = DateNotTrading.objects.filter(date=date).exists()
        if not check_in_dates and weekday not in (5, 6):
            return date


date = datetime.datetime.today().date()
bot = Bot(token='5881451311:AAEJYKo0ttHU0_Ztv3oGuf-rfFrGgajjtEk')
external_room = ChatGroupTelegram.objects.filter(type = 'external',is_signal =True,rank ='1' )

def round_number(number):
    rounded_number = round(number, -6)
    result = '{:,}'.format(int(str(rounded_number)[:-8]))
    return result

def status(number):
    if number >0:
            status ='Mua ròng'
    else:
            status ='Bán ròng'
    return status


def get_omo_info():
    linkbase= 'https://www.sbv.gov.vn/webcenter/portal/vi/menu/trangchu/hdtttt/ttm'
    r = requests.get(linkbase)
    soup = BeautifulSoup(r.text,'html.parser')
    data=[]
    rows = soup.find_all('td') 
    for td in rows:
        data.append(td.get_text(strip=True))
    x = data.index('KẾT QUẢ ĐẤU THẦU THỊ TRƯỜNG MỞ')
    y = data.index('Ghi chú:')
    data_new =data[x:y]
    data_new = [x for x in data_new if x != '']
    date_string  = data_new[1]
    # Tách thành phần ngày, tháng và năm từ chuỗi
    date_components = date_string.split()
    day = int(date_components[1])
    month = int(date_components[3])
    year = int(date_components[5])
    # Tạo đối tượng date
    date_omo = datetime.datetime(year, month, day).date()
    volume_omo = data_new[-1].replace('.', '')
    volume_omo = float(volume_omo.replace(',', '.')) / (-1000)
    rate_omo = float(data_new[-3].replace(',', '.'))
    insert_query = f"INSERT INTO tbomovietnam (date,rate,volume) VALUES ('{date_omo}', {rate_omo},{volume_omo})"
    execute_query(0, insert_query)
    return date_omo,volume_omo,rate_omo


def static_above_ma():
    query_get_df_transation = f"select ticker,date, close from portfolio_stockpricefilter order by ticker,date"    
    df_transaction = read_sql_to_df(1,query_get_df_transation)
    df_transaction ['MA200'] = df_transaction .groupby('ticker')['close'].rolling(window=200).mean().reset_index(0, drop=True)
    df_transaction ['MA100'] = df_transaction .groupby('ticker')['close'].rolling(window=100).mean().reset_index(0, drop=True)
    df_transaction ['MA50'] = df_transaction .groupby('ticker')['close'].rolling(window=50).mean().reset_index(0, drop=True)
    df_transaction ['MA20'] = df_transaction .groupby('ticker')['close'].rolling(window=20).mean().reset_index(0, drop=True)
    data_for_day = df_transaction[(df_transaction['date'].dt.date == date) & (df_transaction['close'] > 0)]
    if data_for_day.shape[0] > 0:
        count_ma200 = round((data_for_day['close'] > data_for_day['MA200']).sum() / data_for_day.shape[0] * 100, 2)
        count_ma100 = round((data_for_day['close'] > data_for_day['MA100']).sum() / data_for_day.shape[0] * 100, 2)
        count_ma50 = round((data_for_day['close'] > data_for_day['MA50']).sum() / data_for_day.shape[0] * 100, 2)
        count_ma20 = round((data_for_day['close'] > data_for_day['MA20']).sum() / data_for_day.shape[0] * 100, 2)
    else:
        count_ma200 = 0
        count_ma100 = 0
        count_ma50 = 0
        count_ma20 = 0
    query_get_vnindex = f"select close from portfolio_sectorprice where date = '{date}' and ticker = 'VNINDEX' " 
    vnindex = query_data(1,query_get_vnindex)
    if vnindex:
        close = vnindex[0][0]
    if len(data_for_day)>0:
        insert_query = f"INSERT INTO tbstockmarketvnstaticma (date,count_ma200,count_ma100,count_ma50,count_ma20, vnindex) VALUES ('{date}', {count_ma200},{count_ma100},{count_ma50},{count_ma20},{close})"
        execute_query(0, insert_query)
    return date, count_ma200,count_ma100,count_ma50,count_ma20, close

def auto_news_static_ma():
    data= static_above_ma()
    previous_date = difine_previous_trading_date(date)
    query_get_data= f"select * from tbstockmarketvnstaticma where date >= '{previous_date.strftime('%Y-%m-%d')}'"
    df_data = read_sql_to_df(0,query_get_data)
    df_data = df_data.sort_values(by='date')
    # Tính phần trăm thay đổi cho từng cột (count_ma200, count_ma100, count_ma50)
    df_data['percent_change_ma200'] = round(df_data['count_ma200'].pct_change() * 100,2)
    df_data['percent_change_ma100'] = round(df_data['count_ma100'].pct_change() * 100,2)
    df_data['percent_change_ma50'] = round(df_data['count_ma50'].pct_change() * 100,2)
    df_data['percent_change_ma20'] = round(df_data['count_ma20'].pct_change() * 100,2)
    df_final = df_data[df_data['date']==date]
    if len(df_final)>0:
        data = df_final.to_dict(orient='records')[0]
        message = "Thống kê chỉ báo trung bình trên toàn thị trường:" + "\n"
        message += f"- Có {data['count_ma200']}% cổ phiếu nằm trên đường trung bình 200 phiên, thay đổi {data['percent_change_ma200']}% so với phiên trước đó "+ "\n"
        message += f"- Có {data['count_ma100']}% cổ phiếu nằm trên đường trung bình 100 phiên, thay đổi {data['percent_change_ma100']}% so với phiên trước đó "+ "\n"
        message += f"- Có {data['count_ma50']}% cổ phiếu nằm trên đường trung bình 50 phiên, thay đổi {data['percent_change_ma50']}% so với phiên trước đó "+ "\n"
        message += f"- Có {data['count_ma20']}% cổ phiếu nằm trên đường trung bình 20 phiên, thay đổi {data['percent_change_ma20']}% so với phiên trước đó "+ "\n"
        # for group in external_room:
        #         bot = Bot(token=group.token.token)
        #         try:
        #             bot.send_message(
        #                 chat_id=group.chat_id, #room Khách hàng
        #                 text=message)
        #         except:
        #             pass
        return message
    


def auto_news_daily():
    message = ""
    bot = Bot(token='5881451311:AAEJYKo0ttHU0_Ztv3oGuf-rfFrGgajjtEk')
    sector_name =SectorListName.objects.all().values()
    df_sector_name = pd.DataFrame(sector_name)
    date = datetime.datetime.today().date()
    previous_trading_date = difine_previous_trading_date(date)
    start_date = date - datetime.timedelta(days=365)
    query_get_df_sector = f"select * from portfolio_sectorprice where date > '{start_date}'"
    df_data = read_sql_to_df(1,query_get_df_sector)
    df_vnindex = df_data[(df_data['ticker'] == "VNINDEX")&(df_data['date'] >= (previous_trading_date).strftime('%Y-%m-%d'))]
    # Tính toán và tạo cột mới 'change' trong DataFrame
    today_close_vnindex =  df_vnindex[df_vnindex['date'] == date.strftime('%Y-%m-%d')]['close'].values[0]
    previous_close_vnindex = df_vnindex[df_vnindex['date'] == previous_trading_date.strftime('%Y-%m-%d')]['close'].values[0]
    change_vnindex = round(today_close_vnindex - previous_close_vnindex ,2)
    change_day_percent_vnindex = round(100*(change_vnindex/previous_close_vnindex),2)
    if today_close_vnindex >0:
        if change_day_percent_vnindex >= 1.5:
            status_vnindex = 'Tăng mạnh'
        elif change_day_percent_vnindex < 1.5 and change_day_percent_vnindex >0:
            status_vnindex  = 'Tăng'
        elif change_day_percent_vnindex > -1.5 and change_day_percent_vnindex <0:
            status_vnindex  = 'Giảm'      
        elif change_day_percent_vnindex <= -1.5:
            status_vnindex  = 'Giảm mạnh'    
        elif change_day_percent_vnindex ==0:
            status_vnindex  = 'Không biến động' 
    
        message += f"Thị trường ngày {date}, chỉ số VNINDEX {status_vnindex} {change_vnindex} điểm ({change_day_percent_vnindex}%) chốt tại mốc {today_close_vnindex}." + "\n"
    
        #tính chỉ số ngành
        query_get_df_transation = f"select * from portfolio_stockpricefilter  where date ='{date}'"    
        df_transaction = read_sql_to_df(1,query_get_df_transation)
        df_transaction['value']=df_transaction['close']*df_transaction['volume']
        query_get_df_stock_sector = f"select * from tbliststockbysectoricb "    
        df_stock_sector = read_sql_to_df(0,query_get_df_stock_sector)

        df_sector = df_data[df_data['ticker'].str.len() == 4]
        df_sector = df_sector.sort_values(by=['ticker', 'date'])
        grouped = df_sector.groupby('ticker')['close'].agg(['min', 'max', 'mean']).reset_index()
        df_sector = df_data[df_data['date'] >= (previous_trading_date).strftime('%Y-%m-%d')]
        df_sector['change_day'] = df_sector.groupby('ticker')['close'].diff()
        df_sector['change_day_percent'] = (df_sector['change_day'] / df_sector['close'].shift(1)) * 100
        df_lated = df_sector[df_sector['date'] == date.strftime('%Y-%m-%d')]
        df_lated = pd.merge(df_sector_name , df_lated, on='ticker')
        df_lated = df_lated [['date','ticker','name','close', 'volume', 'change_day_percent']].reset_index()
        df = pd.merge(df_lated, grouped, on='ticker')
        # Sắp xếp DataFrame theo cột 'change_day_percent' theo thứ tự giảm dần
        sorted_df = df.sort_values(by=['change_day_percent','volume'], ascending=False)
        # Lấy 5 hàng đầu (5 ticker có change_day_percent lớn nhất)
        top_tickers = sorted_df[(sorted_df['change_day_percent'] >= 3) & (sorted_df['volume'] >= 10000)]
        top_5_tickers = top_tickers.head(5)
        top_sector = top_5_tickers ['name'].tolist()
        # Lấy 5 hàng cuối (5 ticker có change_day_percent nhỏ nhất)
        bottom_tickers = sorted_df[(sorted_df['change_day_percent'] <= -3) & (sorted_df['volume'] >= 10000)]
        bottom_5_tickers = bottom_tickers.tail(5)
        bottom_sector = bottom_5_tickers['name'].tolist()
        # Lấy danh sách các ticker có giá trị close lớn hơn hoặc bằng max
        high_close_tickers = df[(df['close'] >= df['max']) & (df['close'] != 100)& (df['close'] != 0)]
        high_close_sector = high_close_tickers['name'].tolist()
        # Lấy danh sách các ticker có giá trị close nhỏ hơn hoặc bằng min
        low_close_tickers = df[(df['close'] <= df['min'])& (df['close'] != 100)& (df['close'] != 0)]
        low_close_sector = low_close_tickers['name'].tolist()

        data_fr =[]
        linkbase= 'https://www.stockbiz.vn/ForeignerTradingStats.aspx?Type=1'
        r = requests.get(linkbase)
        soup = BeautifulSoup(r.text,'html.parser')
        table = soup.find('table', class_='dataTable')
        rows = table.find_all('td') 
        columns = ["date", "buy_volume", "%_buy_volume", "sell_volume", "%_sell_volume", "net_volume", "buy_value", "%_buy_value", "sell_value", "%_sell_value","net_value"]

        for td in rows:
            row = td.get_text(strip=True)
            data_fr.append(row)
        data_fr = data_fr[13:]
        num_columns = len(columns)
        num_data = len(data_fr)
        num_rows = num_data // num_columns
        # Chia dữ liệu thành các dòng
        data_rows = [data_fr[i:i + num_columns] for i in range(0, num_data, num_columns)]
        # Tạo DataFrame từ dữ liệu và cột
        df_fr = pd.DataFrame(data_rows, columns=columns)
        df_fr['date'] = pd.to_datetime(df_fr['date'], format='%d/%m/%Y')
        numeric_columns = columns[1:]  # Lấy tất cả cột sau cột 'Ngày'
        df_fr[numeric_columns] = df_fr[numeric_columns].replace('[\.,%]', '', regex=True).astype(float)
        total_volume = round(df_fr['net_value'].sum(),0)
        result_month_value = round_number(total_volume)
        df_fr_lated = df_fr[df_fr['date'] == (date).strftime('%Y-%m-%d')]
        today_value = df_fr_lated['net_value'].values[0]
        result_today_value = round_number(today_value)

        
    
        message += f"Nước ngoài đã {status(today_value)} trên HOSE {result_today_value} tỷ. Tổng kết trong một tháng, nước ngoài đã {status(total_volume)} {result_month_value} tỷ" + "\n"
        
        if len(top_5_tickers) > 0:
            text_top_5_tickers = "- Các ngành tăng mạnh nhất là " 
            message += print_text(text_top_5_tickers,top_sector,df_stock_sector,df_transaction)

        if len(bottom_5_tickers) > 0:
            text_bottom_5_tickers = "- Các ngành giảm mạnh nhất là "
            message += print_text(text_bottom_5_tickers,bottom_sector,df_stock_sector,df_transaction)

        if len(high_close_tickers) > 0:
            text_high_close_sector = "- Các ngành đã vượt đỉnh 1 năm là "
            message += print_text(text_high_close_sector,high_close_sector,df_stock_sector,df_transaction)

        if len(low_close_tickers) > 0:
            text_low_close_sector = "- Các ngành đã thủng đáy 1 năm là "
            message += print_text(text_low_close_sector,low_close_sector,df_stock_sector,df_transaction)
        message += auto_news_static_ma()
        for group in external_room:
            bot = Bot(token=group.token.token)
            try:
                bot.send_message(
                    chat_id=group.chat_id, #room Khách hàng
                    text=message)
            except:
                pass
    return message
        

       
    # OMO
def auto_news_omo(): 
    data = get_omo_info()   
    query_get_df_omo = f"select * from tbomovietnam where date > '{date - datetime.timedelta(days=30)}'"
    df_omo = read_sql_to_df(0,query_get_df_omo)
    total_volume_omo = round(df_omo['volume'].sum(),2)
    average_rate_omo = round(df_omo['rate'].mean(),2)
    if data[0] ==date and abs(data[1])>=20:
        if data[2] >0:
            status_today ='Bơm ròng'
        else:
            status_today ='Hút ròng'
        if total_volume_omo >0:
            status_total_volume_omo ='Bơm ròng'
        else:
            status_total_volume_omo ='Hút ròng'
        message = f"Ngày {data[0]} NHNN đã {status_today} {abs(data[1])}k tỷ, lãi suất {data[2]}. Tổng kết trong 30 ngày qua, NHNN đã {status_total_volume_omo} {total_volume_omo}k tỷ với lãi suất bình quân {average_rate_omo}%"
        for group in external_room:
            bot = Bot(token=group.token.token)
            try:
                bot.send_message(
                    chat_id=group.chat_id, #room Khách hàng
                    text=message)
            except:
                pass
        return message
       


def auto_news_stock_worlds():
    if date.weekday()==0:
        start_date = difine_previous_trading_date(date - datetime.timedelta(days=3))
    else:
        start_date = difine_previous_trading_date(date - datetime.timedelta(days=1))
    query_get_df_index = f"select * from tbdailymarco where date >= '{start_date}'"
    df_data = read_sql_to_df(0,query_get_df_index)
    df_data = df_data[(df_data['ticker'] != "^FTSE")&(df_data['ticker'] != "T10Y2Y")]
    df_data = df_data.sort_values(by=['ticker', 'date']).reset_index()
    # df_vnindex = df_data[(df_data['ticker'] == "VNINDEX")]
    df_data['change_day'] = round(df_data.groupby('ticker')['close'].diff(),2)
    df_data['change_day_percent'] = round((df_data['change_day'] / df_data['close'].shift(1)) * 100,2)
    selected_row = df_data[df_data['date'] == (date - datetime.timedelta(days=1)).strftime('%Y-%m-%d')]
    if len(selected_row) >0:
        selected_row.loc[selected_row['change_day_percent'] >= 1.5, 'status'] = 'Tăng mạnh'
        selected_row.loc[(selected_row['change_day_percent'] < 1.5) & (selected_row['change_day_percent'] > 0), 'status'] = 'Tăng'
        selected_row.loc[(selected_row['change_day_percent'] >- 1.5) & (selected_row['change_day_percent'] < 0), 'status'] = 'Giảm'
        selected_row.loc[selected_row['change_day_percent'] <= -1.5, 'status'] = 'Giảm mạnh'
        selected_row.loc[selected_row['change_day_percent'] ==0, 'status'] = 'Không biến động'
        df_sent_message = selected_row[abs(selected_row['change_day_percent']) >= 1]
        if len(df_sent_message) >0:
            message = "Tài chính nổi bật thế giới:" + "\n"
            for index, row in df_sent_message.iterrows():
                message += f"- {row['name']} {row['status']} {row['change_day']} điểm ({row['change_day_percent']}%) chốt tại {round(row['close'],2)}"+ "\n"
            for group in external_room:
                bot = Bot(token=group.token.token)
                try:
                    bot.send_message(
                        chat_id=group.chat_id, #room Khách hàng
                        text=message)
                except:
                    pass
        return message
        
        





# top nhóm ngành hút dòng tiền nhiều nhất phiên
# top ngành bị bán nhiều nhất phiên
# top ngành đã đảo chiều sang xu thế tăng dài hạn
# top ngành đảo chiều giảm giá dài hạn
# top ngành về đáy 1 năm
# top ngành vượt đỉnh 1 năm




# query_get_df_transation = f"select ticker,date, close from portfolio_stockprice where date > '2018-01-01' order by ticker,date"    
# df_transaction = read_sql_to_df(1,query_get_df_transation)
# df_transaction = df_transaction.sort_values(by=['ticker', 'date'])
# df_transaction ['MA200'] = df_transaction .groupby('ticker')['close'].rolling(window=200).mean().reset_index(0, drop=True)
# df_transaction ['MA100'] = df_transaction .groupby('ticker')['close'].rolling(window=100).mean().reset_index(0, drop=True)
# df_transaction ['MA50'] = df_transaction .groupby('ticker')['close'].rolling(window=50).mean().reset_index(0, drop=True)
# df_transaction ['MA20'] = df_transaction .groupby('ticker')['close'].rolling(window=20).mean().reset_index(0, drop=True)
# data_for_day = df_transaction[(df_transaction['date'].dt.date == date) & (df_transaction['close'] > 0)]
# df_transaction['date'] = pd.to_datetime(df_transaction['date']).dt.date

# for date_check in df_transaction[df_transaction['close'] > 0]['date'].unique():
#     result = {}
#     # Lọc dữ liệu cho ngày hiện tại
#     data_for_day = df_transaction[(df_transaction['date'] == date_check) & (df_transaction['close'] > 0)]
#     # Đếm số lượng ticker có 'close' > 'MA200' cho ngày hiện tại và tính tỷ lệ
#     result['date'] = date_check
#     if data_for_day.shape[0] > 0:
#         result['count_ma200'] = round((data_for_day['close'] > data_for_day['MA200']).sum() / data_for_day.shape[0] * 100, 2)
#         result['ccount_ma100'] = round((data_for_day['close'] > data_for_day['MA100']).sum() / data_for_day.shape[0] * 100, 2)
#         result['count_ma50'] = round((data_for_day['close'] > data_for_day['MA50']).sum() / data_for_day.shape[0] * 100, 2)
#         result['count_ma20'] = round((data_for_day['close'] > data_for_day['MA20']).sum() / data_for_day.shape[0] * 100, 2)
#     else:
#         result['count_ma200'] = 0
#         result['ccount_ma200'] = 0
#         result['count_ma50'] = 0
#         result['count_ma20'] = 0
#     insert_data.append(result)

# df =pd.DataFrame(insert_data)
# df.to_sql()
# # Kết quả
# print(insert_data)

# df.to_sql('tbstockmarketvnstaticma',engine (0) , if_exists='replace', index=False)

