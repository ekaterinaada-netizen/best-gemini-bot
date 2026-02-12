import os, telebot, threading, http.server, time
from google import genai
from google.genai import types

# Сервер для Render
def run_server():
    port = int(os.environ.get("PORT", 10000))
    http.server.HTTPServer(('', port), http.server.SimpleHTTPRequestHandler).serve_forever()
threading.Thread(target=run_server, daemon=True).start()

# Инициализация
token = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(token)
client = genai.Client(api_key=os.getenv("GEMINI_KEY"))

# УБИВАЕМ КОНФЛИКТЫ ПРИ СТАРТЕ
bot.remove_webhook()
time.sleep(1) # Даем Telegram время на сброс

user_data = {}

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "🍌 Nano Banana 2.5 (AI Studio Style) готова! Пришли фото.")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    file_info = bot.get_file(message.photo[-1].file_id)
    user_data[message.chat.id] = bot.download_file(file_info.file_path)
    bot.reply_to(message, "📸 Фото в памяти! Напиши стиль арт-обработки.")

@bot.message_handler(func=lambda m: m.chat.id in user_data)
def handle_style(message):
    chat_id = message.chat.id
    photo_bytes = user_data[chat_id]
    
    try:
        # Структура ТОЧЬ-В-ТОЧЬ как на твоем скриншоте из Get Code
        response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=[
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_bytes(data=photo_bytes, mime_type="image/jpeg"),
                        types.Part.from_text(text=f"Transformation: {message.text}")
                    ]
                )
            ]
        )
        
        if response.generated_images:
            for img in response.generated_images:
                bot.send_photo(chat_id, img.image_bytes)
        else:
            bot.send_message(chat_id, "Gemini вернула текст вместо фото. Попробуй другой промт.")
            
    except Exception as e:
        bot.send_message(chat_id, f"❌ Ошибка API: {e}")
    finally:
        del user_data[chat_id]

print("🚀 Запуск без конфликтов...")
bot.infinity_polling(timeout=90, long_polling_timeout=5)
