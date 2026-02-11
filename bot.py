import os, telebot, threading, http.server, io
from google import genai
from google.genai import types

# 1. СЕРВЕР-ОБМАНКА
def run_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    http.server.HTTPServer(('', port), http.server.SimpleHTTPRequestHandler).serve_forever()
threading.Thread(target=run_dummy_server, daemon=True).start()

# 2. НАСТРОЙКИ (Новый клиент Google GenAI)
bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))
client = genai.Client(api_key=os.getenv("GEMINI_KEY"))

user_data = {}

# 3. ОБРАБОТЧИКИ
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "🍌 Nano Banana 2.5 на связи! Пришли фото, а затем промт.")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    user_data[message.chat.id] = {'photo': downloaded_file}
    bot.reply_to(message, "📸 Фото в системе! Напиши промт для генерации.")

@bot.message_handler(func=lambda m: m.chat.id in user_data)
def handle_prompt(message):
    chat_id = message.chat.id
    prompt_text = message.text
    photo_bytes = user_data[chat_id]['photo']
    
    bot.send_message(chat_id, "🎨 Генерирую изображение через Nano Banana 2.5...")
    bot.send_chat_action(chat_id, 'upload_photo')

    try:
        # Настраиваем запрос как в твоем коде из AI Studio
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_bytes(data=photo_bytes, mime_type="image/jpeg"),
                    types.Part.from_text(text=f"Create a new image based on this person. Theme: {prompt_text}. Maintain facial identity."),
                ],
            ),
        ]
        
        config = types.GenerateContentConfig(
            response_modalities=["IMAGE"], # Просим только картинку
        )

        # Получаем результат
        response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=contents,
            config=config,
        )

        # Ищем картинку в частях ответа
        image_found = False
        for part in response.candidates[0].content.parts:
            if part.inline_data:
                bot.send_photo(chat_id, part.inline_data.data, caption=f"Готово! ✨\nПромт: {prompt_text}")
                image_found = True
                break
        
        if not image_found:
            bot.reply_to(message, "Бот выдал текст вместо картинки. Попробуй изменить промт.")

    except Exception as e:
        bot.reply_to(message, f"Ошибка Nano Banana: {e}")
    finally:
        if chat_id in user_data: del user_data[chat_id]

bot.infinity_polling()
