import os, telebot, threading, http.server, io, requests, urllib.parse
import google.generativeai as genai
from PIL import Image

# 1. СЕРВЕР-ОБМАНКА
def run_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    http.server.HTTPServer(('', port), http.server.SimpleHTTPRequestHandler).serve_forever()
threading.Thread(target=run_dummy_server, daemon=True).start()

# 2. НАСТРОЙКИ
bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))
genai.configure(api_key=os.getenv("GEMINI_KEY"))

user_data = {}

# 3. ФУНКЦИЯ ГЕНЕРАЦИИ АРТА
def generate_art(prompt):
    clean_prompt = urllib.parse.quote(prompt)
    # Используем модель flux для максимального качества
    url = f"https://pollinations.ai/p/{clean_prompt}?width=1024&height=1024&model=flux&nologo=true"
    try:
        response = requests.get(url, timeout=60)
        if response.status_code == 200:
            return response.content
    except Exception as e:
        print(f"Ошибка Pollinations: {e}")
    return None

# 4. ОБРАБОТЧИКИ
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "🍌 Nano Banana готова! Пришли фото, а потом напиши промт.")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    user_data[message.chat.id] = {'photo_bytes': downloaded_file}
    bot.reply_to(message, "📸 Фото вижу! Теперь напиши промт (например: 'я в стиле киберпанк').")

@bot.message_handler(func=lambda m: m.chat.id in user_data)
def handle_prompt(message):
    chat_id = message.chat.id
    prompt_text = message.text
    photo_bytes = user_data[chat_id]['photo_bytes']
    
    bot.send_message(chat_id, "⚙️ Магия Nano Banana началась...")
    bot.send_chat_action(chat_id, 'upload_photo')

    try:
        # ПЕРЕБОР МОДЕЛЕЙ ДЛЯ ИСПРАВЛЕНИЯ ОШИБКИ 404
        response = None
        # Пробуем разные варианты имен моделей, которые понимает API
        for model_name in ["models/gemini-1.5-flash", "gemini-1.5-flash", "models/gemini-1.5-pro"]:
            try:
                model = genai.GenerativeModel(model_name=model_name)
                img = Image.open(io.BytesIO(photo_bytes))
                
                instruction = f"""
                Analyze this person's facial features, hair, and gender.
                Create a professional artistic prompt for an AI image generator.
                Theme: "{prompt_text}".
                RULES: Keep the face identical. Change clothing and background to match the theme.
                Output only the English prompt.
                """
                
                response = model.generate_content([instruction, img])
                if response: break
            except Exception as inner_e:
                if "404" in str(inner_e): continue
                else: raise inner_e

        if not response:
            bot.reply_to(message, "Google API временно недоступен. Попробуй позже.")
            return

        final_prompt = response.text
        art = generate_art(final_prompt)
        
        if art:
            bot.send_photo(chat_id, art, caption=f"Nano Banana: {prompt_text} ✨")
        else:
            bot.reply_to(message, "❌ Ошибка генерации картинки.")
            
    except Exception as e:
        bot.reply_to(message, f"Ошибка магии: {e}")
    finally:
        if chat_id in user_data: del user_data[chat_id]

@bot.message_handler(func=lambda m: True)
def chat(message):
    try:
        model = genai.GenerativeModel(model_name="models/gemini-1.5-flash")
        res = model.generate_content(message.text)
        bot.reply_to(message, res.text)
    except:
        bot.reply_to(message, "Пришли фото для начала генерации!")

if __name__ == "__main__":
    bot.infinity_polling(timeout=90, long_polling_timeout=30)
