from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, Dispatcher
import os
from telegram import Update
from django.http import HttpResponse
import requests




# khởi tạo đối tượng Updater và Dispatcher
updater = Updater(token='5881451311:AAEJYKo0ttHU0_Ztv3oGuf-rfFrGgajjtEk', use_context=True)
dispatcher = updater.dispatcher

# định nghĩa hàm xử lý command /start
def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Hello, I'm a bot!")

def port(update, context):
    response = requests.get('http://103.176.251.105/get-port/')
    port = response.json()['port']
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"Port is {port}")

def signal(update, context):
    response = requests.get('http://103.176.251.105/get-signal/')
    signal = response.json()
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"Danh sách là {signal}")

# đăng ký command handler cho command /start
start_handler1 = CommandHandler('start', start)
start_handler2 = CommandHandler('port', port)
dispatcher.add_handler(start_handler1)
dispatcher.add_handler(start_handler2)

# start polling để nhận tin nhắn từ người dùng
updater.start_polling()
