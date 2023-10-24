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
    date = datetime.datetime(year, month, day).date()
    volume_omo = float(data_new[-1])/(-1000)
    rate_omo = float(data_new[-3].replace(',', '.'))
    insert_query = f"INSERT INTO tbomovietnam (date,rate,volume) VALUES ('{date}', {rate_omo},{volume_omo})"
    if date:
        execute_query(0, insert_query)
    return date,volume_omo,rate_omo




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
    
        message += f"Nước ngoài đã {status(today_value)} {result_today_value} tỷ. Tổng kết trong một tháng, nước ngoài đã {status(total_volume)} {result_month_value} tỷ" + "\n"
        
        if len(top_5_tickers) > 0:
            message += "- Các ngành tăng mạnh nhất là " + ", ".join(top_sector) + "\n"

        if len(bottom_5_tickers) > 0:
            message += "- Các ngành giảm mạnh nhất là " + ", ".join(bottom_sector) + "\n"

        if len(high_close_tickers) > 0:
            message += "- Các ngành đã vượt đỉnh 1 năm là " + ", ".join(high_close_sector) + "\n"

        if len(low_close_tickers) > 0:
            message += "- Các ngành đã thủng đáy 1 năm là " + ", ".join(low_close_sector)

        for group in external_room:
            bot = Bot(token=group.token.token)
            try:
                bot.send_message(
                    chat_id=group.chat_id, #room Khách hàng
                    text=message)
            except:
                pass
    return message
        

        # if len(top_5_tickers)>0:
        #     bot.send_message(
        #         chat_id='-870288807', 
        #         text="Các ngành tăng mạnh nhất là " + ", ".join(top_sector) )
        # if len(bottom_5_tickers )>0:
        #     bot.send_message(
        #         chat_id='-870288807', 
        #         text="Các ngành giảm mạnh nhất là " + ", ".join(bottom_sector ) )
        # if len(high_close_tickers)>0:
        #     bot.send_message(
        #         chat_id='-870288807', 
        #         text="Các ngành đã vượt đỉnh 1 năm là " + ", ".join(high_close_sector) )
        # if len(low_close_tickers)>0:
        #     bot.send_message(
        #         chat_id='-870288807', 
        #         text="Các ngành đã thủng đáy 1 năm là " + ", ".join(low_close_sector) )


    # OMO
def auto_news_omo(): 
    data = get_omo_info()   
    query_get_df_omo = f"select * from tbomovietnam where date > '{date - datetime.timedelta(days=30)}'"
    df_omo = read_sql_to_df(0,query_get_df_omo)
    total_volume_omo = round(df_omo['volume'].sum(),2)
    average_rate_omo = round(df_omo['rate'].mean(),2)
    if data:
        if data[2] >0:
            status_today ='Bơm ròng'
        else:
            status_today ='Hút ròng'
        if total_volume_omo >0:
            status_total_volume_omo ='Bơm ròng'
        else:
            status_total_volume_omo ='Hút ròng'
        message = f"Ngày {data[0]} NHNN đã {status_today} {abs(data[1])}k tỷ, lãi suất {data[2]}. Tổng kết trong 30 ngày qua, NHNN đã {status_total_volume_omo} {total_volume_omo}k tỷ với lãi suất bình quân {average_rate_omo}%"
        # for group in external_room:
        #     bot = Bot(token=group.token.token)
        #     try:
        #         bot.send_message(
        #             chat_id=group.chat_id, #room Khách hàng
        #             text=message)
        #     except:
        #         pass
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
        message = "Điểm tin tài chính thế giới:" + "\n"
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

