import os
import pandas as pd
from portfolio.models import SectorPrice
from posgress import *

def sector_data_import():
    # Đường dẫn tới thư mục chứa các file CSV
    folder_path = "C:\\ExportData\\Sector"
    # Tạo một danh sách để lưu trữ tất cả các DataFrame từ các file CSV
    dfs = []
    # Duyệt qua tất cả các file trong thư mục
    for filename in os.listdir(folder_path):
        if filename.endswith(".csv"):
            # Loại bỏ phần ".csv" ở cuối và sử dụng tên file làm cột 'name'
            name = os.path.splitext(filename)[0]
            file_path = os.path.join(folder_path, filename)
            # Đọc file CSV, bỏ dòng đầu tiên
            df = pd.read_csv(file_path, header=0, index_col=False)
            df['ticker'] = name
            dfs.append(df)
    # Nối tất cả các DataFrame thành một DataFrame tổng
    sector_df = pd.concat(dfs, ignore_index=True)
    sector_df['date'] = pd.to_datetime(sector_df['date'], format='%d-%b-%y').dt.strftime('%Y-%m-%d')
    # data = sector_df.to_dict(orient='records')
    # SectorPrice.objects.all().delete()
    # # Lưu các đối tượng SectorPrice mới vào cơ sở dữ liệu bằng bulk_create
    # SectorPrice.objects.bulk_create([SectorPrice(**item) for item in data])
    # # In ra DataFrame tổng
    # print(sector_df)
    sector_df.to_sql('portfolio_sectorprice', engine(0), if_exists='replace', index=False)

