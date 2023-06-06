from django.urls import path
from .views import *


urlpatterns = [
    # path('backtest/', run_backtest, name='backtest'),
    path('get-signal/', get_signal, name='get_signal'),
    path('calculator-qty', get_qty_buy, name='get_qty_buy'),
]