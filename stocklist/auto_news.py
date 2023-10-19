import os
import pandas as pd
from portfolio.models import SectorPrice, SectorListName
from posgress import *
import datetime
from telegram import Bot
from portfolio.models import ChatGroupTelegram

date = datetime.datetime.today().date()
bot = Bot(token='5881451311:AAEJYKo0ttHU0_Ztv3oGuf-rfFrGgajjtEk')
external_room = ChatGroupTelegram.objects.filter(type = 'external',is_signal =True,rank ='1' )

def auto_news_daily():
    bot = Bot(token='5881451311:AAEJYKo0ttHU0_Ztv3oGuf-rfFrGgajjtEk')
    sector_name =SectorListName.objects.all().values()
    df_sector_name = pd.DataFrame(sector_name)
    date = datetime.datetime.today().date()
    start_date = date - datetime.timedelta(days=365)
    query_get_df_sector = f"select * from portfolio_sectorprice where date > '{start_date}'"
    df_data = read_sql_to_df(1,query_get_df_sector)
    df_vnindex = df_data[(df_data['ticker'] == "VNINDEX")&(df_data['date'] >= (date -  datetime.timedelta(days=1)).strftime('%Y-%m-%d'))]
    df_vnindex['change_day'] = df_vnindex.groupby('ticker')['close'].diff()
    df_vnindex['change_day_percent'] = (df_vnindex['change_day'] / df_vnindex['close'].shift(1)) * 100
    selected_row = df_vnindex[df_vnindex['date'] == date.strftime('%Y-%m-%d')]

    df_sector = df_data[df_data['ticker'].str.len() == 4]
    df_sector = pd.merge(df_sector_name , df_sector, on='ticker')
    df_sector = df_sector.sort_values(by=['ticker', 'date'])
    df_sector['change_day'] = df_sector.groupby('ticker')['close'].diff()
    df_sector['change_day_percent'] = (df_sector['change_day'] / df_sector['close'].shift(1)) * 100
    grouped = df_sector.groupby('ticker')['close'].agg(['min', 'max', 'mean']).reset_index()
    df_lated = df_sector[df_sector['date'] == date.strftime('%Y-%m-%d')]
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
    # Cập nhật diễn biến ngành
    if len(df_lated)>0 and len(selected_row) >0:
        data_vnindex = selected_row.to_dict(orient='records')[0]
        if data_vnindex['change_day_percent'] >= 1.5:
            data_vnindex['status']  = 'Tăng mạnh'
        elif data_vnindex['change_day_percent'] < 1.5 and data_vnindex['change_day_percent'] >0:
            data_vnindex['status']  = 'Tăng'
        elif data_vnindex['change_day_percent'] > -1.5 and data_vnindex['change_day_percent'] <0:
            data_vnindex['status']  = 'Giảm'      
        elif data_vnindex['change_day_percent'] <= -1.5:
            data_vnindex['status']  = 'Giảm mạnh'    
        elif data_vnindex['change_day_percent'] ==0:
            data_vnindex['status']  = 'Không biến động' 
        message = ""
        message += f"Thị trường ngày {data_vnindex['date']}, chỉ số VNINDEX {data_vnindex['status']} {round(abs(data_vnindex['change_day']),2)} điểm ({round(data_vnindex['change_day_percent'],2)}%) chốt tại mốc {data_vnindex['close']}." + "\n"

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
    query_get_df_omo = f"select * from tbomovietnam where date > '{date - datetime.timedelta(days=30)}'"
    df_omo = read_sql_to_df(0,query_get_df_omo)
    total_volume_omo = df_omo['volume'].sum()
    average_rate_omo = round(df_omo['rate'].mean(),2)
    df_omo_lated = df_omo[df_omo['date'] == (date).strftime('%Y-%m-%d')]
    if len(df_omo_lated) >0:
        dict_omo = df_omo_lated.to_dict(orient='records')[0]
        if dict_omo['volume'] >0:
            dict_omo['status'] ='Bơm ròng'
        else:
            dict_omo['status'] ='Hút ròng'
        if total_volume_omo >0:
            status_total_volume_omo ='Bơm ròng'
        else:
            status_total_volume_omo ='Hút ròng'
        message = f"Ngày {dict_omo['date'].date()} NHNN đã {dict_omo['status']} {abs(dict_omo['volume'])}k tỷ. Tổng kết trong 30 ngày qua, NHNN đã {status_total_volume_omo} {total_volume_omo}k tỷ với lãi suất bình quân {average_rate_omo}%"
        for group in external_room:
            bot = Bot(token=group.token.token)
            try:
                bot.send_message(
                    chat_id=group.chat_id, #room Khách hàng
                    text=message)
            except:
                pass
       


def auto_news_stock_worlds():
    start_date = date - datetime.timedelta(days=2)
    query_get_df_index = f"select * from tbdailymarco where date >= '{start_date}'"
    df_data = read_sql_to_df(0,query_get_df_index)
    df_data = df_data[(df_data['ticker'] != "^FTSE")].reset_index()
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
        
        





# top nhóm ngành hút dòng tiền nhiều nhất phiên
# top ngành bị bán nhiều nhất phiên
# top ngành đã đảo chiều sang xu thế tăng dài hạn
# top ngành đảo chiều giảm giá dài hạn
# top ngành về đáy 1 năm
# top ngành vượt đỉnh 1 năm

