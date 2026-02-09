import os
import telebot
import google.generativeai as genai
import http.server
import threading

# 1. ОБМАНКА ДЛЯ RENDER (начинает работать мгновенно)
def run_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    server_address = ('', port)
    httpd = http.server.HTTPServer(server_address, http.server.SimpleHTTPRequestHandler)
    print(f"--- Обманка запущена на порту {port} ---")
    httpd.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

# 2. НАСТРОЙКИ (берём из Environment Variables)
TOKEN = os.getenv("BOT_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_KEY")

bot = telebot.TeleBot(TOKEN)
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash-latest')

# 3. ЛОГИКА БОТА
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Привет! Я твой ИИ-бот на Render. Спрашивай что угодно!")

@bot.message_handler(func=lambda m: True)
def chat(message):
    try:
        response = model.generate_content(message.text)
        bot.reply_to(message, response.text)
    except Exception as e:
        bot.reply_to(message, f"Ошибка: {e}")

# 4. ЗАПУСК
if __name__ == "__main__":
    print("🎉 БОТ ЗАПУЩЕН!")
    bot.infinity_polling(timeout=60, long_polling_timeout=30)

