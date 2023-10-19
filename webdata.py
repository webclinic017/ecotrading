import yfinance as yf
from pandas_datareader import wb
import datetime
import pandas as pd
from posgress import *
import pandas_datareader.data as web
import numpy as np



    # tỷ giá
dolar_index = yf.Ticker("DX-Y.NYB")
usd_vnd =yf.Ticker("VND=X")
# Lãi suất: ^TNX: bond year 10
bond_year_10 = yf.Ticker("^TNX")
#Giá hàng hóa CL=F: crude_oil = yf.Ticker("CL=F")
crude_oil = yf.Ticker("CL=F")
gold = yf.Ticker("GC=F")
#Chỉ số chứng khoán
dow_jones =yf.Ticker("^DJI")
sp_500 = yf.Ticker("^GSPC")
nikkei = yf.Ticker("^N225")
FTSE_100= yf.Ticker("^FTSE")
hangsheng =yf.Ticker("^HSI")
vnindex = yf.Ticker("^VNINDEX.VN")
dax = yf.Ticker("^GDAXI")

def marco_data_daily(start_date, end_date):  
    tickers = ["DX-Y.NYB", "VND=X", "^TNX", "CL=F", "GC=F", "^DJI","^GSPC", "^N225", "^FTSE", "^HSI"]
    # Tải dữ liệu cho tất cả các ticker trong danh sách
    data = yf.download(tickers, start=start_date, end=end_date)
    stacked_data = data['Adj Close'].stack()
    stacked_data = stacked_data.reset_index()
    stacked_data.columns = ['date', 'ticker', 'close']
    bondy10_y2 = web.DataReader(['T10Y2Y'], 'fred', start_date, end_date).reset_index()
    bondy10_y2['ticker']= 'T10Y2Y'
    bondy10_y2.rename(columns={'T10Y2Y': 'close','DATE':'date'}, inplace=True)
    stacked_data = pd.concat([stacked_data,bondy10_y2], axis=0) 
    conditions = [
        (stacked_data['ticker'] == 'DX-Y.NYB'),
        (stacked_data['ticker'] == 'VND=X'),
        (stacked_data['ticker'] == '^TNX'),
        (stacked_data['ticker'] == 'CL=F'),
        (stacked_data['ticker'] == 'GC=F'),
        (stacked_data['ticker'] == '^DJI'),
        (stacked_data['ticker'] == '^GSPC'),
        (stacked_data['ticker'] == '^N225'),
        (stacked_data['ticker'] == '^HSI'),
        (stacked_data['ticker'] == '^FTSE'),
        (stacked_data['ticker'] == '^GDAXI'),
        (stacked_data['ticker'] == 'T10Y2Y')
            ]
    values = ['Dolar index', 'USD/VND', 'Bond year 10', 'Crude oil','Gold','Dow Jones','S&P 500','Nikkei 225','Hang Seng','FTSE 100','DAX','Bond 10Y-2Y']
    # Sử dụng np.select để tạo cột 'name'
    stacked_data['name'] = np.select(conditions, values, default=None)
    final_data = stacked_data
    # In ra dữ liệu
    return final_data

# Thiết lập ngày bắt đầu và kết thúc
def marco_data_yearly():
    start_date = datetime.datetime(2000, 1, 1)
    end_date = datetime.datetime(2030, 10,9)
    countries=['US', 'CN', 'VN']
    gdb_cap = wb.download(indicator='NY.GDP.PCAP.KD', country=countries, start=start_date, end=end_date)
    inflation_data = wb.download(indicator='FP.CPI.TOTL.ZG', country=countries, start=start_date, end=end_date)
    unemployment_data = wb.download(indicator='SL.UEM.TOTL.ZS', country=countries, start=start_date, end=end_date)
    export_data = wb.download(indicator='NE.EXP.GNFS.CD', country=countries, start=start_date, end=end_date)
    import_data = wb.download(indicator='NE.IMP.GNFS.CD', country=countries, start=start_date, end=end_date)
    gdp_growth_data = wb.download(indicator='NY.GDP.MKTP.KD.ZG', country=countries, start=start_date, end=end_date)
    debt_on_GDP_ratio= wb.download(indicator='GC.DOD.TOTL.GD.ZS',country=countries, start=start_date, end=end_date)
    # Gộp các dữ liệu thành một DataFrame duy nhất
    world_marcro_data = pd.concat([gdb_cap,gdp_growth_data,export_data, import_data, unemployment_data, inflation_data, debt_on_GDP_ratio], axis=1)
    # Đặt tên cột cho DataFrame
    world_marcro_data.columns = ['GDPcap','GDPGrowth', 'ExportValue', 'ImportValue', 'UnemploymentRate', 'InflationRate', 'debtonGDPratio']
    world_marcro_data.reset_index(inplace=True)
    return world_marcro_data

