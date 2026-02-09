import os, telebot, threading, http.server, io, requests, urllib.parse
import google.generativeai as genai
from PIL import Image

# 1. СЕРВЕР-ОБМАНКА (Чтобы Render не отключал бота)
def run_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    http.server.HTTPServer(('', port), http.server.SimpleHTTPRequestHandler).serve_forever()
threading.Thread(target=run_dummy_server, daemon=True).start()

# 2. НАСТРОЙКИ
bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))
genai.configure(api_key=os.getenv("GEMINI_KEY"))

# Временная память бота для хранения фото-референсов
user_data = {} # {chat_id: {'photo_bytes': b'...'}}

# 3. ФУНКЦИЯ ГЕНЕРАЦИИ АРТА (Pollinations)
def generate_art(prompt):
    # Кодируем промт для URL
    clean_prompt = urllib.parse.quote(prompt)
    # Используем модель flux для высокого качества и nologo для чистоты
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
    bot.reply_to(message, "🍌 Nano Banana на связи! Пришли мне фото (референс), а затем напиши, какой арт создать.")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    chat_id = message.chat.id
    # Скачиваем фото в лучшем качестве
    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    
    user_data[chat_id] = {'photo_bytes': downloaded_file}
    bot.reply_to(message, "📸 Фото получил! Теперь напиши промт (например: 'в стиле киберпанка' или 'в вечернем платье в Париже'). Я сохраню твое лицо, но изменю окружение.")

@bot.message_handler(func=lambda m: m.chat.id in user_data)
def handle_prompt(message):
    chat_id = message.chat.id
    prompt_text = message.text
    photo_bytes = user_data[chat_id]['photo_bytes']
    
    bot.send_message(chat_id, "⚙️ Магия Nano Banana началась... Анализирую внешность и создаю арт.")
    bot.send_chat_action(chat_id, 'upload_photo')

    try:
        # Gemini анализирует ДНК внешности
        model = genai.GenerativeModel('gemini-1.5-flash')
        img = Image.open(io.BytesIO(photo_bytes))
        
        # Строгая инструкция по сохранению внешности и смене декораций
        instruction = f"""
        Analyze this person's facial features (eyes, nose, face shape), hair color/texture, gender, and age.
        Create a detailed artistic prompt for an AI image generator based on this analysis.
        
        CRITICAL RULES:
        1. KEEP the person's face and identity exactly as in the photo.
        2. IGNORE the current clothes, background, and lighting from the photo.
        3. APPLY new theme: "{prompt_text}".
        4. Describe the person in the new outfit and setting specified in the theme.
        5. Output ONLY the English prompt for the generator.
        """
        
        response = model.generate_content([instruction, img])
        final_prompt = response.text
        
        # Генерируем финальный арт через Pollinations
        art = generate_art(final_prompt)
        
        if art:
            bot.send_photo(chat_id, art, caption=f"Nano Banana: {prompt_text} ✨")
        else:
            bot.reply_to(message, "❌ Ошибка генерации. Попробуй еще раз.")
            
    except Exception as e:
        bot.reply_to(message, f"Ошибка магии: {e}")
    finally:
        # Очищаем память, чтобы можно было начать заново
        if chat_id in user_data:
            del user_data[chat_id]

@bot.message_handler(func=lambda m: True)
def chat(message):
    # Просто текстовое общение, если фото не прислано
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        res = model.generate_content(message.text)
        bot.reply_to(message, res.text)
    except:
        bot.reply_to(message, "Я готов к работе. Пришли фото!")

if __name__ == "__main__":
    print("🎉 БОТ ЗАПУЩЕН!")
    bot.infinity_polling(timeout=90, long_polling_timeout=30)
