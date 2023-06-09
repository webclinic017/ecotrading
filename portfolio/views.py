from django.shortcuts import render
from portfolio.models import *
from django.http import HttpResponse, Http404
from django.template import loader
from datetime import datetime
from django.http import JsonResponse
from django.http import HttpResponsePermanentRedirect


# Create your views here.


def redirect_view(request):
    return HttpResponsePermanentRedirect('http://ecotrading.com.vn/admin')



def account(request,pk):
    end_date = datetime.now()
    start_date = end_date - timedelta(days = 10*365)
    template = loader.get_template('account/account.html')
    time_data = StockPriceFilter.objects.all().order_by('-date_time').first().date_time
    account = Account.objects.get(pk=pk)
    port = account.str_portfolio
    # giá trị thị trường của tài khoản
    market_value = account.market_value
    #tổng tiền nạp vào, rút ra của tài khoản
    net_cash_flow =account.net_cash_flow
    #Khả dụng
    net_cash_available = account.net_cash_available
    total_profit = account.total_profit
    order_list = Transaction.objects.filter(account_id =pk,status_raw = 'matched' ).order_by('-modified_at')
    str_close_deal = account.close_deal[1]
    total_profit_close = account.total_profit_close
    total_profit_open = account.total_profit_open
    if request.method == 'POST':
        info = get_list_stock_price()# Hàm để lấy giá chứng khoán
        time_data = info.first().date_time
    context = {
        'time': time_data,
        'port':port,
        'net_cash_flow':'{:,.0f}'.format(net_cash_flow),
        'market_value': '{:,.0f}'.format(market_value),
        'net_cash_available': '{:,.0f}'.format(net_cash_available), 
        'total_profit': '{:,.0f}'.format(total_profit),
        'account':account,
        'pk': pk ,
        'order_list':order_list,
        'close_deal':str_close_deal,
        'total_profit_close':'{:,.0f}'.format(total_profit_close),
        'total_profit_open':'{:,.0f}'.format(total_profit_open)


        }    
    return HttpResponse(template.render(context, request))

      



def get_port(request):
    account = Account.objects.get(pk=6)
    total = account.total_profit
    return JsonResponse({'port': total})

from django.urls import reverse



#Dung DRF
# views.py

from rest_framework import viewsets
from .models import Transaction
from .serializers import TransactionSerializer
from django.shortcuts import render
from rest_framework.decorators import action
from rest_framework.response import Response

class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer

    