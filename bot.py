import os, telebot, threading, http.server, requests, urllib.parse
from google import genai
from google.genai import types

# Сервер-заглушка
def run_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    http.server.HTTPServer(('', port), http.server.SimpleHTTPRequestHandler).serve_forever()
threading.Thread(target=run_dummy_server, daemon=True).start()

bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))
client = genai.Client(api_key=os.getenv("GEMINI_KEY"))
user_data = {}

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "🍌 Nano Banana 1.5 + Pollinations! Пришли фото.")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    user_data[message.chat.id] = {'photo': downloaded_file}
    bot.reply_to(message, "📸 Вижу тебя! Теперь напиши, в каком стиле сделать арт?")

@bot.message_handler(func=lambda m: m.chat.id in user_data)
def handle_prompt(message):
    chat_id = message.chat.id
    user_prompt = message.text
    photo_bytes = user_data[chat_id]['photo']
    
    bot.send_message(chat_id, "🧠 Gemini анализирует фото...")

    try:
        # Используем 1.5 Flash ТОЛЬКО для описания (у неё лимиты больше)
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=[
                types.Part.from_bytes(data=photo_bytes, mime_type="image/jpeg"),
                "Describe this person's face and hair briefly to recreate them in an AI art. Focus on features."
            ]
        )
        description = response.text
        print(f"DEBUG: Description: {description}")

        bot.send_message(chat_id, "🎨 Pollinations рисует твой шедевр...")
        
        # Создаем финальный промт для рисования
        full_prompt = f"Professional AI portrait, {user_prompt}, based on this appearance: {description}. High quality, detailed face."
        encoded_prompt = urllib.parse.quote(full_prompt)
        image_url = f"https://pollinations.ai/p/{encoded_prompt}?width=1024&height=1024&nologo=true&seed={os.urandom(4).hex()}"
        
        bot.send_photo(chat_id, image_url, caption=f"Твой Nano Banana арт готов! ✨")

    except Exception as e:
        bot.reply_to(message, f"Ошибка: {e}")
    finally:
        if chat_id in user_data: del user_data[chat_id]

bot.infinity_polling()
