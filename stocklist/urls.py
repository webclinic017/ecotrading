from django.urls import path
from .views import run_backtest


urlpatterns = [
    # ...
    path('backtest/', run_backtest, name='backtest'),
]