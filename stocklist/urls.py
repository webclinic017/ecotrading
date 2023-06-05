from django.urls import path
from .views import *


urlpatterns = [
    # ...
    path('backtest/', run_backtest, name='backtest'),
    path('get-signal/', get_signal, name='get_signal'),
]