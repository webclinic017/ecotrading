from django.urls import path
from .views import *


urlpatterns = [
    # path('backtest/', run_backtest, name='backtest'),
    # path('get_signal/', get_signal, name='get_signal'),
    path('warehouse', warehouse, name='warehouse'),
    # path('warehouse/get-price', get_all_market_price, name='static_page_info_bot'),
    
]