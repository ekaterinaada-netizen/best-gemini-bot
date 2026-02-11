import os, telebot, threading, http.server, io
from google import genai
from google.genai import types

# СЕРВЕР-ОБМАНКА (Логируем посещения)
class SimpleHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Nano Banana Server is Running")

def run_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    http.server.HTTPServer(('', port), SimpleHandler).serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

# НАСТРОЙКИ
print("🔄 Запуск инициализации бота...")
bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))
client = genai.Client(api_key=os.getenv("GEMINI_KEY"))
user_data = {}

@bot.message_handler(commands=['start'])
def start(message):
    print(f"✅ Получена команда /start от {message.chat.id}")
    bot.reply_to(message, "🍌 Nano Banana 2.5 на связи! Пришли фото.")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    print(f"📸 Получено фото от {message.chat.id}")
    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    user_data[message.chat.id] = {'photo': downloaded_file}
    bot.reply_to(message, "📸 Фото в системе! Жду промт.")

@bot.message_handler(func=lambda m: m.chat.id in user_data)
def handle_prompt(message):
    chat_id = message.chat.id
    print(f"📝 Получен промт от {chat_id}: {message.text}")
    photo_bytes = user_data[chat_id]['photo']
    bot.send_message(chat_id, "🎨 Начинаю генерацию...")

    try:
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_bytes(data=photo_bytes, mime_type="image/jpeg"),
                    types.Part.from_text(text=f"Create a new image. Theme: {message.text}. Maintain facial identity."),
                ],
            ),
        ]
        
        response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=contents,
            config=types.GenerateContentConfig(response_modalities=["IMAGE"]),
        )

        for part in response.candidates[0].content.parts:
            if part.inline_data:
                bot.send_photo(chat_id, part.inline_data.data)
                print(f"✨ Успешная генерация для {chat_id}")
                break
    except Exception as e:
        print(f"❌ Ошибка генерации: {e}")
        bot.reply_to(message, f"Ошибка: {e}")
    finally:
        if chat_id in user_data: del user_data[chat_id]

print("🚀 Бот вошел в режим прослушивания (Infinity Polling)...")
bot.infinity_polling(timeout=90, long_polling_timeout=30)
