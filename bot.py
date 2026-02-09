import os
import telebot
import google.generativeai as genai
from PIL import Image, ImageDraw, ImageFont
import io
from datetime import datetime
import textwrap
import http.server
import threading

# 1. СЕРВЕР-ОБМАНКА ДЛЯ RENDER (чтобы не было Timed Out)
def run_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    server_address = ('', port)
    try:
        httpd = http.server.HTTPServer(server_address, http.server.SimpleHTTPRequestHandler)
        print(f"--- Обманка запущена на порту {port} ---")
        httpd.serve_forever()
    except Exception as e:
        print(f"Ошибка сервера-обманки: {e}")

# Запуск обманки в отдельном потоке
threading.Thread(target=run_dummy_server, daemon=True).start()

# 2. НАСТРОЙКИ БОТА И GEMINI
TOKEN = os.getenv("BOT_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_KEY")

bot = telebot.TeleBot(TOKEN)
genai.configure(api_key=GEMINI_KEY)

# Список моделей для перебора (от новых к стабильным)
MODELS_TO_TRY = [
    'gemini-1.5-flash',
    'gemini-1.5-flash-latest',
    'gemini-1.5-pro',
    'gemini-pro'
]

def generate_with_fallback(prompt):
    """Пробует разные модели, если одна выдает 404"""
    for model_name in MODELS_TO_TRY:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            if "404" in str(e):
                print(f"Модель {model_name} не найдена, пробуем следующую...")
                continue
            return f"Ошибка: {e}"
    return "Ни одна модель Gemini не ответила. Проверьте API ключ."

# 3. ОБРАБОТЧИКИ КОМАНД
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "✨ Бот запущен и готов к работе! Пиши свой вопрос или используй /image для магии.")

@bot.message_handler(commands=['image'])
def image_command(message):
    # Заготовка под Nano Banana
    bot.reply_to(message, "🎨 Команда для красивых генераций принята! Скоро я научусь рисовать карточки.")

@bot.message_handler(func=lambda m: True)
def chat(message):
    # Используем всеядную функцию
    answer = generate_with_fallback(message.text)
    bot.reply_to(message, answer)

# 4. ЗАПУСК
if __name__ == "__main__":
    print("🎉 БОТ ЗАПУЩЕН!")
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=30)
    except Exception as e:
        print(f"Ошибка поллинга: {e}")
