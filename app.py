import json
import os
from datetime import datetime
import telegram
import requests
from flask import Flask, render_template, request
from telegram import Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from selenium import webdriver
from selenium.webdriver.common.by import By
import time

app = Flask(__name__)

# 2Captcha API Key
API_KEY = '3b939b4b7093b70ef59defb145ebd27f'

# Telegram Bot Token
TOKEN = '7784427346:AAGsIu8re1MWZMGaI1QPo51WLpsoxAhbm4'
chat_id = '5316684496'  # Enter your chat ID here for notifications

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
async def start(update, context):
    await update.message.reply_text("Welcome! Please enter your details to proceed with the booking.")

# Main function for Telegram bot
def main():
    application = Application.builder().token(TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_appointment))

    # Start the bot
    application.run_polling()

# Ensure the Flask app and the Telegram bot work together and the app runs on the correct host and port for Railway deployment
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))  # Listen on all IPs and the correct port

# Separate logic to book the appointment
def solve_captcha_and_book_appointment():
    """Solve CAPTCHA and book appointment using Selenium"""
    driver = webdriver.Chrome()
    driver.get("https://servicos.dpf.gov.br/agenda-web/acessar")
    
    try:
        # Fill out the form
        service_dropdown = driver.find_element(By.NAME, "service")
        service_dropdown.send_keys("Segurança Privada")  # Service type (adjust if needed)

        code_input = driver.find_element(By.NAME, "code")
        code_input.send_keys("12345")  # Request code (replace with actual)

        birthdate_input = driver.find_element(By.NAME, "birthdate")
        birthdate_input.send_keys("01/01/1990")  # Date of birth (replace with actual)

        captcha_image_url = driver.find_element(By.CSS_SELECTOR, "img[src*='captcha']").get_attribute("src")
        captcha_solution = solve_captcha(captcha_image_url)

        if captcha_solution is None:
            send_telegram_message("Failed to solve CAPTCHA. Please try again.")
            driver.quit()
            return

        captcha_input = driver.find_element(By.NAME, "captcha_response")
        captcha_input.send_keys(captcha_solution)

        submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit_button.click()

        time.sleep(5)  # Wait for the form to submit

        send_telegram_message("Appointment booked successfully!")
        driver.quit()

    except Exception as e:
        send_telegram_message(f"An error occurred while attempting to book the appointment: {str(e)}")
        driver.quit()