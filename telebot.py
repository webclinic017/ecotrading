import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ecotrading.settings")
import django
django.setup()
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import logging
from django.apps import apps
from stocklist.logic import *
import re


# Thiết lập logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Lấy danh sách các room có điều kiện
external_room = ChatGroupTelegram.objects.filter(type='external', is_signal=True, rank='1')
def contains_ticker(text):
    # Sử dụng biểu thức chính quy để kiểm tra xem tin nhắn có chứa các từ 'thông tin', 'báo cáo', 'phân tích'
    # và sau đó là một mã cổ phiếu có đúng 3 kí tự viết liền nhau hay không.
    pattern = r'@([A-Z]{3})'
    match = re.search(pattern, text)
    if match:
        ticker =  match.group(1).upper()  # Trả về mã cổ phiếu nếu có, hoặc None nếu không.
        return ticker.upper()
    return None

def start(update, context):
    update.message.reply_text('Xin chào! Gửi mã cổ phiếu theo cú pháp @XYZ để nhận thông tin tương ứng.')

def reply_to_message(update, context):
    ticker = update.message.text
    ticker = contains_ticker(ticker)
    FundamentalAnalysisModel = apps.get_model('stocklist', 'FundamentalAnalysis')
    try:
        if ticker:
            analysis = FundamentalAnalysisModel.objects.filter(ticker__ticker=ticker).order_by('-modified_date').first()
            if analysis:
                response = f'Thông tin cổ phiếu {ticker}:\n'
                response += f'Ngày báo cáo {analysis.date}. P/E: {analysis.ticker.p_e}, P/B: {analysis.ticker.p_b}, Định giá {analysis.valuation}:\n'
                response += f'{analysis.info}.\n'
                response += f'Nguồn {analysis.source}'
            else:
                response = f'Không tìm thấy thông tin cho mã cổ phiếu {ticker}.'
    except FundamentalAnalysisModel.DoesNotExist:
        pass
        # response = f'Không tìm thấy thông tin cho mã cổ phiếu {ticker}.'

    update.message.reply_text(response)



for group in external_room:
    try:
        # Khởi tạo đối tượng Updater cho từng bot
        updater = Updater(token=group.token.token, use_context=True)
        dispatcher = updater.dispatcher

        # Đăng ký handler cho lệnh /start và tin nhắn văn bản
        start_handler = CommandHandler('start', start)
        dispatcher.add_handler(start_handler)
        reply_handler = MessageHandler(Filters.text & ~Filters.command, reply_to_message)
        dispatcher.add_handler(reply_handler)

        # Khởi chạy bot
        updater.start_polling()

    except Exception as e:
        print(f"Error initializing bot for group {group.chat_id}: {e}")

# Dừng chương trình khi nhấn Ctrl-C
updater.idle()
