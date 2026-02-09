import os
import telebot
import google.generativeai as genai
from PIL import Image, ImageDraw, ImageFont
import io
import textwrap
import http.server
import threading

# 1. СЕРВЕР-ОБМАНКА
def run_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    server_address = ('', port)
    httpd = http.server.HTTPServer(server_address, http.server.SimpleHTTPRequestHandler)
    httpd.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

# 2. НАСТРОЙКИ
TOKEN = os.getenv("BOT_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_KEY")

bot = telebot.TeleBot(TOKEN)
genai.configure(api_key=GEMINI_KEY)

# 3. ФУНКЦИЯ РИСОВАНИЯ (NANO BANANA)
def create_banana_card(text):
    # Создаем холст (градиентный фон или просто темный)
    img = Image.new('RGB', (800, 400), color=(20, 20, 20))
    draw = ImageDraw.Draw(img)
    
    # Рисуем рамку
    draw.rectangle([10, 10, 790, 390], outline=(255, 215, 0), width=3)
    
    # Текст (используем стандартный шрифт, так как на Render своих нет)
    lines = textwrap.wrap(text, width=40)
    y_text = 100
    for line in lines[:5]: # Ограничим 5 строками
        draw.text((60, y_text), line, fill=(255, 255, 255))
        y_text += 50
    
    draw.text((600, 350), "Nano Banana ✨", fill=(255, 215, 0))
    
    # Сохраняем в память
    bio = io.BytesIO()
    img.save(bio, 'PNG')
    bio.seek(0)
    return bio

# 4. ОБРАБОТЧИКИ
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Я готов! Пиши текст или используй /image для генерации карточки 🍌")

@bot.message_handler(commands=['image'])
def make_image(message):
    prompt = message.text.replace('/image', '').strip()
    if not prompt:
        bot.reply_to(message, "Напиши что-нибудь после /image")
        return
    
    bot.send_chat_action(message.chat.id, 'upload_photo')
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(f"Опиши кратко и красиво: {prompt}")
        card = create_banana_card(response.text)
        bot.send_photo(message.chat.id, card, caption="Ваша генерация в стиле Nano Banana 🍌")
    except Exception as e:
        bot.reply_to(message, f"Ошибка магии: {e}")

@bot.message_handler(func=lambda m: True)
def chat(message):
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(message.text)
        bot.reply_to(message, response.text)
    except Exception as e:
        bot.reply_to(message, f"Проблема с ключом или моделью: {e}")

if __name__ == "__main__":
    bot.infinity_polling(timeout=60)
