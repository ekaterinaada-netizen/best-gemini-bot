import os, telebot, threading, http.server, urllib.parse, time
from google import genai
from google.genai import types

# 1. СЕРВЕР ДЛЯ RENDER
def run_server():
    port = int(os.environ.get("PORT", 10000))
    print(f"Попытка запустить сервер на порту {port}...")
    http.server.HTTPServer(('', port), http.server.SimpleHTTPRequestHandler).serve_forever()

threading.Thread(target=run_server, daemon=True).start()

# 2. ИНИЦИАЛИЗАЦИЯ
print("Запуск инициализации бота...")
token = os.getenv("BOT_TOKEN")
api_key = os.getenv("GEMINI_KEY")

bot = telebot.TeleBot(token)
client = genai.Client(api_key=api_key)

# Сбрасываем старые зависшие сессии
bot.remove_webhook()
time.sleep(2)
print("Связь с Telegram очищена. Бот готов.")

user_data = {}

@bot.message_handler(commands=['start'])
def start(message):
    print(f"Получена команда /start от {message.chat.id}")
    bot.reply_to(message, "🍌 Nano Banana ожила! Пришли фото, и мы проверим Gemini 1.5.")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    print(f"Получено фото от {message.chat.id}")
    file_info = bot.get_file(message.photo[-1].file_id)
    user_data[message.chat.id] = bot.download_file(file_info.file_path)
    bot.reply_to(message, "📸 Фото в памяти! Теперь пришли стиль (промт).")

@bot.message_handler(func=lambda m: m.chat.id in user_data)
def handle_style(message):
    chat_id = message.chat.id
    style_text = message.text
    print(f"Обработка стиля для {chat_id}: {style_text}")
    
    bot.send_message(chat_id, "🧠 Gemini 1.5 Flash анализирует...")

    try:
        # Пытаемся вызвать модель. Если снова будет 404, мы это увидим в логах
        response = client.models.generate_content(
            model="gemini-1.5-flash", 
            contents=[
                types.Part.from_bytes(data=user_data[chat_id], mime_type="image/jpeg"),
                types.Part.from_text(text="Describe this person's appearance briefly for an AI portrait.")
            ]
        )
        
        appearance = response.text
        print("Gemini успешно ответила.")

        full_prompt = f"Professional portrait, {style_text}, {appearance}, high quality"
        encoded_prompt = urllib.parse.quote(full_prompt)
        image_url = f"https://pollinations.ai/p/{encoded_prompt}?width=1024&height=1024&seed={os.urandom(4).hex()}"
        
        bot.send_photo(chat_id, image_url, caption="✨ Твой арт готов!")
        print("Арт успешно отправлен.")

    except Exception as e:
        print(f"❌ ОШИБКА: {e}")
        bot.reply_to(message, f"❌ Ошибка: {e}")
    finally:
        del user_data[chat_id]

print("🚀 Бот начинает опрос Telegram (Polling)...")
bot.infinity_polling(timeout=90, long_polling_timeout=5)
