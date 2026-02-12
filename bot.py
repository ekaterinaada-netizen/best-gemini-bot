import os, telebot, threading, http.server, urllib.parse
from google import genai
from google.genai import types

# 1. СЕРВЕР ДЛЯ RENDER
def run_server():
    port = int(os.environ.get("PORT", 10000))
    http.server.HTTPServer(('', port), http.server.SimpleHTTPRequestHandler).serve_forever()
threading.Thread(target=run_server, daemon=True).start()

# 2. НАСТРОЙКИ
bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))

# Убираем http_options, пусть библиотека сама решит вопрос с версией
client = genai.Client(api_key=os.getenv("GEMINI_KEY"))

user_data = {}

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "🍌 Nano Banana готова к финальному тесту! Жду фото.")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    file_info = bot.get_file(message.photo[-1].file_id)
    user_data[message.chat.id] = bot.download_file(file_info.file_path)
    bot.reply_to(message, "📸 Фото здесь. Теперь пришли свой длинный промт!")

@bot.message_handler(func=lambda m: m.chat.id in user_data)
def handle_style(message):
    chat_id = message.chat.id
    style_text = message.text
    photo_bytes = user_data[chat_id]
    
    bot.send_message(chat_id, "🧠 Пытаюсь достучаться до Gemini 1.5 Flash...")

    try:
        # ИСПОЛЬЗУЕМ gemini-1.5-flash-latest — это самый верный вариант
        response = client.models.generate_content(
            model="gemini-1.5-flash-latest", 
            contents=[
                types.Part.from_bytes(data=photo_bytes, mime_type="image/jpeg"),
                types.Part.from_text(text="Describe this person's appearance briefly for an AI portrait.")
            ]
        )
        
        appearance = response.text
        bot.send_message(chat_id, "🎨 Gemini ответила! Pollinations рисует...")

        full_prompt = f"Professional portrait, {style_text}, {appearance}, high quality, 8k"
        encoded_prompt = urllib.parse.quote(full_prompt)
        image_url = f"https://pollinations.ai/p/{encoded_prompt}?width=1024&height=1024&seed={os.urandom(4).hex()}"
        
        bot.send_photo(chat_id, image_url, caption="✨ Твой шедевр готов!")

    except Exception as e:
        # Если снова 404, выведем подробную подсказку
        bot.reply_to(message, f"❌ Ошибка вызова: {e}\n\nПопробуй еще раз через минуту.")
    finally:
        if chat_id in user_data:
            del user_data[chat_id]

bot.infinity_polling()
