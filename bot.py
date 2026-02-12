import os, telebot, threading, http.server, urllib.parse
from google import genai
from google.genai import types

# 1. СЕРВЕР ДЛЯ RENDER (чтобы статус был Live)
def run_server():
    port = int(os.environ.get("PORT", 10000))
    server_address = ('', port)
    httpd = http.server.HTTPServer(server_address, http.server.SimpleHTTPRequestHandler)
    httpd.serve_forever()

threading.Thread(target=run_server, daemon=True).start()

# 2. НАСТРОЙКИ И ИНИЦИАЛИЗАЦИЯ
bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))
client = genai.Client(api_key=os.getenv("GEMINI_KEY"))
user_data = {}

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "🍌 Nano Banana 1.5 на связи! Пришли фото, и я превращу его в арт по твоему описанию.")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    # Качаем фото в память
    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    user_data[message.chat.id] = downloaded_file
    bot.reply_to(message, "📸 Вижу! Теперь отправь описание стиля или промт (как ты сделала только что).")

@bot.message_handler(func=lambda m: m.chat.id in user_data)
def handle_style(message):
    chat_id = message.chat.id
    style_description = message.text
    photo_bytes = user_data[chat_id]
    
    bot.send_message(chat_id, "🧠 Gemini анализирует черты лица для сохранения сходства...")

    try:
        # ИСПРАВЛЕНО: Убрано 'models/' из названия, чтобы избежать ошибки 404
        response = client.models.generate_content(
            model="gemini-1.5-flash", 
            contents=[
                types.Part.from_bytes(data=photo_bytes, mime_type="image/jpeg"),
                types.Part.from_text(text="Describe this person's face and appearance very briefly to keep resemblance in a new AI portrait.")
            ]
        )
        
        appearance_desc = response.text
        bot.send_message(chat_id, "🎨 Pollinations начинает отрисовку шедевра...")

        # Формируем финальный промт для генератора картинок
        # Соединяем твое шикарное описание и анализ внешности от Gemini
        full_prompt = f"Professional digital art, {style_description}, {appearance_desc}, high quality, detailed face"
        encoded_prompt = urllib.parse.quote(full_prompt)
        
        # Ссылка на генератор (добавляем случайный seed для уникальности)
        image_url = f"https://pollinations.ai/p/{encoded_prompt}?width=1024&height=1024&seed={os.urandom(4).hex()}"
        
        bot.send_photo(chat_id, image_url, caption="✨ Твой персональный арт готов!")

    except Exception as e:
        bot.reply_to(message, f"❌ Произошла ошибка: {e}")
    finally:
        # Очищаем данные пользователя, чтобы можно было начать заново
        if chat_id in user_data:
            del user_data[chat_id]

# 3. ЗАПУСК БОТА
print("🚀 Бот успешно запущен и готов к работе!")
bot.infinity_polling()
