from django.urls import path
from .views import *


urlpatterns = [
    # path('backtest/', run_backtest, name='backtest'),
    path('get_signal/', get_signal, name='get_signal'),
    path('calculator-qty', get_qty_buy, name='get_qty_buy'),
    path('aboutbot/', static_page_info_bot, name='static_page_info_bot'),
    
]