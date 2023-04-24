from rest_framework.serializers import ModelSerializer, SerializerMethodField
from portfolio.models import *


class TransactionSerializer(ModelSerializer):
    # portfolio = SerializerMethodField()

    class Meta:
        model = Transaction
        fields = ('id','account','stock','position','price','qty', 'cut_loss_price', 'take_profit_price')

    # def get_portfolio(self, obj):
    #     end_date = datetime.now()
    #     start_date = end_date - timedelta(days = 10*365)
    #     return qty_stock_on_account(obj.pk, start_date, end_date)[0]
        
