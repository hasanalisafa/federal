from flask import Flask, render_template, request
import json
from datetime import datetime
import telegram
import requests
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from telegram import Bot
from telegram.ext import CommandHandler, MessageHandler, Filters, Updater
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# 2Captcha API Key from environment variables
API_KEY = os.getenv('CAPTCHA_API_KEY')

# Telegram Bot Token from environment variables
TOKEN = os.getenv('TELEGRAM_TOKEN')
chat_id = os.getenv('TELEGRAM_CHAT_ID')

# Initialize the bot
bot = Bot(token=TOKEN)

# Function to handle CAPTCHA solving
def solve_captcha(captcha_image_url):
    url = 'http://2captcha.com/in.php'
    data = {
        'key': API_KEY,
        'method': 'post',
        'body': captcha_image_url,
        'json': 1,
    }
    response = requests.post(url, data=data)
    result = response.json()
    if result['status'] == 1:
        captcha_id = result['request']
        solution_url = f"http://2captcha.com/res.php?key={API_KEY}&action=get&id={captcha_id}&json=1"
        solution_response = requests.get(solution_url)
        solution_result = solution_response.json()
        if solution_result['status'] == 1:
            return solution_result['request']
        else:
            return None
    return None

# Function to send messages via Telegram
def send_telegram_message(chat_id, message):
    bot.send_message(chat_id=chat_id, text=message)

# Function to handle user details and book an appointment
def handle_appointment(update, context):
    user_chat_id = update.message.chat_id
    user_name = update.message.from_user.first_name

    # Collect details from user
    send_telegram_message(user_chat_id, "Please enter the service type (e.g., Segurança Privada):")
    service = update.message.text

    send_telegram_message(user_chat_id, "Please enter the request number:")
    code = update.message.text

    send_telegram_message(user_chat_id, "Please enter your date of birth (dd/mm/yyyy):")
    birthdate = update.message.text

    send_telegram_message(user_chat_id, "Please enter the private invitation code:")
    invite = update.message.text

    # Validation
    if invite != "1924":
        send_telegram_message(user_chat_id, "Invalid invite code. Please try again.")
        return

    # Save data to users.json
    try:
        with open('users.json', 'r', encoding='utf-8') as f:
            users = json.load(f)
    except:
        users = []

    user = next((u for u in users if u['chat_id'] == user_chat_id), None)
    if not user:
        user = {"chat_id": user_chat_id, "name": user_name, "requests": []}
        users.append(user)

    user['requests'].append({
        "codigo": code,
        "birthdate": birthdate,
        "service": service,
        "auto_book": True,
        "registered_at": datetime.now().strftime("%Y-%m-%d %H:%M")
    })

    with open('users.json', 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

    send_telegram_message(user_chat_id, "Booking process initiated! Processing details...")

    # Call the function to process the appointment (CAPTCHA, etc.)
    solve_captcha_and_book_appointment()

    send_telegram_message(user_chat_id, "Your appointment has been successfully booked!")

# Function to start the bot
def start(update, context):
    send_telegram_message(update.message.chat_id, "Welcome! Please enter your details to proceed with the booking.")

# Main function for Telegram bot
def main():
    updater = Updater(TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    # Add handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_appointment))

    # Start the bot
    updater.start_polling()
    updater.idle()

# Starting the Flask app
app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        # Handle POST request logic here (you can call your appointment function or actions)
        pass
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)