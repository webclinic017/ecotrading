from stocklist.logic import *
from stocklist.auto_news import auto_news_daily, auto_news_omo, auto_news_static_ma, auto_news_stock_worlds
from stockwarehouse.models import morning_check, atternoon_check
from webdata import save_data
from portfolio.models import get_all_info_stock_price


def schedule_morning():
    today = datetime.now().date()
    not_trading_dates = DateNotTrading.objects.filter(date=today)

    # try:
    #     # Uncomment nếu bạn có một hàm check_update_analysis_and_send_notifications
    #     # check_update_analysis_and_send_notifications()
    # except Exception as e_check_update:
    #     print(f"An error occurred while running check_update_analysis_and_send_notifications: {e_check_update}")

    try:
        save_data()
    except Exception as e_save_data:
        print(f"An error occurred while running save_data: {e_save_data}")

    try:
        auto_news_stock_worlds()
    except Exception as e_auto_news:
        print(f"An error occurred while running auto_news_stock_worlds: {e_auto_news}")

    try:
        morning_check()
    except Exception as e_morning_check:
        print(f"An error occurred while running morning_check: {e_morning_check}")

    if not not_trading_dates:
        try:
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
        except Exception as e_check_dividend:
            print(f"An error occurred while running check_dividend: {e_check_dividend}")
    else:
        pass



def schedule_mid_trading_date():
    today = datetime.now().date()
    not_trading_dates = DateNotTrading.objects.filter(date=today)
    
    if not not_trading_dates:
        try:
            get_info_stock_price_filter()
        except Exception as e_get_info_stock:
            print(f"An error occurred while running get_info_stock_price_filter: {e_get_info_stock}")

        try:
            atternoon_check()
        except Exception as e_afternoon_check:
            print(f"An error occurred while running atternoon_check: {e_afternoon_check}")
    else:
        pass

def schedule_after_trading_date():
    today = datetime.now().date()
    not_trading_dates = DateNotTrading.objects.filter(date=today)
    
    if not not_trading_dates:
        try:
            auto_news_daily()
        except Exception as e_auto_news:
            print(f"An error occurred while running auto_news_daily: {e_auto_news}")
        try:
            filter_stock_daily()
        except Exception as e_filter_stock:
            print(f"An error occurred while running filter_stock_daily: {e_filter_stock}")
    else:
        pass

