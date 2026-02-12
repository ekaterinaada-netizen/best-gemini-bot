import os, telebot, threading, http.server, urllib.parse, time
import google.generativeai as genai

# 1. СЕРВЕР ДЛЯ RENDER
def run_server():
    port = int(os.environ.get("PORT", 10000))
    http.server.HTTPServer(('', port), http.server.SimpleHTTPRequestHandler).serve_forever()
threading.Thread(target=run_server, daemon=True).start()

# 2. НАСТРОЙКИ
bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))
genai.configure(api_key=os.getenv("GEMINI_KEY"))

# Выбираем стабильную модель напрямую
model = genai.GenerativeModel('gemini-1.5-flash')

bot.remove_webhook()
time.sleep(1)

user_data = {}

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "🍌 Nano Banana 1.5 (Classic Mode) готова! Пришли фото.")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    file_info = bot.get_file(message.photo[-1].file_id)
    user_data[message.chat.id] = bot.download_file(file_info.file_path)
    bot.reply_to(message, "📸 Фото получил. Теперь твой шикарный промт!")

@bot.message_handler(func=lambda m: m.chat.id in user_data)
def handle_style(message):
    chat_id = message.chat.id
    photo_bytes = user_data[chat_id]
    
    bot.send_message(chat_id, "🧠 Gemini анализирует лицо через Classic API...")

    try:
        # Прямая передача данных в классическом стиле
        response = model.generate_content([
            "Describe the person's face briefly for AI image generation.",
            {"mime_type": "image/jpeg", "data": photo_bytes}
        ])
        
        appearance = response.text
        bot.send_message(chat_id, "🎨 Gemini ответила! Pollinations рисует...")

        full_prompt = f"Professional digital portrait, {message.text}, {appearance}, high quality, 8k, cinematic lighting"
        encoded_prompt = urllib.parse.quote(full_prompt)
        image_url = f"https://pollinations.ai/p/{encoded_prompt}?width=1024&height=1024&seed={os.urandom(4).hex()}"
        
        bot.send_photo(chat_id, image_url, caption="✨ Твой шедевр готов!")

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка Classic API: {e}")
    finally:
        if chat_id in user_data:
            del user_data[chat_id]

bot.infinity_polling()
