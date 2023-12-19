from stocklist.logic import *
from stocklist.auto_news import auto_news_daily, auto_news_omo, auto_news_static_ma, auto_news_stock_worlds
from stockwarehouse.models import morning_check, atternoon_check
from webdata import save_data
from portfolio.models import get_all_info_stock_price


def schedule_morning():
    today = datetime.now().date()
    not_trading_dates = DateNotTrading.objects.filter(date=today)
    check_update_analysis_and_send_notifications()
    save_data()
    auto_news_stock_worlds()
    morning_check()
    if not not_trading_dates:
        # Thực hiện công việc cần làm vào 7h30
        # Ví dụ: Gửi email
        # send_mail(
        #     'Morning Check',
        #     'Nội dung kiểm tra buổi sáng...',
        #     'from@example.com',
        #     ['to@example.com'],
        #     fail_silently=False,
        # )
        
        check_dividend()
        
        
    else:
        pass


def schedule_mid_trading_date():
    today = datetime.now().date()
    not_trading_dates = DateNotTrading.objects.filter(date=today)
    
    if not not_trading_dates:
        get_info_stock_price_filter()
        atternoon_check()
        
    else:
        pass

def schedule_after_trading_date():
    today = datetime.now().date()
    not_trading_dates = DateNotTrading.objects.filter(date=today)
    
    if not not_trading_dates:
        auto_news_daily()
        filter_stock_daily()
        
    else:
        pass

