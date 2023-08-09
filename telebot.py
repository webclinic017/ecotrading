import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ecotrading.settings")
import django
django.setup()
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import logging
from django.apps import apps
from stocklist.models import FundamentalAnalysis

# khởi tạo đối tượng Updater
updater = Updater(token='5881451311:AAEJYKo0ttHU0_Ztv3oGuf-rfFrGgajjtEk', use_context=True)
dispatcher = updater.dispatcher

# Thiết lập logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Xử lý khi nhận lệnh /start
def start(update, context):
    update.message.reply_text('Xin chào! Gửi mã cổ phiếu để nhận thông tin tương ứng.')

# Xử lý khi nhận tin nhắn văn bản
def reply_to_message(update, context):
    ticker = update.message.text
    FundamentalAnalysisModel = apps.get_model('stocklist', 'FundamentalAnalysis')
    try:
        analysis = FundamentalAnalysisModel.objects.filter(ticker__ticker=ticker).order_by('-modified_date').first()
        if analysis:
            response = f'Thông tin cổ phiếu {ticker}:\n'
            response += f'{analysis.info}. Định giá {analysis.valuation} (Nguồn {analysis.source})\n'
        else:
            response = f'Không tìm thấy thông tin cho mã cổ phiếu {ticker}.'
    except FundamentalAnalysisModel.DoesNotExist:
        response = f'Không tìm thấy thông tin cho mã cổ phiếu {ticker}.'

    update.message.reply_text(response)

# Đăng ký handler cho lệnh /start
start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)

# Đăng ký handler cho tin nhắn văn bản
reply_handler = MessageHandler(Filters.text & ~Filters.command, reply_to_message)
dispatcher.add_handler(reply_handler)

# Khởi chạy bot
updater.start_polling()

# Dừng bot khi nhấn Ctrl-C
updater.idle()
