import os, telebot, threading, http.server, requests, urllib.parse
from google import genai
from google.genai import types

# 1. СЕРВЕР-ЗАГЛУШКА ДЛЯ RENDER
class SimpleHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Nano Banana is Alive")

def run_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    http.server.HTTPServer(('', port), SimpleHandler).serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

# 2. НАСТРОЙКИ БОТА
bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))
client = genai.Client(api_key=os.getenv("GEMINI_KEY"))
user_data = {}

@bot.message_handler(commands=['start'])
def start(message):
    print(f"✅ Команда /start от {message.chat.id}")
    bot.reply_to(message, "🍌 Nano Banana 1.5 + Pollinations на связи!\n\nПришли мне фото, а потом напиши стиль.")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    print(f"📸 Получено фото от {message.chat.id}")
    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    user_data[message.chat.id] = {'photo': downloaded_file}
    bot.reply_to(message, "📸 Вижу тебя! Теперь напиши, в каком стиле сделать арт? (Например: киберпанк, викинг, аниме)")

@bot.message_handler(func=lambda m: m.chat.id in user_data)
def handle_prompt(message):
    chat_id = message.chat.id
    user_prompt = message.text
    photo_bytes = user_data[chat_id]['photo']
    
    bot.send_message(chat_id, "🧠 Gemini анализирует черты лица...")
    print(f"📝 Промт от {chat_id}: {user_prompt}")

    try:
        # Используем Gemini 1.5 Flash для анализа фото (у неё огромные лимиты)
        response = client.models.generate_content(
            model="gemini-1.5-flash", 
            contents=[
                types.Part.from_bytes(data=photo_bytes, mime_type="image/jpeg"),
                types.Part.from_text(text="Describe this person's face and hair briefly to recreate them in an AI art. Focus on key features.")
            ]
        )
        
        description = response.text
        print(f"✅ Описание готово: {description[:50]}...")

        bot.send_message(chat_id, "🎨 Pollinations рисует арт...")
        
        # Генерируем ссылку для Pollinations
        full_prompt = f"Professional AI portrait, {user_prompt}, based on this appearance: {description}. High quality, detailed face, cinematic lighting."
        encoded_prompt = urllib.parse.quote(full_prompt)
        # Добавляем seed, чтобы картинки всегда были разными
        image_url = f"https://pollinations.ai/p/{encoded_prompt}?width=1024&height=1024&nologo=true&seed={os.urandom(4).hex()}"
        
        bot.send_photo(chat_id, image_url, caption=f"✨ Твой арт готов!\nСтиль: {user_prompt}")
        print(f"✨ Успешная отправка арта для {chat_id}")

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        bot.reply_to(message, f"Ошибка: {e}")
    finally:
        if chat_id in user_data: 
            del user_data[chat_id]

# 3. ЗАПУСК
print("🚀 Бот запущен и слушает Telegram...")
bot.infinity_polling(timeout=90, long_polling_timeout=30)
