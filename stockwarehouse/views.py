import math
from django.shortcuts import render

from itertools import product
import numpy as np
import talib
from datetime import datetime, timedelta
from .models import *
from django.shortcuts import render
from statistics import mean
from django.http import JsonResponse


def warehouse(request):
    # Xử lý logic cho trang warehouse ở đây
    if request.method == 'POST':
        # Xử lý logic khi có yêu cầu POST từ form
        action = request.POST.get('action', None)

        if action == 'update_market_price':
            # Xử lý cập nhật giá thị trường cho các cổ phiếu trong danh sách
            port = Portfolio.objects.filter(sum_stock__gt=0).order_by('stock').distinct('stock')
            for item in port:
                item.market_price = get_stock_market_price(item.stock)
                item.save()

        elif action == 'calculate_max_qty_buy':
            # Xử lý tính toán số lượng tối đa có thể mua
            account = float(request.POST['account'])
            ticker = request.POST['ticker']
            price = float(request.POST['price'])
            account = Account.objects.get(pk=account)
            initial_margin_ratio = StockListMargin.objects.get(stock=ticker).initial_margin_requirement
            max_value = abs((account.nav - account.initial_margin_requirement * 0.65) / (0.65 * initial_margin_ratio/100))
            qty = math.floor(int(max_value / price))
            return JsonResponse({'qty': '{:,.0f}'.format(qty)})

    # Trả về template chung cho cả hai trường hợp
    return render(request, 'stockwarehouse/warehouse.html')

