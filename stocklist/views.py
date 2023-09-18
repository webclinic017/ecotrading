import math
from django.db.models import Avg
import sys
from itertools import product
import numpy as np
import talib
from datetime import datetime, timedelta
import backtrader as bt
import backtrader.feeds as btfeed
import pandas as pd
import matplotlib.pyplot as plt
import backtrader.analyzers as btanalyzers
from stocklist.logic import *
from django.shortcuts import render
from backtrader.observer import Observer
from statistics import mean
from django.http import JsonResponse



def get_signal(request):
    list_buy = []
    if request.method == 'POST':
        list_buy = filter_stock_muanual() 
    data = {'list_buy': list_buy}
    return render(request, 'stocklist/getsignal.html', data)



def get_qty_buy(request):
    if request.method == 'POST':
        nav = float(request.POST['nav'])
        ticker = request.POST['ticker']
        price = float(request.POST['price'])
        risk = 0.03
        R = risk * nav
        ratio_cutloss = ParamsOptimize.objects.filter(ticker=ticker).first().ratio_cutloss
        qty = math.floor(int(R / (price * ratio_cutloss )))
        return JsonResponse({'qty': '{:,.0f}'.format(qty)})

    return render(request, 'stocklist/calculator.html')

def static_page_info_bot(request):
    return render(request, 'stocklist/static_info_bot.html')