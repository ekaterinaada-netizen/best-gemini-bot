import os, telebot, threading, http.server, base64
from google import genai
from google.genai import types

# 1. СЕРВЕР-ЗАГЛУШКА ДЛЯ RENDER
def run_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    http.server.HTTPServer(('', port), http.server.SimpleHTTPRequestHandler).serve_forever()
threading.Thread(target=run_dummy_server, daemon=True).start()

# 2. НАСТРОЙКИ БОТА
bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))
client = genai.Client(api_key=os.getenv("GEMINI_KEY"))
user_data = {}

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "🍌 Nano Banana активирована! Пришли фото, и я превращу его в арт.")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    user_data[message.chat.id] = downloaded_file
    bot.reply_to(message, "📸 Фото вижу! Теперь напиши желаемый стиль (например: киберпанк, масло, аниме).")

@bot.message_handler(func=lambda m: m.chat.id in user_data)
def handle_style(message):
    chat_id = message.chat.id
    style_prompt = message.text
    photo_bytes = user_data[chat_id]
    
    bot.send_message(chat_id, "🎨 Начинаю генерацию по структуре AI Studio...")

    try:
        # Прямое копирование структуры со скриншота: role="user" + parts
        response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=[
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_bytes(data=photo_bytes, mime_type="image/jpeg"),
                        types.Part.from_text(text=f"Transform this person into {style_prompt} style. Keep the face recognizable.")
                    ]
                )
            ]
        )
        
        # Проверяем наличие сгенерированных изображений (как в Nano Banana)
        if response.generated_images:
            for img in response.generated_images:
                bot.send_photo(chat_id, img.image_bytes, caption=f"✨ Твой арт в стиле: {style_prompt}")
        else:
            bot.reply_to(message, "Модель не вернула изображение. Попробуй другой стиль.")

    except Exception as e:
        print(f"❌ Ошибка API: {e}")
        bot.reply_to(message, f"Ошибка API: {e}")
    finally:
        if chat_id in user_data:
            del user_data[chat_id]

# 3. ЗАПУСК
print("🚀 Бот запущен...")
bot.infinity_polling()
