import math
from django.shortcuts import render
from .models import *
from django.shortcuts import render
from statistics import mean
from django.http import JsonResponse
from portfolio.models import get_list_stock_price


def warehouse(request):
    # Xử lý logic cho trang warehouse ở đây
    if request.method == 'POST':
        # Xử lý logic khi có yêu cầu POST từ form
        action = request.POST.get('action', None)

        if action == 'update_market_price':
            # Xử lý cập nhật giá thị trường cho các cổ phiếu trong danh sách
            stock_list = Portfolio.objects.values_list('stock', flat=True).distinct()
            stock_list_python = list(stock_list)
            get_list_stock_price(stock_list_python)



        elif action == 'calculate_max_qty_buy':
            # Xử lý tính toán số lượng tối đa có thể mua
            account = float(request.POST['account'])
            ticker = request.POST['ticker'].upper()
            print(ticker)
            price = float(request.POST['price'])
            account = Account.objects.get(pk=account)
            margin = StockListMargin.objects.filter(stock=ticker).first()
            max_value = 0
            if account.excess_equity > 0 and margin:
                max_value = abs(account.excess_equity  / (margin.initial_margin_requirement/100))
            
                
            qty = math.floor(int(max_value / price))
            return JsonResponse({'qty': '{:,.0f}'.format(qty)})

    # Trả về template chung cho cả hai trường hợp
    return render(request, 'stockwarehouse/warehouse.html')

