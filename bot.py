import os, telebot, threading, http.server, urllib.parse
from google import genai
from google.genai import types

# Сервер-заглушка
def run_server():
    http.server.HTTPServer(('', int(os.environ.get("PORT", 10000))), http.server.SimpleHTTPRequestHandler).serve_forever()
threading.Thread(target=run_server, daemon=True).start()

bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))
client = genai.Client(api_key=os.getenv("GEMINI_KEY"))
user_data = {}

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "🍌 Nano Banana перешла в стабильный режим! Пришли фото.")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_data[message.chat.id] = bot.download_file(bot.get_file(message.photo[-1].file_id).file_path)
    bot.reply_to(message, "📸 Вижу! В каком стиле сделать арт?")

@bot.message_handler(func=lambda m: m.chat.id in user_data)
def handle_style(message):
    chat_id = message.chat.id
    style = message.text
    photo_bytes = user_data[chat_id]
    bot.send_message(chat_id, "🧠 Gemini анализирует черты лица...")

    try:
        # 1. Используем 1.5 Flash для ОПИСАНИЯ (она почти всегда доступна)
        response = client.models.generate_content(
            model="gemini-1.5-flash", 
            contents=[
                types.Part.from_bytes(data=photo_bytes, mime_type="image/jpeg"),
                types.Part.from_text(text="Describe this person's appearance briefly for an AI portrait generator.")
            ]
        )
        description = response.text

        # 2. Рисуем через Pollinations (без лимитов!)
        bot.send_message(chat_id, "🎨 Pollinations создает шедевр...")
        full_prompt = f"Professional digital art, {style}, {description}"
        encoded_prompt = urllib.parse.quote(full_prompt)
        image_url = f"https://pollinations.ai/p/{encoded_prompt}?width=1024&height=1024&seed={os.urandom(4).hex()}"
        
        bot.send_photo(chat_id, image_url, caption=f"✨ Стиль: {style}")

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")
    finally:
        del user_data[chat_id]

bot.infinity_polling()