def marco_data_monthly():
    end_date = datetime.datetime.now().date()
    start_date = end_date - datetime.timedelta(days= 365) 
    usa = web.DataReader(['GDP','CORESTICKM159SFRBATL','GFDEBTN', 'M2SL','BOPGSTB','GFDEGDQ188S','PALLFNFINDEXM','JTSOSL','IMP5520','EXP5520'], 'fred', start_date, end_date)
    usa['countries'] = 'US'
    usa_new_column_names = {
        'GDP': 'GDP',#Gross Domestic Product 
        'CORESTICKM159SFRBATL': 'CPI', #Sticky Price Consumer Price Index less Food and Energy () 
        'M2SL': 'M2',
        'BOPGSTB': 'BOP',#trade balance: BOPGSTB
        'GFDEBTN': 'Dept',#Federal Debt: Total Public Debt (GFDEBTN)
        'GFDEGDQ188S': 'DeptofGDP',  #Federal Debt: Total Public Debt as Percent of Gross Domestic Product (GFDEGDQ188S)
        'PALLFNFINDEXM': 'allCommodities',#Global Price Index of All Commodities ()
        'JTSOSL': 'Nonfarm', #Other Separations: Total Nonfarm 
        'IMP5520': 'Imports VN', #U.S. Imports of Goods by Customs Basis from Vietnam (IMP5520) 
        'EXP5520': 'Exports VN',#U.S. Exports of Goods by F.A.S. Basis to Vietnam (EXP5520)
    }
    usa.rename(columns=usa_new_column_names, inplace=True)
    usa.reset_index(inplace=True)
    #china
    china = web.DataReader(['CHNGDPNQDSMEI','CPALTT01CNM659N','MYAGM2CNM189N','INTDSRCNM193N','XTEXVA01CNM667S','IR3TTS01CNM156N','IRSTCB01CNM156N','XTIMVA01CNM667S' ], 'fred', start_date, end_date)
    china['countries'] = 'China'
    china_new_column_names = {
    'CHNGDPNQDSMEI': 'GDP',   #'National Accounts: GDP by Expenditure: Current Prices: Gross Domestic Product: Total for China ()
    'CPALTT01CNM659N': 'CPI', #Consumer Price Index: All Items: Total for China (CPALTT01CNM659N)
    'MYAGM2CNM189N':'M2', #M2 for China 
    'INTDSRCNM193N':'Interest', #Interest Rates, Discount Rate for China (INTDSRCNM193N)
    'XTEXVA01CNM667S': 'Exports',#International Trade: Exports: Value (Goods): Total for China (XTEXVA01CNM667S)
    'IR3TTS01CNM156N':'Interest_3M', #Interest Rates: 3-Month or 90-Day Rates and Yields: Treasury Securities: Total for China (IR3TTS01CNM156N)
    'IRSTCB01CNM156N':'Immediate Rates', # Interest Rates: Immediate Rates (< 24 Hours): Central Bank Rates: Total for China (IRSTCB01CNM156N)
    'XTIMVA01CNM667S': 'Imports' #International Trade: Imports: Value (Goods): Total for China 
    }
    china.rename(columns=china_new_column_names, inplace=True)
    china.reset_index(inplace=True)
    return usa, china



def save_data():
    end_date = datetime.datetime.now().date()
    start_date = end_date - datetime.timedelta(days= 1800) 
    df_marco_daily = marco_data_daily(start_date, end_date)
    df_marco_daily.to_sql('tbdailymarco', engine(0), if_exists='replace', index=False)
    df_yearly_macro= marco_data_yearly()
    df_yearly_macro.to_sql('tbyearlymacro', engine(0), if_exists='replace', index=False)
    df_monthy_usa = marco_data_monthly()[0]
    df_monthy_usa.to_sql('tbusamonthlymarco', engine(0), if_exists='replace', index=False)
    df_monthy_china = marco_data_monthly()[1]
    df_monthy_china.to_sql('tbchinamonthlymarco', engine(0), if_exists='replace', index=False)








 

