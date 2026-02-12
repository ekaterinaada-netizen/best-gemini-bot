import os, telebot, threading, http.server, urllib.parse, time
from google import genai
from google.genai import types

# 1. СЕРВЕР ДЛЯ RENDER
def run_server():
    port = int(os.environ.get("PORT", 10000))
    http.server.HTTPServer(('', port), http.server.SimpleHTTPRequestHandler).serve_forever()
threading.Thread(target=run_server, daemon=True).start()

# 2. ИНИЦИАЛИЗАЦИЯ
bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))
# Инициализируем клиент БЕЗ дополнительных настроек версии, чтобы он был гибким
client = genai.Client(api_key=os.getenv("GEMINI_KEY"))

# Сброс вебхуков для предотвращения ошибки 409
bot.remove_webhook()
time.sleep(1)

user_data = {}

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "🍌 Nano Banana готова! Я починил путь к модели. Пришли фото!")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    file_info = bot.get_file(message.photo[-1].file_id)
    user_data[message.chat.id] = bot.download_file(file_info.file_path)
    bot.reply_to(message, "📸 Фото получил. Теперь твой шикарный промт!")

@bot.message_handler(func=lambda m: m.chat.id in user_data)
def handle_style(message):
    chat_id = message.chat.id
    photo_bytes = user_data[chat_id]
    
    bot.send_message(chat_id, "🧠 Gemini анализирует внешность...")

    try:
        # ИСПОЛЬЗУЕМ САМОЕ ПРОСТОЕ ИМЯ. Библиотека сама добавит нужные префиксы.
        response = client.models.generate_content(
            model="gemini-1.5-flash", 
            contents=[
                types.Part.from_bytes(data=photo_bytes, mime_type="image/jpeg"),
                types.Part.from_text(text="Describe the person's face briefly to keep resemblance.")
            ]
        )
        
        appearance = response.text
        bot.send_message(chat_id, "🎨 Pollinations создает твой шедевр...")

        # Собираем промт из твоего текста и анализа Gemini
        full_prompt = f"Professional portrait, {message.text}, {appearance}, high quality, 8k"
        encoded_prompt = urllib.parse.quote(full_prompt)
        
        # Генерируем ссылку
        image_url = f"https://pollinations.ai/p/{encoded_prompt}?width=1024&height=1024&seed={os.urandom(4).hex()}"
        
        bot.send_photo(chat_id, image_url, caption="✨ Готово! Как тебе результат?")

    except Exception as e:
        # Если ошибка все еще будет, мы увидим её точный текст
        bot.reply_to(message, f"❌ Увы, опять ошибка API: {e}")
    finally:
        if chat_id in user_data:
            del user_data[chat_id]

bot.infinity_polling()
