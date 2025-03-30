from flask import Flask, request
import json
import requests
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters
import os

app = Flask(__name__)

# Telegram Bot Token
TOKEN = '7916508457:AAG286xWn621PwrnisliRg80Te3llx_t5xU'
chat_id = '5316684496'  # Enter your chat ID here for notifications
bot = Bot(token=TOKEN)

# Set webhook for Telegram Bot
@app.route('/<bot_token>', methods=['POST'])
def webhook(bot_token):
    if bot_token != TOKEN:
        return "Unauthorized", 403
    data = request.get_json()
    update = Update.de_json(data, bot)
    dispatcher.process_update(update)
    return 'ok', 200

# Function to handle start command
def start(update, context):
    update.message.reply_text("Welcome! Please enter your details to proceed with the booking.")

# Function to handle message from users
def handle_message(update, context):
    user_chat_id = update.message.chat_id
    text = update.message.text
    update.message.reply_text(f'You sent: {text}')

# Setup Telegram dispatcher
dispatcher = Dispatcher(bot, None)
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

# To check if webhook is working
@app.route('/')
def index():
    return "Bot is running!"

if __name__ == '__main__':
    # Set webhook URL in Telegram
    webhook_url = f'https://api.telegram.org/bot{TOKEN}/setWebhook?url=https://federal-production-f9e2.up.railway.app/{TOKEN}'
    requests.get(webhook_url)

    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))  # Listen on all IPs and the correct port